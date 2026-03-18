"""tests for leaderboard service and endpoints."""

import pytest
import pytest_asyncio
from collections.abc import AsyncGenerator

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

import uuid6

from app.main import app
from app.dependencies import get_async_session
from app.models import Base
from app.modules.puzzle.models import Puzzle, FreeplayPuzzleAttempt
from app.modules.tracking import Device
from app.modules.authentication import User


# --- helpers ---

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


# --- fixture: client + db that share the same database ---

@pytest_asyncio.fixture
async def seeded_client(postgres_url) -> AsyncGenerator[tuple[AsyncClient, AsyncSession], None]:
    """client and db session sharing the same database."""
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


LEADERBOARD_PARAMS = {
    "puzzle_type": "sudoku",
    "puzzle_size": "9x9",
    "puzzle_difficulty": "easy",
}


# --- tests ---

class TestFreeplayLeaderboard:
    @pytest.mark.asyncio
    async def test_empty_leaderboard(self, client):
        """leaderboard returns empty when no attempts exist."""
        response = await client.get("/api/puzzle/freeplay/leaderboard", params=LEADERBOARD_PARAMS)
        assert response.status_code == 200
        data = response.json()
        assert data["leaderboard"] == []
        assert data["count"] == 0

    @pytest.mark.asyncio
    async def test_single_user_leaderboard(self, seeded_client):
        """leaderboard shows a single solved attempt."""
        client, db = seeded_client
        device = await create_device(db)
        user = await create_user(db, "player1", "player1@test.com")
        puzzle = await create_puzzle(db)
        await create_attempt(db, puzzle, device, user, start=1000, finish=11000)
        await db.commit()

        response = await client.get("/api/puzzle/freeplay/leaderboard", params=LEADERBOARD_PARAMS)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["leaderboard"][0]["username"] == "player1"
        assert data["leaderboard"][0]["rank"] == 1

    @pytest.mark.asyncio
    async def test_leaderboard_ordering(self, seeded_client):
        """leaderboard ranks by fastest time."""
        client, db = seeded_client
        device = await create_device(db)
        fast_user = await create_user(db, "speedy", "speedy@test.com")
        slow_user = await create_user(db, "turtle", "turtle@test.com")
        puzzle = await create_puzzle(db)

        await create_attempt(db, puzzle, device, slow_user, start=1000, finish=31000)
        await create_attempt(db, puzzle, device, fast_user, start=1000, finish=11000)
        await db.commit()

        response = await client.get("/api/puzzle/freeplay/leaderboard", params=LEADERBOARD_PARAMS)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert data["leaderboard"][0]["username"] == "speedy"
        assert data["leaderboard"][1]["username"] == "turtle"

    @pytest.mark.asyncio
    async def test_leaderboard_excludes_unsolved(self, seeded_client):
        """unsolved attempts don't appear on leaderboard."""
        client, db = seeded_client
        device = await create_device(db)
        user = await create_user(db, "quitter", "quitter@test.com")
        puzzle = await create_puzzle(db)
        await create_attempt(db, puzzle, device, user, start=1000, finish=11000, is_solved=False)
        await db.commit()

        response = await client.get("/api/puzzle/freeplay/leaderboard", params=LEADERBOARD_PARAMS)
        assert response.status_code == 200
        assert response.json()["count"] == 0

    @pytest.mark.asyncio
    async def test_leaderboard_excludes_tutorial(self, seeded_client):
        """attempts using tutorial don't appear on leaderboard."""
        client, db = seeded_client
        device = await create_device(db)
        user = await create_user(db, "helper", "helper@test.com")
        puzzle = await create_puzzle(db)
        await create_attempt(db, puzzle, device, user, start=1000, finish=11000, used_tutorial=True)
        await db.commit()

        response = await client.get("/api/puzzle/freeplay/leaderboard", params=LEADERBOARD_PARAMS)
        assert response.status_code == 200
        assert response.json()["count"] == 0

    @pytest.mark.asyncio
    async def test_leaderboard_best_time_per_user(self, seeded_client):
        """only the user's best time appears, not all attempts."""
        client, db = seeded_client
        device = await create_device(db)
        user = await create_user(db, "improver", "improver@test.com")
        puzzle1 = await create_puzzle(db)
        puzzle2 = await create_puzzle(db)

        await create_attempt(db, puzzle1, device, user, start=1000, finish=31000)
        await create_attempt(db, puzzle2, device, user, start=1000, finish=11000)
        await db.commit()

        response = await client.get("/api/puzzle/freeplay/leaderboard", params=LEADERBOARD_PARAMS)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert "10.00s" in data["leaderboard"][0]["duration_display"]

    @pytest.mark.asyncio
    async def test_leaderboard_excludes_anonymous(self, seeded_client):
        """anonymous attempts (no user_id) don't appear on leaderboard."""
        client, db = seeded_client
        device = await create_device(db)
        puzzle = await create_puzzle(db)
        await create_attempt(db, puzzle, device, None, start=1000, finish=11000)
        await db.commit()

        response = await client.get("/api/puzzle/freeplay/leaderboard", params=LEADERBOARD_PARAMS)
        assert response.status_code == 200
        assert response.json()["count"] == 0

    @pytest.mark.asyncio
    async def test_leaderboard_invalid_time_period(self, client):
        """invalid time_period returns 400."""
        response = await client.get("/api/puzzle/freeplay/leaderboard", params={
            **LEADERBOARD_PARAMS,
            "time_period": "invalid",
        })
        assert response.status_code == 400
        assert "time_period" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_leaderboard_invalid_scoring_method(self, client):
        """invalid scoring_method returns 400."""
        response = await client.get("/api/puzzle/freeplay/leaderboard", params={
            **LEADERBOARD_PARAMS,
            "scoring_method": "invalid",
        })
        assert response.status_code == 400
        assert "scoring_method" in response.json()["detail"]
