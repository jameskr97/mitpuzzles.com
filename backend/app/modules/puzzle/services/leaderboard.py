"""leaderboard service — freeplay and daily leaderboard computations."""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
import uuid

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.puzzle.models import (
    Puzzle,
    FreeplayPuzzleAttempt,
    DailyPuzzleAttempt,
)
from app.modules.puzzle.utils import format_duration
from app.modules.authentication import User

LEADERBOARD_TOP_N_AVERAGE = 3


class LeaderboardService:
    """leaderboard computations for freeplay and daily puzzles."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_freeplay_leaderboard(
        self,
        puzzle_type: str,
        puzzle_size: str,
        puzzle_difficulty: str,
        limit: int = 10,
        user=None,
        time_period: str = "all_time",
    ) -> Dict[str, Any]:
        """get leaderboard using single best time per user."""
        cutoff = _time_cutoff(time_period)

        base_conditions = _freeplay_base_conditions(puzzle_type, puzzle_size, puzzle_difficulty, cutoff)

        completion_time = (FreeplayPuzzleAttempt.timestamp_finish - FreeplayPuzzleAttempt.timestamp_start) / 1000.0

        # subquery: best time per user
        best_times = (
            select(
                FreeplayPuzzleAttempt.user_id,
                func.min(completion_time).label("best_time_seconds"),
            )
            .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
            .where(and_(*base_conditions))
            .group_by(FreeplayPuzzleAttempt.user_id)
            .subquery()
        )

        # main query: join back to get usernames, match on best time
        main_conditions = [
            FreeplayPuzzleAttempt.is_solved == True,
            FreeplayPuzzleAttempt.user_id.is_not(None),
            Puzzle.puzzle_type == puzzle_type,
            Puzzle.puzzle_size == puzzle_size,
            Puzzle.puzzle_difficulty == puzzle_difficulty,
        ]
        if cutoff:
            main_conditions.append(FreeplayPuzzleAttempt.created_at >= cutoff)

        query = (
            select(
                FreeplayPuzzleAttempt.user_id,
                completion_time.label("completion_time_seconds"),
                User.username,
            )
            .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
            .join(User, FreeplayPuzzleAttempt.user_id == User.id)
            .join(
                best_times,
                and_(
                    FreeplayPuzzleAttempt.user_id == best_times.c.user_id,
                    completion_time == best_times.c.best_time_seconds,
                ),
            )
            .where(and_(*main_conditions))
            .order_by(completion_time.asc())
        )

        all_rows = (await self.db.execute(query)).all()
        return _build_leaderboard_response(all_rows, limit, user)

    async def get_freeplay_leaderboard_ao_n(
        self,
        puzzle_type: str,
        puzzle_size: str,
        puzzle_difficulty: str,
        limit: int = 10,
        user=None,
        time_period: str = "all_time",
    ) -> Dict[str, Any]:
        """get leaderboard using average of best N times. users need >= N solves to appear."""
        n = LEADERBOARD_TOP_N_AVERAGE
        cutoff = _time_cutoff(time_period)

        base_conditions = _freeplay_base_conditions(puzzle_type, puzzle_size, puzzle_difficulty, cutoff)
        completion_time = (FreeplayPuzzleAttempt.timestamp_finish - FreeplayPuzzleAttempt.timestamp_start) / 1000.0

        # rank each user's solves by time
        ranked = (
            select(
                FreeplayPuzzleAttempt.user_id,
                completion_time.label("completion_time_seconds"),
                func.row_number()
                .over(partition_by=FreeplayPuzzleAttempt.user_id, order_by=completion_time.asc())
                .label("rn"),
            )
            .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
            .where(and_(*base_conditions))
            .subquery()
        )

        # average of top N, only for users with >= N solves
        avg_subquery = (
            select(
                ranked.c.user_id,
                func.avg(ranked.c.completion_time_seconds).label("avg_time_seconds"),
            )
            .where(ranked.c.rn <= n)
            .group_by(ranked.c.user_id)
            .having(func.count() >= n)
            .subquery()
        )

        query = (
            select(
                avg_subquery.c.user_id,
                avg_subquery.c.avg_time_seconds.label("completion_time_seconds"),
                User.username,
            )
            .join(User, avg_subquery.c.user_id == User.id)
            .order_by(avg_subquery.c.avg_time_seconds.asc())
        )

        all_rows = (await self.db.execute(query)).all()
        return _build_leaderboard_response(all_rows, limit, user)

    async def get_daily_leaderboard(
        self,
        daily_puzzle_id: uuid.UUID,
        limit: int = 10,
        user=None,
    ) -> Dict[str, Any]:
        """get leaderboard for a specific daily puzzle."""
        completion_time = (FreeplayPuzzleAttempt.timestamp_finish - FreeplayPuzzleAttempt.timestamp_start) / 1000.0

        best_times = (
            select(
                DailyPuzzleAttempt.user_id,
                func.min(completion_time).label("best_time_seconds"),
            )
            .join(FreeplayPuzzleAttempt, DailyPuzzleAttempt.attempt_id == FreeplayPuzzleAttempt.id)
            .where(
                DailyPuzzleAttempt.daily_puzzle_id == daily_puzzle_id,
                DailyPuzzleAttempt.user_id.is_not(None),
                FreeplayPuzzleAttempt.is_solved == True,
                FreeplayPuzzleAttempt.timestamp_finish.is_not(None),
                FreeplayPuzzleAttempt.timestamp_start.is_not(None),
            )
            .group_by(DailyPuzzleAttempt.user_id)
            .subquery()
        )

        query = (
            select(
                best_times.c.user_id,
                best_times.c.best_time_seconds.label("completion_time_seconds"),
                User.username,
            )
            .join(User, best_times.c.user_id == User.id)
            .order_by(best_times.c.best_time_seconds.asc())
        )

        all_rows = (await self.db.execute(query)).all()
        return _build_leaderboard_response(all_rows, limit, user)


# --- shared helpers ---


def _time_cutoff(time_period: str) -> Optional[datetime]:
    """convert a time period string to a naive UTC cutoff datetime."""
    now = datetime.utcnow()
    if time_period == "today":
        return now - timedelta(hours=24)
    elif time_period == "weekly":
        return now - timedelta(days=7)
    elif time_period == "monthly":
        return now - timedelta(days=30)
    return None


def _freeplay_base_conditions(
    puzzle_type: str, puzzle_size: str, puzzle_difficulty: str, cutoff: Optional[datetime]
) -> List:
    """build the common WHERE conditions for freeplay leaderboard queries."""
    conditions = [
        FreeplayPuzzleAttempt.is_solved == True,
        FreeplayPuzzleAttempt.user_id.is_not(None),
        Puzzle.puzzle_type == puzzle_type,
        Puzzle.puzzle_size == puzzle_size,
        Puzzle.puzzle_difficulty == puzzle_difficulty,
        FreeplayPuzzleAttempt.timestamp_finish.is_not(None),
        FreeplayPuzzleAttempt.timestamp_start.is_not(None),
        FreeplayPuzzleAttempt.used_tutorial == False,
    ]
    if cutoff:
        conditions.append(FreeplayPuzzleAttempt.created_at >= cutoff)
    return conditions


def _build_leaderboard_response(all_rows, limit: int, user) -> Dict[str, Any]:
    """build the leaderboard response dict from ranked rows."""
    current_user_entry = None
    current_user_rank = None

    if user:
        for idx, row in enumerate(all_rows, 1):
            if row.user_id == user.id:
                current_user_rank = idx
                current_user_entry = row
                break

    top_entries = all_rows[:limit]
    entries = []
    current_user_in_top = False

    for rank, row in enumerate(top_entries, 1):
        is_current = bool(user and row.user_id == user.id)
        if is_current:
            current_user_in_top = True
        entries.append({
            "rank": rank,
            "duration_display": format_duration(row.completion_time_seconds),
            "username": row.username,
            "is_current_user": is_current,
        })

    # append current user at their actual rank if they're not in the top N
    if user and current_user_entry and not current_user_in_top:
        entries.append({
            "rank": current_user_rank,
            "duration_display": format_duration(current_user_entry.completion_time_seconds),
            "username": current_user_entry.username,
            "is_current_user": True,
        })

    return {"leaderboard": entries, "count": len(entries)}
