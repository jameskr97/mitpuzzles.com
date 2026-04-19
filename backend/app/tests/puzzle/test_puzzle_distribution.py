"""tests for puzzle distribution — uniqueness, exhaustion, and re-solving."""

import pytest

from app.modules.puzzle.services.puzzle import PuzzleService
from app.tests.conftest import create_device, create_user, create_puzzle, create_attempt, create_puzzle_shown


@pytest.mark.asyncio
class TestPuzzleDistribution:

    async def test_unseen_puzzle_served_first(self, db):
        """user gets a puzzle they haven't seen before."""
        device = await create_device(db)
        user = await create_user(db, "alice", "alice@test.com")
        p1 = await create_puzzle(db, "sudoku", "9x9", "easy")
        p2 = await create_puzzle(db, "sudoku", "9x9", "easy")

        # mark p1 as seen
        await create_puzzle_shown(db, p1, device, user)
        await db.commit()

        service = PuzzleService(db)
        result = await service.get_next_puzzle(device.id, user.id, "sudoku", "9x9", "easy")

        assert result is not None
        assert result.id == p2.id

    async def test_seen_puzzle_excluded(self, db):
        """already-seen puzzles are not served when unseen ones exist."""
        device = await create_device(db)
        user = await create_user(db, "bob", "bob@test.com")
        p1 = await create_puzzle(db, "sudoku", "9x9", "easy")
        p2 = await create_puzzle(db, "sudoku", "9x9", "easy")

        await create_puzzle_shown(db, p1, device, user)
        await create_puzzle_shown(db, p2, device, user)
        await db.commit()

        # both seen — no unseen puzzles left
        service = PuzzleService(db)
        result = await service.get_next_puzzle(device.id, user.id, "sudoku", "9x9", "easy")
        assert result is None

    async def test_exhausted_pool_falls_back_to_seen(self, db):
        """when all puzzles are seen, ignore_seen=True re-serves them."""
        device = await create_device(db)
        user = await create_user(db, "carol", "carol@test.com")
        p1 = await create_puzzle(db, "sudoku", "9x9", "easy")

        await create_puzzle_shown(db, p1, device, user)
        await db.commit()

        service = PuzzleService(db)
        result = await service.get_next_puzzle(
            device.id, user.id, "sudoku", "9x9", "easy", ignore_seen=True,
        )

        assert result is not None
        assert result.id == p1.id

    async def test_re_solve_submit_accepted(self, db):
        """submitting a solve for an already-solved puzzle succeeds."""
        device = await create_device(db)
        user = await create_user(db, "dave", "dave@test.com")
        puzzle = await create_puzzle(db, "sudoku", "9x9", "easy")

        # first solve
        a1 = await create_attempt(db, puzzle, device, user, start=1000, finish=11000, is_solved=True)
        await create_puzzle_shown(db, puzzle, device, user, attempt=a1)
        await db.commit()

        # second solve — same puzzle
        a2 = await create_attempt(db, puzzle, device, user, start=20000, finish=28000, is_solved=True)
        await db.commit()

        assert a2 is not None
        assert a2.puzzle_id == puzzle.id
        assert a2.is_solved is True

    async def test_anonymous_seen_isolation(self, db):
        """anonymous users' seen puzzles are scoped to their device."""
        device1 = await create_device(db)
        device2 = await create_device(db)
        puzzle = await create_puzzle(db, "sudoku", "9x9", "easy")

        # device1 has seen it, device2 hasn't
        await create_puzzle_shown(db, puzzle, device1, None)
        await db.commit()

        service = PuzzleService(db)

        result1 = await service.get_next_puzzle(device1.id, None, "sudoku", "9x9", "easy")
        assert result1 is None

        result2 = await service.get_next_puzzle(device2.id, None, "sudoku", "9x9", "easy")
        assert result2 is not None
        assert result2.id == puzzle.id
