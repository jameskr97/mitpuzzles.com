"""tests for daily puzzle endpoints."""

import pytest
from datetime import datetime, timezone

from app.tests.conftest import (
    create_device, create_user, create_puzzle, authenticate,
    create_daily_puzzle, create_daily_attempt,
)

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


class TestDailyClaimAttempt:
    @pytest.mark.asyncio
    async def test_claim_anonymous_attempt(self, seeded_client):
        """logging in claims today's anonymous daily attempt."""
        client, db = seeded_client
        device = await create_device(db)
        user = await create_user(db, "claimer", "claimer@test.com")
        puzzle = await create_puzzle(db)
        daily = await create_daily_puzzle(db, puzzle, datetime.now(timezone.utc))
        # anonymous attempt (no user)
        await create_daily_attempt(db, daily, device, None, start=1000, finish=6000)
        await authenticate(client, db, user)
        await db.commit()

        response = await client.post(
            "/api/puzzle/daily/claim",
            cookies={"device_id": str(device.id)},
        )
        assert response.status_code == 200
        assert response.json()["claimed"] == True

        # verify: leaderboard should now show the user
        lb = await client.get(f"/api/puzzle/daily/{TODAY}/leaderboard")
        assert lb.json()["count"] == 1
        assert lb.json()["leaderboard"][0]["username"] == "claimer"

    @pytest.mark.asyncio
    async def test_claim_does_nothing_if_already_claimed(self, seeded_client):
        """claiming when user already has an attempt returns false."""
        client, db = seeded_client
        device = await create_device(db)
        user = await create_user(db, "already", "already@test.com")
        puzzle = await create_puzzle(db)
        daily = await create_daily_puzzle(db, puzzle, datetime.now(timezone.utc))
        # user already has an attempt
        await create_daily_attempt(db, daily, device, user, start=1000, finish=6000)
        await authenticate(client, db, user)
        await db.commit()

        response = await client.post(
            "/api/puzzle/daily/claim",
            cookies={"device_id": str(device.id)},
        )
        assert response.status_code == 200
        assert response.json()["claimed"] == False

    @pytest.mark.asyncio
    async def test_claim_does_nothing_if_no_anonymous_attempt(self, seeded_client):
        """claiming with no anonymous attempt on this device returns false."""
        client, db = seeded_client
        device = await create_device(db)
        user = await create_user(db, "noattempt", "noattempt@test.com")
        puzzle = await create_puzzle(db)
        await create_daily_puzzle(db, puzzle, datetime.now(timezone.utc))
        await authenticate(client, db, user)
        await db.commit()

        response = await client.post(
            "/api/puzzle/daily/claim",
            cookies={"device_id": str(device.id)},
        )
        assert response.status_code == 200
        assert response.json()["claimed"] == False

    @pytest.mark.asyncio
    async def test_claim_does_not_steal_other_device_attempt(self, seeded_client):
        """claiming only works for the current device's attempt."""
        client, db = seeded_client
        device1 = await create_device(db)
        device2 = await create_device(db)
        user = await create_user(db, "thief", "thief@test.com")
        puzzle = await create_puzzle(db)
        daily = await create_daily_puzzle(db, puzzle, datetime.now(timezone.utc))
        # anonymous attempt on device2, not device1
        await create_daily_attempt(db, daily, device2, None, start=1000, finish=6000)
        await authenticate(client, db, user)
        await db.commit()

        # try to claim from device1
        response = await client.post(
            "/api/puzzle/daily/claim",
            cookies={"device_id": str(device1.id)},
        )
        assert response.status_code == 200
        assert response.json()["claimed"] == False

    @pytest.mark.asyncio
    async def test_claim_does_not_overwrite_other_user(self, seeded_client):
        """if another user already claimed this device's attempt, can't re-claim."""
        client, db = seeded_client
        device = await create_device(db)
        user1 = await create_user(db, "first", "first@test.com")
        user2 = await create_user(db, "second", "second@test.com")
        puzzle = await create_puzzle(db)
        daily = await create_daily_puzzle(db, puzzle, datetime.now(timezone.utc))
        # user1 already has this attempt
        await create_daily_attempt(db, daily, device, user1, start=1000, finish=6000)
        await authenticate(client, db, user2)
        await db.commit()

        response = await client.post(
            "/api/puzzle/daily/claim",
            cookies={"device_id": str(device.id)},
        )
        assert response.status_code == 200
        assert response.json()["claimed"] == False


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
