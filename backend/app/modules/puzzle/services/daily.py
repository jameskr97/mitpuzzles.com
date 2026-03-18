"""daily challenge service — create, status, and submit daily puzzles."""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

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
    """daily challenge operations: creation, status tracking, and submissions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_all_active_puzzle_types(self) -> List[str]:
        """get all distinct puzzle types that have active puzzles."""
        result = await self.db.execute(
            select(Puzzle.puzzle_type).where(Puzzle.is_active == True).distinct()
        )
        return list(result.scalars().all())

    async def get_or_create_daily_puzzles(self, date: datetime) -> List[DailyPuzzle]:
        """get or lazily create daily puzzles for a given date (one per active game type)."""
        puzzle_date = date.replace(hour=0, minute=0, second=0, microsecond=0)

        existing_query = (
            select(DailyPuzzle)
            .options(selectinload(DailyPuzzle.puzzle))
            .where(DailyPuzzle.puzzle_date == puzzle_date)
        )
        result = await self.db.execute(existing_query)
        existing = result.scalars().all()
        existing_types = {dp.puzzle.puzzle_type for dp in existing}

        all_types = await self._get_all_active_puzzle_types()

        if existing_types >= set(all_types):
            return list(existing)

        # create missing ones
        puzzle_service = PuzzleService(self.db)
        missing_types = [t for t in all_types if t not in existing_types]

        for game_type in missing_types:
            puzzle = await puzzle_service.get_random_puzzle(puzzle_type=game_type)
            if not puzzle:
                continue

            daily = DailyPuzzle(puzzle_date=puzzle_date, puzzle_id=puzzle.id)
            self.db.add(daily)
            try:
                await self.db.flush()
            except Exception:
                # race condition — another request created it; roll back and re-query
                await self.db.rollback()
                result = await self.db.execute(existing_query)
                return list(result.scalars().all())

        await self.db.commit()

        result = await self.db.execute(existing_query)
        return list(result.scalars().all())

    async def get_daily_puzzle_status(
        self,
        date: datetime,
        user_id: Optional[uuid.UUID],
        device_id: uuid.UUID,
    ) -> List[Dict[str, Any]]:
        """get daily puzzle status for a user/device on a given date."""
        daily_puzzles = await self.get_or_create_daily_puzzles(date)
        daily_puzzle_ids = [dp.id for dp in daily_puzzles]

        attempt_query = (
            select(DailyPuzzleAttempt)
            .options(selectinload(DailyPuzzleAttempt.attempt))
            .where(
                DailyPuzzleAttempt.device_id == device_id,
                DailyPuzzleAttempt.daily_puzzle_id.in_(daily_puzzle_ids),
            )
        )
        result = await self.db.execute(attempt_query)
        attempts = {a.daily_puzzle_id: a for a in result.scalars().all()}

        statuses = []
        for dp in daily_puzzles:
            attempt = attempts.get(dp.id)
            freeplay_attempt = attempt.attempt if attempt else None

            completion_time = None
            is_solved = False
            if freeplay_attempt and freeplay_attempt.is_solved:
                is_solved = True
                if freeplay_attempt.timestamp_finish and freeplay_attempt.timestamp_start:
                    time_seconds = (freeplay_attempt.timestamp_finish - freeplay_attempt.timestamp_start) / 1000.0
                    completion_time = format_duration(time_seconds)

            statuses.append({
                "puzzle_type": dp.puzzle.puzzle_type,
                "puzzle_id": str(dp.puzzle_id),
                "daily_puzzle_id": str(dp.id),
                "is_solved": is_solved,
                "completion_time": completion_time,
            })

        return statuses

    async def submit_daily_attempt(
        self,
        date: datetime,
        puzzle_type: str,
        device_id: uuid.UUID,
        user,
        attempt_data,
    ) -> Dict[str, Any]:
        """submit an attempt for a daily puzzle."""
        puzzle_date = date.replace(hour=0, minute=0, second=0, microsecond=0)

        # find the daily puzzle for this date + type
        query = (
            select(DailyPuzzle)
            .join(Puzzle, DailyPuzzle.puzzle_id == Puzzle.id)
            .where(DailyPuzzle.puzzle_date == puzzle_date, Puzzle.puzzle_type == puzzle_type)
        )
        daily_puzzle = await self.db.scalar(query)
        if not daily_puzzle:
            raise HTTPException(
                status_code=404,
                detail=f"No daily puzzle found for {puzzle_type} on {date.strftime('%Y-%m-%d')}",
            )

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
