"""test configuration — shared fixtures and helpers for all tests."""

import secrets
from collections.abc import AsyncGenerator
from datetime import datetime

import pytest
import pytest_asyncio
import uuid6
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from testcontainers.postgres import PostgresContainer

from app.main import app
from app.dependencies import get_async_session
from app.models import Base
from app.modules.puzzle.models import Puzzle, FreeplayPuzzleAttempt, DailyPuzzle, DailyPuzzleAttempt
from app.modules.tracking import Device
from app.modules.authentication import User, AccessToken


# --- database ---

@pytest.fixture(scope="session")
def postgres_url():
    """start a PostgreSQL container for the test session."""
    with PostgresContainer("postgres:18") as pg:
        url = pg.get_connection_url()
        async_url = url.replace("psycopg2", "asyncpg")
        yield async_url


@pytest_asyncio.fixture
async def db(postgres_url) -> AsyncGenerator[AsyncSession, None]:
    """fresh database for each test — creates tables, yields session, drops tables."""
    engine = create_async_engine(postgres_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# --- test client ---

@pytest_asyncio.fixture
async def client(postgres_url) -> AsyncGenerator[AsyncClient, None]:
    """async test client with its own fresh database."""
    engine = create_async_engine(postgres_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async def override_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def seeded_client(postgres_url) -> AsyncGenerator[tuple[AsyncClient, AsyncSession], None]:
    """client and db session sharing the same database — use when tests need to seed data."""
    engine = create_async_engine(postgres_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async def override_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_session
    transport = ASGITransport(app=app)

    async with session_maker() as db:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client, db

    app.dependency_overrides.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# --- entity helpers ---

async def create_device(db: AsyncSession) -> Device:
    device = Device(id=uuid6.uuid7(), user_agent="test-agent")
    db.add(device)
    await db.flush()
    return device


async def create_user(db: AsyncSession, username: str, email: str) -> User:
    user = User(
        id=uuid6.uuid7(),
        username=username,
        email=email,
        hashed_password="$argon2id$fake",
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )
    db.add(user)
    await db.flush()
    return user


async def create_puzzle(db: AsyncSession, puzzle_type="sudoku", size="9x9", difficulty="easy") -> Puzzle:
    puzzle = Puzzle(
        id=uuid6.uuid7(),
        complete_id=str(uuid6.uuid7()),
        definition_id=str(uuid6.uuid7()),
        solution_id=str(uuid6.uuid7()),
        puzzle_type=puzzle_type,
        puzzle_size=size,
        puzzle_difficulty=difficulty,
        puzzle_data={"rows": 9, "cols": 9, "initial_state": [], "solution": []},
        is_active=True,
    )
    db.add(puzzle)
    await db.flush()
    return puzzle


async def authenticate(client: AsyncClient, db: AsyncSession, user: User) -> None:
    """create an access token and set the cookie on the client."""
    token = secrets.token_urlsafe(32)
    access_token = AccessToken(token=token, user_id=user.id)
    db.add(access_token)
    await db.flush()
    client.cookies.set("access_token", token)


async def create_attempt(
    db: AsyncSession,
    puzzle: Puzzle,
    device: Device,
    user: User | None,
    start: int,
    finish: int,
    is_solved: bool = True,
    used_tutorial: bool = False,
) -> FreeplayPuzzleAttempt:
    attempt = FreeplayPuzzleAttempt(
        id=uuid6.uuid7(),
        device_id=device.id,
        user_id=user.id if user else None,
        puzzle_id=puzzle.id,
        timestamp_start=start,
        timestamp_finish=finish,
        action_history=[],
        board_state=[],
        is_solved=is_solved,
        used_tutorial=used_tutorial,
    )
    db.add(attempt)
    await db.flush()
    return attempt


async def create_daily_puzzle(db: AsyncSession, puzzle: Puzzle, date: datetime) -> DailyPuzzle:
    daily = DailyPuzzle(
        puzzle_date=date.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None),
        puzzle_id=puzzle.id,
    )
    db.add(daily)
    await db.flush()
    return daily


async def create_daily_attempt(
    db: AsyncSession,
    daily_puzzle: DailyPuzzle,
    device: Device,
    user: User | None,
    start: int,
    finish: int,
    is_solved: bool = True,
) -> DailyPuzzleAttempt:
    attempt = FreeplayPuzzleAttempt(
        id=uuid6.uuid7(),
        device_id=device.id,
        user_id=user.id if user else None,
        puzzle_id=daily_puzzle.puzzle_id,
        timestamp_start=start,
        timestamp_finish=finish,
        action_history=[],
        board_state=[],
        is_solved=is_solved,
    )
    db.add(attempt)
    await db.flush()

    daily_attempt = DailyPuzzleAttempt(
        user_id=user.id if user else None,
        device_id=device.id,
        daily_puzzle_id=daily_puzzle.id,
        attempt_id=attempt.id,
    )
    db.add(daily_attempt)
    await db.flush()
    return daily_attempt
