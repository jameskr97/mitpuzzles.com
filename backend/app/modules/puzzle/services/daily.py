"""daily challenge service — one global puzzle per day."""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.puzzle.models import (
    Puzzle,
    FreeplayPuzzleAttempt,
    DailyPuzzle,
    DailyPuzzleAttempt,
)
from app.modules.puzzle.utils import format_duration
from app.modules.puzzle.services.puzzle import PuzzleService


class DailyPuzzleService:
    """daily challenge operations: one puzzle per day for everyone."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_daily_puzzle(self, date: datetime) -> DailyPuzzle:
        """get or lazily create the single daily puzzle for a given date."""
        puzzle_date = date.replace(hour=0, minute=0, second=0, microsecond=0)

        existing_query = (
            select(DailyPuzzle)
            .options(selectinload(DailyPuzzle.puzzle))
            .where(DailyPuzzle.puzzle_date == puzzle_date)
        )
        result = await self.db.execute(existing_query)
        existing = result.scalars().first()

        if existing:
            return existing

        # pick a random puzzle from supported daily game types
        DAILY_PUZZLE_TYPES = ["aquarium", "kakurasu", "lightup", "minesweeper", "mosaic", "nonograms", "sudoku", "tents", "hashi"]
        puzzle_service = PuzzleService(self.db)
        import random
        puzzle_type = random.choice(DAILY_PUZZLE_TYPES)
        puzzle = await puzzle_service.get_random_puzzle(puzzle_type=puzzle_type)
        if not puzzle:
            raise HTTPException(status_code=404, detail="no active puzzles available.")

        daily = DailyPuzzle(puzzle_date=puzzle_date, puzzle_id=puzzle.id)
        self.db.add(daily)
        try:
            await self.db.flush()
        except Exception:
            # race condition — another request created it; roll back and re-query
            await self.db.rollback()
            result = await self.db.execute(existing_query)
            return result.scalars().first()

        await self.db.commit()

        result = await self.db.execute(existing_query)
        return result.scalars().first()

    async def get_daily_puzzle_status(
        self,
        date: datetime,
        user_id: Optional[uuid.UUID],
        device_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """get daily puzzle status for a user/device on a given date."""
        daily_puzzle = await self.get_or_create_daily_puzzle(date)

        attempt_query = (
            select(DailyPuzzleAttempt)
            .options(selectinload(DailyPuzzleAttempt.attempt))
            .where(
                DailyPuzzleAttempt.device_id == device_id,
                DailyPuzzleAttempt.daily_puzzle_id == daily_puzzle.id,
            )
        )
        result = await self.db.execute(attempt_query)
        attempt = result.scalars().first()
        freeplay_attempt = attempt.attempt if attempt else None

        completion_time = None
        is_solved = False
        if freeplay_attempt and freeplay_attempt.is_solved:
            is_solved = True
            if freeplay_attempt.timestamp_finish and freeplay_attempt.timestamp_start:
                time_seconds = (freeplay_attempt.timestamp_finish - freeplay_attempt.timestamp_start) / 1000.0
                completion_time = format_duration(time_seconds)

        return {
            "puzzle_type": daily_puzzle.puzzle.puzzle_type,
            "puzzle_size": daily_puzzle.puzzle.puzzle_size,
            "puzzle_difficulty": daily_puzzle.puzzle.puzzle_difficulty,
            "puzzle_id": str(daily_puzzle.puzzle_id),
            "daily_puzzle_id": str(daily_puzzle.id),
            "is_solved": is_solved,
            "completion_time": completion_time,
        }

    async def submit_daily_attempt(
        self,
        date: datetime,
        device_id: uuid.UUID,
        user,
        attempt_data,
    ) -> Dict[str, Any]:
        """submit an attempt for today's daily puzzle."""
        daily_puzzle = await self.get_or_create_daily_puzzle(date)

        # check for existing attempt
        existing = await self.db.scalar(
            select(DailyPuzzleAttempt).where(
                DailyPuzzleAttempt.device_id == device_id,
                DailyPuzzleAttempt.daily_puzzle_id == daily_puzzle.id,
            )
        )

        # create the freeplay attempt
        puzzle_service = PuzzleService(self.db)
        freeplay_attempt = await puzzle_service.create_freeplay_attempt(attempt_data, device_id, user)

        if existing:
            existing.attempt_id = freeplay_attempt.id
            if user:
                existing.user_id = user.id
            await self.db.commit()
        else:
            daily_attempt = DailyPuzzleAttempt(
                user_id=user.id if user else None,
                device_id=device_id,
                daily_puzzle_id=daily_puzzle.id,
                attempt_id=freeplay_attempt.id,
            )
            self.db.add(daily_attempt)
            await self.db.commit()

        return {"status": "Daily puzzle submitted.", "id": str(freeplay_attempt.id)}
