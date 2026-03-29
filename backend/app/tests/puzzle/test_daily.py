"""tests for daily puzzle endpoints."""

import pytest
import pytest_asyncio
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

import uuid6

from app.main import app
from app.dependencies import get_async_session
from app.models import Base
from app.modules.puzzle.models import Puzzle, FreeplayPuzzleAttempt, DailyPuzzle, DailyPuzzleAttempt
from app.modules.tracking import Device
from app.modules.authentication import User, AccessToken


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


async def authenticate(client: AsyncClient, db: AsyncSession, user: User) -> None:
    """create an access token and set the cookie on the client."""
    import secrets
    token = secrets.token_urlsafe(32)
    access_token = AccessToken(token=token, user_id=user.id)
    db.add(access_token)
    await db.flush()
    client.cookies.set("access_token", token)


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


# --- fixture ---

@pytest_asyncio.fixture
async def seeded_client(postgres_url) -> AsyncGenerator[tuple[AsyncClient, AsyncSession], None]:
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


TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")


# --- tests ---

class TestDailyToday:
    @pytest.mark.asyncio
    async def test_today_creates_puzzle(self, seeded_client):
        """GET /daily/today creates a daily puzzle if none exists."""
        client, db = seeded_client
        device = await create_device(db)
        await create_puzzle(db)
        await db.commit()

        response = await client.get(
            "/api/puzzle/daily/today",
            cookies={"device_id": str(device.id)},
        )
        assert response.status_code == 200
        data = response.json()
        assert "date" in data
        assert "puzzle" in data
        puzzle = data["puzzle"]
        assert puzzle["puzzle_type"] == "sudoku"
        assert puzzle["is_solved"] == False

    @pytest.mark.asyncio
    async def test_today_returns_same_puzzle(self, seeded_client):
        """calling /daily/today twice returns the same puzzle."""
        client, db = seeded_client
        device = await create_device(db)
        await create_puzzle(db)
        await db.commit()

        r1 = await client.get("/api/puzzle/daily/today", cookies={"device_id": str(device.id)})
        r2 = await client.get("/api/puzzle/daily/today", cookies={"device_id": str(device.id)})
        assert r1.json()["puzzle"]["puzzle_id"] == r2.json()["puzzle"]["puzzle_id"]

    @pytest.mark.asyncio
    async def test_today_shows_solved(self, seeded_client):
        """status shows is_solved=true after submitting."""
        client, db = seeded_client
        device = await create_device(db)
        user = await create_user(db, "solver", "solver@test.com")
        puzzle = await create_puzzle(db)
        daily = await create_daily_puzzle(db, puzzle, datetime.now(timezone.utc))
        await create_daily_attempt(db, daily, device, user, start=1000, finish=11000)
        await authenticate(client, db, user)
        await db.commit()

        response = await client.get(
            "/api/puzzle/daily/today",
            cookies={"device_id": str(device.id)},
        )
        assert response.status_code == 200
        assert response.json()["puzzle"]["is_solved"] == True
        assert response.json()["puzzle"]["completion_time"] is not None


class TestDailyDefinition:
    @pytest.mark.asyncio
    async def test_get_definition(self, seeded_client):
        """GET /daily/{date}/definition returns the puzzle definition."""
        client, db = seeded_client
        puzzle = await create_puzzle(db)
        await create_daily_puzzle(db, puzzle, datetime.now(timezone.utc))
        await db.commit()

        response = await client.get(f"/api/puzzle/daily/{TODAY}/definition")
        assert response.status_code == 200
        data = response.json()
        assert data["puzzle_type"] == "sudoku"
        assert str(data["id"]) == str(puzzle.id)

    @pytest.mark.asyncio
    async def test_invalid_date_format(self, seeded_client):
        """invalid date format returns 400."""
        client, _ = seeded_client
        response = await client.get("/api/puzzle/daily/not-a-date/definition")
        assert response.status_code == 400


class TestDailySubmit:
    @pytest.mark.asyncio
    async def test_submit_attempt(self, seeded_client):
        """POST /daily/{date}/submit creates a daily attempt."""
        client, db = seeded_client
        device = await create_device(db)
        user = await create_user(db, "submitter", "submitter@test.com")
        puzzle = await create_puzzle(db)
        await create_daily_puzzle(db, puzzle, datetime.now(timezone.utc))
        await authenticate(client, db, user)
        await db.commit()

        response = await client.post(
            f"/api/puzzle/daily/{TODAY}/submit",
            json={
                "puzzle_id": str(puzzle.id),
                "timestamp_start": 1000,
                "timestamp_finish": 11000,
                "action_history": [],
                "board_state": [],
                "is_solved": True,
                "used_tutorial": False,
            },
            cookies={"device_id": str(device.id)},
        )
        assert response.status_code == 201
        assert response.json()["status"] == "Daily puzzle submitted."

    @pytest.mark.asyncio
    async def test_submit_replaces_existing(self, seeded_client):
        """submitting again updates the existing daily attempt."""
        client, db = seeded_client
        device = await create_device(db)
        user = await create_user(db, "retrier", "retrier@test.com")
        puzzle = await create_puzzle(db)
        await create_daily_puzzle(db, puzzle, datetime.now(timezone.utc))
        await authenticate(client, db, user)
        await db.commit()

        payload = {
            "puzzle_id": str(puzzle.id),
            "timestamp_start": 1000,
            "timestamp_finish": 11000,
            "action_history": [],
            "board_state": [],
            "is_solved": True,
            "used_tutorial": False,
        }

        r1 = await client.post(f"/api/puzzle/daily/{TODAY}/submit", json=payload, cookies={"device_id": str(device.id)})
        r2 = await client.post(f"/api/puzzle/daily/{TODAY}/submit", json=payload, cookies={"device_id": str(device.id)})
        assert r1.status_code == 201
        assert r2.status_code == 201
        # second submit should succeed (updates existing, not duplicate)
        assert r1.json()["id"] != r2.json()["id"]


class TestDailyLeaderboard:
    @pytest.mark.asyncio
    async def test_empty_leaderboard(self, seeded_client):
        """daily leaderboard is empty with no attempts."""
        client, db = seeded_client
        puzzle = await create_puzzle(db)
        await create_daily_puzzle(db, puzzle, datetime.now(timezone.utc))
        await db.commit()

        response = await client.get(f"/api/puzzle/daily/{TODAY}/leaderboard")
        assert response.status_code == 200
        assert response.json()["leaderboard"] == []
        assert response.json()["count"] == 0

    @pytest.mark.asyncio
    async def test_leaderboard_with_solves(self, seeded_client):
        """daily leaderboard ranks solvers by time."""
        client, db = seeded_client
        device1 = await create_device(db)
        device2 = await create_device(db)
        puzzle = await create_puzzle(db)
        daily = await create_daily_puzzle(db, puzzle, datetime.now(timezone.utc))

        fast = await create_user(db, "fast", "fast@test.com")
        slow = await create_user(db, "slow", "slow@test.com")
        await create_daily_attempt(db, daily, device1, fast, start=1000, finish=6000)
        await create_daily_attempt(db, daily, device2, slow, start=1000, finish=31000)
        await db.commit()

        response = await client.get(f"/api/puzzle/daily/{TODAY}/leaderboard")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert data["leaderboard"][0]["username"] == "fast"
        assert data["leaderboard"][0]["rank"] == 1
        assert data["leaderboard"][1]["username"] == "slow"
        assert data["leaderboard"][1]["rank"] == 2

    @pytest.mark.asyncio
    async def test_leaderboard_excludes_unsolved(self, seeded_client):
        """unsolved daily attempts don't appear on the leaderboard."""
        client, db = seeded_client
        device = await create_device(db)
        puzzle = await create_puzzle(db)
        daily = await create_daily_puzzle(db, puzzle, datetime.now(timezone.utc))

        user = await create_user(db, "quitter", "quitter@test.com")
        await create_daily_attempt(db, daily, device, user, start=1000, finish=11000, is_solved=False)
        await db.commit()

        response = await client.get(f"/api/puzzle/daily/{TODAY}/leaderboard")
        assert response.status_code == 200
        assert response.json()["count"] == 0

    @pytest.mark.asyncio
    async def test_leaderboard_excludes_anonymous(self, seeded_client):
        """anonymous daily attempts don't appear on the leaderboard."""
        client, db = seeded_client
        device = await create_device(db)
        puzzle = await create_puzzle(db)
        daily = await create_daily_puzzle(db, puzzle, datetime.now(timezone.utc))

        await create_daily_attempt(db, daily, device, None, start=1000, finish=11000)
        await db.commit()

        response = await client.get(f"/api/puzzle/daily/{TODAY}/leaderboard")
        assert response.status_code == 200
        assert response.json()["count"] == 0


class TestDailyOnePuzzlePerDate:
    @pytest.mark.asyncio
    async def test_only_one_puzzle_per_date(self, seeded_client):
        """even with multiple active puzzle types, only one daily puzzle is created."""
        client, db = seeded_client
        device = await create_device(db)
        await create_puzzle(db, puzzle_type="sudoku")
        await create_puzzle(db, puzzle_type="mosaic", size="5x5")
        await create_puzzle(db, puzzle_type="hashi", size="7x7")
        await db.commit()

        r1 = await client.get("/api/puzzle/daily/today", cookies={"device_id": str(device.id)})
        assert r1.status_code == 200
        puzzle_id_1 = r1.json()["puzzle"]["puzzle_id"]

        # second call returns the same single puzzle
        r2 = await client.get("/api/puzzle/daily/today", cookies={"device_id": str(device.id)})
        assert r2.json()["puzzle"]["puzzle_id"] == puzzle_id_1
