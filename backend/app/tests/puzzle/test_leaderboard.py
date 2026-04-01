"""tests for leaderboard service and endpoints."""

import pytest

from app.tests.conftest import (
    create_device, create_user, create_puzzle, authenticate, create_attempt,
)


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
    async def test_leaderboard_shows_user_neighbors_when_outside_top(self, seeded_client):
        """when user is at rank 10 with limit=5, show top 5 + ranks 9,10,11."""
        client, db = seeded_client
        device = await create_device(db)
        puzzle = await create_puzzle(db)

        # create 12 users with increasing times (player1=fastest, player12=slowest)
        users = []
        for i in range(1, 13):
            user = await create_user(db, f"player{i}", f"player{i}@test.com")
            users.append(user)
            await create_attempt(db, puzzle, device, user, start=1000, finish=1000 + i * 10000)

        # authenticate as player10 (rank 10)
        target_user = users[9]
        await authenticate(client, db, target_user)
        await db.commit()

        response = await client.get("/api/puzzle/freeplay/leaderboard", params={
            **LEADERBOARD_PARAMS,
            "limit": 5,
        })
        assert response.status_code == 200
        data = response.json()
        board = data["leaderboard"]

        # should have top 5 + neighbors (9, 10, 11) = 8 entries
        assert data["count"] == 8

        # top 5
        assert board[0]["username"] == "player1"
        assert board[0]["rank"] == 1
        assert board[4]["username"] == "player5"
        assert board[4]["rank"] == 5

        # neighbors
        assert board[5]["username"] == "player9"
        assert board[5]["rank"] == 9
        assert board[6]["username"] == "player10"
        assert board[6]["rank"] == 10
        assert board[6]["is_current_user"] == True
        assert board[7]["username"] == "player11"
        assert board[7]["rank"] == 11

    @pytest.mark.asyncio
    async def test_leaderboard_no_neighbors_when_in_top(self, seeded_client):
        """when user is in the top N, no neighbor section is added."""
        client, db = seeded_client
        device = await create_device(db)
        puzzle = await create_puzzle(db)

        users = []
        for i in range(1, 8):
            user = await create_user(db, f"player{i}", f"player{i}@test.com")
            users.append(user)
            await create_attempt(db, puzzle, device, user, start=1000, finish=1000 + i * 10000)

        # authenticate as player3 (rank 3, within top 5)
        await authenticate(client, db, users[2])
        await db.commit()

        response = await client.get("/api/puzzle/freeplay/leaderboard", params={
            **LEADERBOARD_PARAMS,
            "limit": 5,
        })
        assert response.status_code == 200
        data = response.json()
        # just top 5, no extra neighbors
        assert data["count"] == 5
        assert any(e["is_current_user"] for e in data["leaderboard"])

    @pytest.mark.asyncio
    async def test_leaderboard_last_place_no_neighbor_after(self, seeded_client):
        """when user is last, show neighbor before and self, but no neighbor after."""
        client, db = seeded_client
        device = await create_device(db)
        puzzle = await create_puzzle(db)

        # create 8 users (player1=fastest, player8=slowest)
        users = []
        for i in range(1, 9):
            user = await create_user(db, f"player{i}", f"player{i}@test.com")
            users.append(user)
            await create_attempt(db, puzzle, device, user, start=1000, finish=1000 + i * 10000)

        # authenticate as player8 (last place, rank 8)
        await authenticate(client, db, users[7])
        await db.commit()

        response = await client.get("/api/puzzle/freeplay/leaderboard", params={
            **LEADERBOARD_PARAMS,
            "limit": 5,
        })
        assert response.status_code == 200
        data = response.json()
        board = data["leaderboard"]

        # top 5 + neighbor before (7) + self (8) = 7 entries, no entry after
        assert data["count"] == 7

        # top 5
        assert board[4]["username"] == "player5"
        assert board[4]["rank"] == 5

        # neighbors: only before + self
        assert board[5]["username"] == "player7"
        assert board[5]["rank"] == 7
        assert board[6]["username"] == "player8"
        assert board[6]["rank"] == 8
        assert board[6]["is_current_user"] == True

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
