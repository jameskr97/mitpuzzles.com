"""leaderboard service — freeplay and daily leaderboard computations."""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
import uuid

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from itertools import groupby

from app.modules.puzzle.models import (
    Puzzle,
    FreeplayPuzzleAttempt,
    DailyPuzzleAttempt,
    PuzzleShown,
    UserLeaderboardScore,
)
from app.modules.puzzle.utils import format_duration, redact_username
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
                FreeplayPuzzleAttempt.id.label("attempt_id"),
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
        """leaderboard using precomputed best ao3 scores from user_leaderboard_score."""
        score_type = f"ao{LEADERBOARD_TOP_N_AVERAGE}"

        conditions = [
            UserLeaderboardScore.puzzle_type == puzzle_type,
            UserLeaderboardScore.puzzle_size == puzzle_size,
            UserLeaderboardScore.puzzle_difficulty == puzzle_difficulty,
            UserLeaderboardScore.score_type == score_type,
        ]

        cutoff = _time_cutoff(time_period)
        if cutoff:
            conditions.append(UserLeaderboardScore.updated_at >= cutoff)

        query = (
            select(
                UserLeaderboardScore.user_id,
                (UserLeaderboardScore.time_ms / 1000.0).label("completion_time_seconds"),
                User.username,
            )
            .join(User, UserLeaderboardScore.user_id == User.id)
            .where(and_(*conditions))
            .order_by(UserLeaderboardScore.time_ms.asc())
        )

        all_rows = (await self.db.execute(query)).all()
        return _build_leaderboard_response(all_rows, limit, user)

    async def compute_best_ao_n(
        self,
        user_id: uuid.UUID,
        puzzle_type: str,
        puzzle_size: str,
        puzzle_difficulty: str,
        n: int = 3,
    ) -> Optional[float]:
        """compute a user's best average-of-n time (in seconds) for a puzzle category.

        returns None if the user doesn't have n consecutive solved assignments.
        """
        completion_time = (FreeplayPuzzleAttempt.timestamp_finish - FreeplayPuzzleAttempt.timestamp_start) / 1000.0

        query = (
            select(completion_time.label("duration"))
            .select_from(PuzzleShown)
            .join(Puzzle, PuzzleShown.puzzle_id == Puzzle.id)
            .outerjoin(
                FreeplayPuzzleAttempt,
                and_(
                    PuzzleShown.attempt_id == FreeplayPuzzleAttempt.id,
                    FreeplayPuzzleAttempt.is_solved == True,
                    FreeplayPuzzleAttempt.used_tutorial == False,
                    FreeplayPuzzleAttempt.timestamp_finish.is_not(None),
                    FreeplayPuzzleAttempt.timestamp_start.is_not(None),
                ),
            )
            .where(and_(
                PuzzleShown.user_id == user_id,
                Puzzle.puzzle_type == puzzle_type,
                Puzzle.puzzle_size == puzzle_size,
                Puzzle.puzzle_difficulty == puzzle_difficulty,
            ))
            .order_by(PuzzleShown.shown_at.asc())
        )

        rows = (await self.db.execute(query)).all()
        durations = [r.duration for r in rows]

        if len(durations) < n:
            return None

        best = None
        for i in range(len(durations) - n + 1):
            window = durations[i:i + n]
            if any(d is None for d in window):
                continue
            mean = sum(window) / n
            if best is None or mean < best:
                best = mean

        return best

    async def update_user_ao_score(
        self,
        user_id: uuid.UUID,
        puzzle_type: str,
        puzzle_size: str,
        puzzle_difficulty: str,
        score_type: str = "ao3",
        commit: bool = True,
    ) -> Optional[float]:
        """compute and upsert a user's best ao score. returns the score or None."""
        n = int(score_type.removeprefix("ao"))
        best = await self.compute_best_ao_n(user_id, puzzle_type, puzzle_size, puzzle_difficulty, n)

        if best is None:
            return None

        time_ms = round(best * 1000.0)

        # check for existing record
        existing = await self.db.scalar(
            select(UserLeaderboardScore).where(and_(
                UserLeaderboardScore.user_id == user_id,
                UserLeaderboardScore.puzzle_type == puzzle_type,
                UserLeaderboardScore.puzzle_size == puzzle_size,
                UserLeaderboardScore.puzzle_difficulty == puzzle_difficulty,
                UserLeaderboardScore.score_type == score_type,
            ))
        )

        if existing:
            if time_ms < existing.time_ms:
                existing.time_ms = time_ms
        else:
            record = UserLeaderboardScore(
                user_id=user_id,
                puzzle_type=puzzle_type,
                puzzle_size=puzzle_size,
                puzzle_difficulty=puzzle_difficulty,
                score_type=score_type,
                time_ms=time_ms,
            )
            self.db.add(record)

        if commit:
            await self.db.commit()

        return time_ms

    async def backfill_ao_scores(
        self,
        score_type: str = "ao3",
        on_progress=None,
    ) -> dict:
        """backfill best ao scores for all users across all puzzle categories.

        on_progress is an optional callback(user_id, puzzle_type, size, difficulty, score).
        returns {processed: int, updated: int}.
        """
        n = int(score_type.removeprefix("ao"))

        # find all distinct (user, type, size, difficulty) combos with enough puzzle_shown records
        combos_query = (
            select(
                PuzzleShown.user_id,
                Puzzle.puzzle_type,
                Puzzle.puzzle_size,
                Puzzle.puzzle_difficulty,
            )
            .join(Puzzle, PuzzleShown.puzzle_id == Puzzle.id)
            .where(PuzzleShown.user_id.is_not(None))
            .group_by(PuzzleShown.user_id, Puzzle.puzzle_type, Puzzle.puzzle_size, Puzzle.puzzle_difficulty)
            .having(func.count() >= n)
        )

        combos = (await self.db.execute(combos_query)).all()
        processed = 0
        updated = 0

        for row in combos:
            score = await self.update_user_ao_score(
                user_id=row.user_id,
                puzzle_type=row.puzzle_type,
                puzzle_size=row.puzzle_size,
                puzzle_difficulty=row.puzzle_difficulty,
                score_type=score_type,
                commit=False,
            )
            processed += 1
            if score is not None:
                updated += 1
            if on_progress:
                on_progress(row.user_id, row.puzzle_type, row.puzzle_size, row.puzzle_difficulty, score)

        await self.db.flush()
        return {"processed": processed, "updated": updated}

    async def get_puzzle_leaderboard(
        self,
        puzzle_id: uuid.UUID,
        limit: int = 10,
        user=None,
    ) -> Dict[str, Any]:
        """get leaderboard for a specific puzzle by puzzle_id."""
        completion_time = (FreeplayPuzzleAttempt.timestamp_finish - FreeplayPuzzleAttempt.timestamp_start) / 1000.0

        # best time per user for this puzzle
        best_times = (
            select(
                FreeplayPuzzleAttempt.user_id,
                func.min(completion_time).label("best_time_seconds"),
            )
            .where(
                FreeplayPuzzleAttempt.puzzle_id == puzzle_id,
                FreeplayPuzzleAttempt.is_solved == True,
                FreeplayPuzzleAttempt.user_id.is_not(None),
                FreeplayPuzzleAttempt.timestamp_finish.is_not(None),
                FreeplayPuzzleAttempt.timestamp_start.is_not(None),
                FreeplayPuzzleAttempt.used_tutorial == False,
            )
            .group_by(FreeplayPuzzleAttempt.user_id)
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
            "username": redact_username(row.username),
            "is_current_user": is_current,
            "attempt_id": str(row.attempt_id) if hasattr(row, "attempt_id") else None,
        })

    # if user is outside top N, show their neighbors (before, self, after)
    if user and current_user_entry and not current_user_in_top:
        user_idx = current_user_rank - 1  # 0-based index into all_rows

        for offset in [-1, 0, 1]:
            neighbor_idx = user_idx + offset
            if neighbor_idx < 0 or neighbor_idx >= len(all_rows):
                continue
            # skip if already in the top entries
            if neighbor_idx < limit:
                continue
            row = all_rows[neighbor_idx]
            entries.append({
                "rank": neighbor_idx + 1,
                "duration_display": format_duration(row.completion_time_seconds),
                "username": redact_username(row.username),
                "is_current_user": bool(row.user_id == user.id),
                "attempt_id": str(row.attempt_id) if hasattr(row, "attempt_id") else None,
            })

    return {"leaderboard": entries, "count": len(entries)}
