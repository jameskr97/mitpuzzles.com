"""user stats service — per-user puzzle performance aggregation."""

import uuid
from typing import Optional, Dict, Any, List

from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.puzzle.models import Puzzle, FreeplayPuzzleAttempt


class UserStatsService:
    """aggregates puzzle performance stats for a specific user."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_stats(
        self,
        user_id: uuid.UUID,
        puzzle_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """get per-(type, size, difficulty) stats for a user."""
        duration_expr = (
            FreeplayPuzzleAttempt.timestamp_finish - FreeplayPuzzleAttempt.timestamp_start
        ) / 1000.0

        query = (
            select(
                Puzzle.puzzle_type,
                Puzzle.puzzle_size,
                Puzzle.puzzle_difficulty,
                func.count(FreeplayPuzzleAttempt.id).label("total_attempts"),
                func.sum(case((FreeplayPuzzleAttempt.is_solved == True, 1), else_=0)).label("solved"),
                func.min(
                    case(
                        (FreeplayPuzzleAttempt.is_solved == True, duration_expr),
                        else_=None,
                    )
                ).label("best_time"),
                func.avg(
                    case(
                        (FreeplayPuzzleAttempt.is_solved == True, duration_expr),
                        else_=None,
                    )
                ).label("avg_time"),
            )
            .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
            .where(
                FreeplayPuzzleAttempt.user_id == user_id,
                FreeplayPuzzleAttempt.timestamp_finish.is_not(None),
            )
        )

        if puzzle_type:
            query = query.where(Puzzle.puzzle_type == puzzle_type)

        query = query.group_by(
            Puzzle.puzzle_type, Puzzle.puzzle_size, Puzzle.puzzle_difficulty
        ).order_by(Puzzle.puzzle_type, Puzzle.puzzle_size, Puzzle.puzzle_difficulty)

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "puzzle_type": row.puzzle_type,
                "puzzle_size": row.puzzle_size,
                "puzzle_difficulty": row.puzzle_difficulty,
                "total_attempts": row.total_attempts,
                "solved": row.solved or 0,
                "best_time": round(row.best_time, 2) if row.best_time else None,
                "avg_time": round(row.avg_time, 2) if row.avg_time else None,
            }
            for row in rows
        ]

    async def get_user_solve_history(
        self,
        user_id: uuid.UUID,
        puzzle_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """get individual solved attempts ordered by time, for graphing."""
        duration_expr = (
            FreeplayPuzzleAttempt.timestamp_finish - FreeplayPuzzleAttempt.timestamp_start
        ) / 1000.0

        query = (
            select(
                Puzzle.puzzle_type,
                Puzzle.puzzle_size,
                Puzzle.puzzle_difficulty,
                FreeplayPuzzleAttempt.timestamp_finish.label("finished_at"),
                duration_expr.label("duration"),
            )
            .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
            .where(
                FreeplayPuzzleAttempt.user_id == user_id,
                FreeplayPuzzleAttempt.is_solved == True,
                FreeplayPuzzleAttempt.timestamp_finish.is_not(None),
            )
            .order_by(FreeplayPuzzleAttempt.timestamp_finish.asc())
        )

        if puzzle_type:
            query = query.where(Puzzle.puzzle_type == puzzle_type)

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "puzzle_type": row.puzzle_type,
                "puzzle_size": row.puzzle_size,
                "puzzle_difficulty": row.puzzle_difficulty,
                "finished_at": row.finished_at,
                "duration": round(row.duration, 2),
            }
            for row in rows
        ]
