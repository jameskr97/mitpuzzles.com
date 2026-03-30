"""user stats service — per-user puzzle performance aggregation."""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from sqlalchemy import select, func, case, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.puzzle.models import Puzzle, FreeplayPuzzleAttempt, DailyPuzzle, DailyPuzzleAttempt, PuzzleShown
from app.modules.puzzle.utils import format_duration


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

    async def get_user_profile(self, user) -> Dict[str, Any]:
        """assemble the full user profile stats response."""
        user_id = user.id
        duration_expr = (
            FreeplayPuzzleAttempt.timestamp_finish - FreeplayPuzzleAttempt.timestamp_start
        ) / 1000.0

        # -- aggregates: shown from puzzle_shown, solved from attempts --
        shown_query = (
            select(func.count(PuzzleShown.id).label("total_shown"))
            .where(PuzzleShown.user_id == user_id)
        )
        shown_row = (await self.db.execute(shown_query)).first()

        solved_query = (
            select(
                func.sum(case((FreeplayPuzzleAttempt.is_solved == True, 1), else_=0)).label("total_solved"),
                func.sum(
                    case(
                        (
                            and_(
                                FreeplayPuzzleAttempt.is_solved == True,
                                FreeplayPuzzleAttempt.timestamp_finish.is_not(None),
                            ),
                            duration_expr,
                        ),
                        else_=0,
                    )
                ).label("total_time"),
            )
            .where(FreeplayPuzzleAttempt.user_id == user_id)
        )
        solved_row = (await self.db.execute(solved_query)).first()

        # -- per-type breakdown: shown from puzzle_shown, solved/times from attempts --
        shown_by_type_query = (
            select(
                Puzzle.puzzle_type,
                func.count(PuzzleShown.id).label("shown_count"),
            )
            .join(Puzzle, PuzzleShown.puzzle_id == Puzzle.id)
            .where(PuzzleShown.user_id == user_id)
            .group_by(Puzzle.puzzle_type)
        )
        shown_by_type = {row.puzzle_type: row.shown_count for row in (await self.db.execute(shown_by_type_query)).all()}

        solved_by_type_query = (
            select(
                Puzzle.puzzle_type,
                func.sum(case((FreeplayPuzzleAttempt.is_solved == True, 1), else_=0)).label("solved_count"),
                func.min(
                    case((FreeplayPuzzleAttempt.is_solved == True, duration_expr), else_=None)
                ).label("best_time"),
                func.avg(
                    case((FreeplayPuzzleAttempt.is_solved == True, duration_expr), else_=None)
                ).label("avg_time"),
            )
            .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
            .where(FreeplayPuzzleAttempt.user_id == user_id)
            .group_by(Puzzle.puzzle_type)
        )
        solved_by_type = {row.puzzle_type: row for row in (await self.db.execute(solved_by_type_query)).all()}

        # merge shown + solved into per-type stats
        all_types = set(shown_by_type.keys()) | set(solved_by_type.keys())
        puzzle_type_stats = sorted([
            {
                "puzzle_type": pt,
                "solved_count": (solved_by_type[pt].solved_count or 0) if pt in solved_by_type else 0,
                "attempt_count": shown_by_type.get(pt, 0),
                "best_time": round(solved_by_type[pt].best_time, 2) if pt in solved_by_type and solved_by_type[pt].best_time else None,
                "avg_time": round(solved_by_type[pt].avg_time, 2) if pt in solved_by_type and solved_by_type[pt].avg_time else None,
            }
            for pt in all_types
        ], key=lambda x: x["solved_count"], reverse=True)

        # -- daily streak --
        daily_streak = await self._get_daily_streak(user_id)

        # -- solve time history (for chart) --
        solve_time_history = await self._get_solve_time_history(user_id)

        # -- activity feed --
        activity_feed = await self._get_activity_feed(user_id)

        # -- game log (recent attempts) --
        game_log = await self._get_game_log(user_id)

        # -- featured solves (fastest per top 2 types) --
        featured_solves = await self._get_featured_solves(user_id, puzzle_type_stats)

        return {
            "username": user.username or "anonymous",
            "member_since": user.date_created.strftime("%Y-%m-%d"),
            "is_own_profile": False,
            "total_puzzles_solved": solved_row.total_solved or 0,
            "total_puzzles_attempted": shown_row.total_shown or 0,
            "total_time_seconds": round(solved_row.total_time or 0, 1),
            "puzzle_type_stats": puzzle_type_stats,
            "daily_streak": daily_streak,
            "solve_time_history": solve_time_history,
            "activity_feed": activity_feed,
            "game_log": game_log,
            "featured_solves": featured_solves,
        }

    async def _get_daily_streak(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """compute daily challenge streak stats."""
        query = (
            select(DailyPuzzle.puzzle_date)
            .join(DailyPuzzleAttempt, DailyPuzzleAttempt.daily_puzzle_id == DailyPuzzle.id)
            .join(FreeplayPuzzleAttempt, DailyPuzzleAttempt.attempt_id == FreeplayPuzzleAttempt.id)
            .where(
                DailyPuzzleAttempt.user_id == user_id,
                FreeplayPuzzleAttempt.is_solved == True,
            )
            .distinct()
            .order_by(DailyPuzzle.puzzle_date.desc())
        )
        result = await self.db.execute(query)
        dates = [row[0] for row in result.all()]

        if not dates:
            return {"current_streak": 0, "longest_streak": 0, "total_dailies_solved": 0, "fastest_daily_count": 0}

        today = datetime.utcnow().date()
        current_streak = 0
        longest_streak = 0
        streak = 0
        prev_date = None

        for d in sorted(dates):
            d_date = d.date() if hasattr(d, "date") else d
            if prev_date is None or (d_date - prev_date).days == 1:
                streak += 1
            else:
                streak = 1
            longest_streak = max(longest_streak, streak)
            prev_date = d_date

        # current streak: count backwards from today/yesterday
        for i, d in enumerate(dates):
            d_date = d.date() if hasattr(d, "date") else d
            expected = today - timedelta(days=i)
            if d_date == expected or (i == 0 and d_date == today - timedelta(days=1)):
                current_streak += 1
            else:
                break

        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "total_dailies_solved": len(dates),
            "fastest_daily_count": 0,
        }

    async def _get_solve_time_history(self, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        """get solve time history grouped by puzzle type for the chart."""
        history = await self.get_user_solve_history(user_id)

        by_type: Dict[str, List[Dict[str, Any]]] = {}
        for entry in history:
            pt = entry["puzzle_type"]
            if pt not in by_type:
                by_type[pt] = []
            ts = entry["finished_at"]
            if isinstance(ts, (int, float)):
                date_str = datetime.utcfromtimestamp(ts / 1000).strftime("%Y-%m-%d")
            else:
                date_str = str(ts)[:10]
            by_type[pt].append({"date": date_str, "avg_time": entry["duration"]})

        return [
            {"puzzle_type": pt, "data": points}
            for pt, points in by_type.items()
        ]

    async def _get_activity_feed(self, user_id: uuid.UUID, days: int = 7) -> List[Dict[str, Any]]:
        """get recent activity grouped by day."""
        duration_expr = (
            FreeplayPuzzleAttempt.timestamp_finish - FreeplayPuzzleAttempt.timestamp_start
        ) / 1000.0

        cutoff_ms = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)

        query = (
            select(
                Puzzle.puzzle_type,
                FreeplayPuzzleAttempt.is_solved,
                FreeplayPuzzleAttempt.timestamp_finish,
                duration_expr.label("duration"),
            )
            .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
            .where(
                FreeplayPuzzleAttempt.user_id == user_id,
                FreeplayPuzzleAttempt.timestamp_finish.is_not(None),
                FreeplayPuzzleAttempt.timestamp_finish > cutoff_ms,
            )
            .order_by(FreeplayPuzzleAttempt.timestamp_finish.desc())
        )
        result = await self.db.execute(query)
        rows = result.all()

        from collections import defaultdict
        days_map: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(lambda: defaultdict(lambda: {"count": 0, "best": None}))

        for row in rows:
            ts = row.timestamp_finish
            if isinstance(ts, (int, float)):
                date_str = datetime.utcfromtimestamp(ts / 1000).strftime("%Y-%m-%d")
            else:
                date_str = str(ts)[:10]

            if row.is_solved:
                entry = days_map[date_str][row.puzzle_type]
                entry["count"] += 1
                if row.duration and (entry["best"] is None or row.duration < entry["best"]):
                    entry["best"] = row.duration

        ICONS = {
            "sudoku": "🔢", "nonograms": "🏁", "minesweeper": "💣",
            "lightup": "��", "hashi": "🌉", "mosaic": "🧩",
            "tents": "⛺", "aquarium": "🐠", "kakurasu": "⬛",
        }

        feed = []
        for date_str in sorted(days_map.keys(), reverse=True):
            entries = []
            for pt, data in days_map[date_str].items():
                icon = ICONS.get(pt, "🧩")
                text = f"Solved {data['count']} {pt.capitalize()} puzzle{'s' if data['count'] != 1 else ''}"
                detail = f"best: {format_duration(data['best'])}" if data["best"] else None
                entries.append({"icon": icon, "text": text, "detail": detail})
            feed.append({"date": date_str, "entries": entries})

        return feed

    async def _get_game_log(self, user_id: uuid.UUID, limit: int = 10) -> List[Dict[str, Any]]:
        """get recent game attempts."""
        duration_expr = (
            FreeplayPuzzleAttempt.timestamp_finish - FreeplayPuzzleAttempt.timestamp_start
        ) / 1000.0

        query = (
            select(
                FreeplayPuzzleAttempt.id.label("attempt_id"),
                Puzzle.puzzle_type,
                Puzzle.puzzle_size,
                Puzzle.puzzle_difficulty,
                FreeplayPuzzleAttempt.is_solved,
                FreeplayPuzzleAttempt.timestamp_finish,
                case(
                    (FreeplayPuzzleAttempt.is_solved == True, duration_expr),
                    else_=None,
                ).label("time"),
            )
            .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
            .where(
                FreeplayPuzzleAttempt.user_id == user_id,
                FreeplayPuzzleAttempt.timestamp_finish.is_not(None),
            )
            .order_by(FreeplayPuzzleAttempt.timestamp_finish.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "attempt_id": str(row.attempt_id),
                "puzzle_type": row.puzzle_type,
                "puzzle_size": row.puzzle_size,
                "puzzle_difficulty": row.puzzle_difficulty,
                "solved": row.is_solved,
                "time": round(row.time, 2) if row.time else None,
                "date": datetime.utcfromtimestamp(row.timestamp_finish / 1000).strftime("%Y-%m-%d")
                    if isinstance(row.timestamp_finish, (int, float))
                    else str(row.timestamp_finish)[:10],
            }
            for row in rows
        ]

    async def _get_featured_solves(
        self, user_id: uuid.UUID, puzzle_type_stats: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """get fastest solve attempt_id for top 2 most-played types."""
        top_types = [s["puzzle_type"] for s in puzzle_type_stats[:2]]
        if not top_types:
            return []

        duration_expr = (
            FreeplayPuzzleAttempt.timestamp_finish - FreeplayPuzzleAttempt.timestamp_start
        ) / 1000.0

        featured = []
        for pt in top_types:
            query = (
                select(
                    FreeplayPuzzleAttempt.id.label("attempt_id"),
                    duration_expr.label("duration"),
                )
                .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
                .where(
                    FreeplayPuzzleAttempt.user_id == user_id,
                    FreeplayPuzzleAttempt.is_solved == True,
                    Puzzle.puzzle_type == pt,
                )
                .order_by(duration_expr.asc())
                .limit(1)
            )
            result = await self.db.execute(query)
            row = result.first()
            if row:
                featured.append({
                    "puzzle_type": pt,
                    "attempt_id": str(row.attempt_id),
                    "best_time": round(row.duration, 2),
                })

        return featured
