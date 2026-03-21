"""core puzzle service — get, create, record, browse operations."""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from fastapi import HTTPException
from sqlalchemy import select, func, Integer, cast, and_, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload
from sqlalchemy.sql.functions import count

from app.modules.puzzle.models import (
    Puzzle,
    FreeplayPuzzleAttempt,
    PuzzlePriority,
    PuzzleShown,
)
from app.modules.puzzle.formatting import format_puzzle_for_frontend, format_puzzle_with_solution


NONOGRAMS_MIN_BLACK_CELLS_PERCENTAGE = 0.1


class PuzzleService:
    """core puzzle operations: queries, creation, and recording."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_puzzle_by_id(self, puzzle_id: uuid.UUID) -> Optional[Puzzle]:
        return await self.db.scalar(select(Puzzle).where(Puzzle.id == puzzle_id))

    async def get_types(self) -> Dict[str, Any]:
        """get all puzzle types with their available size/difficulty combinations."""
        types_config = {}

        puzzle_types = (await self.db.scalars(select(Puzzle.puzzle_type).distinct())).all()
        for puzzle_type in puzzle_types:
            query = (
                select(Puzzle.puzzle_size, Puzzle.puzzle_difficulty)
                .distinct(Puzzle.puzzle_size, Puzzle.puzzle_difficulty)
                .where(Puzzle.puzzle_type == puzzle_type)
                .order_by(Puzzle.puzzle_size)
            )
            difficulty_combinations_rows = (await self.db.execute(query)).all()
            variants = [{"size": row[0], "difficulty": row[1]} for row in difficulty_combinations_rows]
            variants.sort(key=lambda v: _sort_key((v["size"], v["difficulty"])))

            num_puzzles = await self.db.scalar(
                select(count(Puzzle.id)).where(Puzzle.puzzle_type == puzzle_type)
            )
            types_config[puzzle_type] = {
                "available_difficulties": variants,
                "default_difficulty": variants[0],
                "total_puzzles": num_puzzles,
            }
        return types_config

    async def get_random_puzzle(
        self,
        puzzle_type: str,
        puzzle_size: Optional[str] = None,
        puzzle_difficulty: Optional[str] = None,
    ) -> Optional[Puzzle]:
        """get a random active puzzle matching the given criteria."""
        query = select(Puzzle).where(Puzzle.puzzle_type == puzzle_type, Puzzle.is_active == True)

        if puzzle_size:
            query = query.where(Puzzle.puzzle_size == puzzle_size)
        else:
            query = query.where(Puzzle.puzzle_size == await self._smallest_size(puzzle_type))

        if puzzle_difficulty:
            query = query.where(Puzzle.puzzle_difficulty == puzzle_difficulty)

        query = self._apply_nonograms_filter(query, puzzle_type)
        query = query.order_by(func.random())
        return await self.db.scalar(query)

    async def get_next_puzzle(
        self,
        device_id: uuid.UUID,
        user_id: Optional[uuid.UUID],
        puzzle_type: str,
        puzzle_size: Optional[str] = None,
        puzzle_difficulty: Optional[str] = None,
        ignore_seen: bool = False,
    ) -> Optional[Puzzle]:
        """get the next puzzle for a user/device, respecting priority and uniqueness rules.

        rules:
        - logged in users: can't see same puzzle on ANY device
        - anonymous users: can't see same puzzle on THEIR device
        """
        query = select(Puzzle).where(Puzzle.puzzle_type == puzzle_type, Puzzle.is_active == True)

        if puzzle_size:
            query = query.where(Puzzle.puzzle_size == puzzle_size)
        else:
            query = query.where(Puzzle.puzzle_size == await self._smallest_size(puzzle_type))

        if puzzle_difficulty:
            query = query.where(Puzzle.puzzle_difficulty == puzzle_difficulty)

        query = self._apply_nonograms_filter(query, puzzle_type)

        # left join with active priority records
        PriorityAlias = aliased(PuzzlePriority)
        query = query.outerjoin(
            PriorityAlias,
            and_(Puzzle.id == PriorityAlias.puzzle_id, PriorityAlias.removed_at == None),
        )

        # exclude already-seen puzzles
        if not ignore_seen:
            ShownAlias = aliased(PuzzleShown)
            if user_id:
                query = query.outerjoin(
                    ShownAlias,
                    and_(Puzzle.id == ShownAlias.puzzle_id, ShownAlias.user_id == user_id),
                )
            else:
                query = query.outerjoin(
                    ShownAlias,
                    and_(
                        Puzzle.id == ShownAlias.puzzle_id,
                        ShownAlias.device_id == device_id,
                        ShownAlias.user_id == None,
                    ),
                )
            query = query.where(ShownAlias.id == None)

        # try priority puzzles first
        priority_puzzle = await self.db.scalar(
            query.where(PriorityAlias.id.is_not(None)).order_by(func.random()).limit(1)
        )
        if priority_puzzle:
            return priority_puzzle

        # fall back to any random puzzle
        return await self.db.scalar(query.order_by(func.random()).limit(1))

    async def browse_puzzles(
        self,
        puzzle_id: Optional[str] = None,
        puzzle_types: Optional[List[str]] = None,
        puzzle_sizes: Optional[List[str]] = None,
        puzzle_difficulties: Optional[List[str]] = None,
        has_attempts: Optional[str] = None,
        include_solution: bool = False,
        limit: int = 36,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """browse puzzles with optional filtering and pagination."""
        excluded_types = ["battleships", "norinori"]

        conditions = [~Puzzle.puzzle_type.in_(excluded_types)]
        if puzzle_id:
            conditions.append(Puzzle.id == uuid.UUID(puzzle_id))
        if puzzle_types:
            conditions.append(Puzzle.puzzle_type.in_(puzzle_types))
        if puzzle_sizes:
            conditions.append(Puzzle.puzzle_size.in_(puzzle_sizes))
        if puzzle_difficulties:
            conditions.append(Puzzle.puzzle_difficulty.in_(puzzle_difficulties))

        if has_attempts == "with_attempts":
            subq = select(FreeplayPuzzleAttempt.id).where(FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
            conditions.append(exists(subq))
        elif has_attempts == "without_attempts":
            subq = select(FreeplayPuzzleAttempt.id).where(FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
            conditions.append(~exists(subq))

        base_query = select(Puzzle).where(*conditions)
        total_count = await self.db.scalar(select(func.count(Puzzle.id)).where(*conditions))

        if total_count == 0:
            return {"puzzles": [], "total_count": 0, "offset": offset, "limit": limit, "has_more": False}

        result = await self.db.execute(
            base_query.order_by(Puzzle.puzzle_type).limit(limit).offset(offset)
        )
        puzzles = result.scalars().all()

        format_fn = format_puzzle_with_solution if include_solution else format_puzzle_for_frontend
        return {
            "puzzles": [format_fn(p) for p in puzzles],
            "total_count": total_count,
            "offset": offset,
            "limit": limit,
            "has_more": offset + limit < total_count,
        }

    async def get_dynamic_filter_options(
        self,
        puzzle_types: Optional[List[str]] = None,
        puzzle_sizes: Optional[List[str]] = None,
        puzzle_difficulties: Optional[List[str]] = None,
        has_attempts: Optional[str] = None,
        filter_user_id: Optional[uuid.UUID] = None,
        filter_device_id: Optional[uuid.UUID] = None,
    ) -> Dict[str, Any]:
        """get available filter options with counts based on current selections."""
        excluded_types = ["battleships", "norinori"]

        def base_conditions(exclude_dimension: str):
            conds = [~Puzzle.puzzle_type.in_(excluded_types)]
            if exclude_dimension != "puzzle_type" and puzzle_types:
                conds.append(Puzzle.puzzle_type.in_(puzzle_types))
            if exclude_dimension != "puzzle_size" and puzzle_sizes:
                conds.append(Puzzle.puzzle_size.in_(puzzle_sizes))
            if exclude_dimension != "puzzle_difficulty" and puzzle_difficulties:
                conds.append(Puzzle.puzzle_difficulty.in_(puzzle_difficulties))
            if exclude_dimension != "has_attempts" and has_attempts:
                subq = select(FreeplayPuzzleAttempt.id).where(FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
                if has_attempts == "with_attempts":
                    conds.append(exists(subq))
                elif has_attempts == "without_attempts":
                    conds.append(~exists(subq))
            if filter_user_id:
                subq = select(FreeplayPuzzleAttempt.id).where(
                    FreeplayPuzzleAttempt.puzzle_id == Puzzle.id,
                    FreeplayPuzzleAttempt.user_id == filter_user_id,
                )
                conds.append(exists(subq))
            if filter_device_id:
                subq = select(FreeplayPuzzleAttempt.id).where(
                    FreeplayPuzzleAttempt.puzzle_id == Puzzle.id,
                    FreeplayPuzzleAttempt.device_id == filter_device_id,
                )
                conds.append(exists(subq))
            return conds

        async def count_dimension(column, exclude_dim: str):
            all_values = (
                await self.db.execute(select(column).distinct().where(~Puzzle.puzzle_type.in_(excluded_types)))
            ).scalars().all()
            results = []
            for value in all_values:
                if value is None:
                    continue
                q = select(func.count(Puzzle.id)).where(column == value, *base_conditions(exclude_dim))
                c = await self.db.scalar(q)
                results.append({"value": value, "count": c})
            return results

        available_types = await count_dimension(Puzzle.puzzle_type, "puzzle_type")
        available_sizes = await count_dimension(Puzzle.puzzle_size, "puzzle_size")
        available_difficulties = await count_dimension(Puzzle.puzzle_difficulty, "puzzle_difficulty")

        # attempts filter counts
        base_conds = base_conditions("has_attempts")
        total_count = await self.db.scalar(select(func.count(Puzzle.id)).where(*base_conds))
        with_subq = select(FreeplayPuzzleAttempt.id).where(FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
        with_count = await self.db.scalar(
            select(func.count(Puzzle.id)).where(exists(with_subq), *base_conds)
        )
        without_count = total_count - with_count

        return {
            "puzzle_types": available_types,
            "puzzle_sizes": available_sizes,
            "puzzle_difficulties": available_difficulties,
            "attempts_options": [
                {"value": "all", "count": total_count},
                {"value": "with_attempts", "count": with_count},
                {"value": "without_attempts", "count": without_count},
            ],
        }

    async def get_puzzle_stats(self, puzzle_id: uuid.UUID) -> Dict[str, Any]:
        """get statistics for a specific puzzle."""
        from sqlalchemy import case

        duration_expr = (FreeplayPuzzleAttempt.timestamp_finish - FreeplayPuzzleAttempt.timestamp_start) / 1000.0

        result = await self.db.execute(
            select(
                func.count(FreeplayPuzzleAttempt.id).label("total_attempts"),
                func.sum(case((FreeplayPuzzleAttempt.is_solved == True, 1), else_=0)).label("solved_attempts"),
                func.sum(case((FreeplayPuzzleAttempt.user_id.is_not(None), 1), else_=0)).label("authenticated_attempts"),
                func.sum(case((FreeplayPuzzleAttempt.user_id.is_(None), 1), else_=0)).label("anonymous_attempts"),
                func.avg(duration_expr).label("avg_duration_seconds"),
                func.min(duration_expr).label("min_duration_seconds"),
                func.max(duration_expr).label("max_duration_seconds"),
                func.count(func.distinct(FreeplayPuzzleAttempt.device_id)).label("unique_devices"),
                func.count(func.distinct(FreeplayPuzzleAttempt.user_id)).label("unique_users"),
            ).where(
                FreeplayPuzzleAttempt.puzzle_id == puzzle_id,
                FreeplayPuzzleAttempt.timestamp_finish.is_not(None),
            )
        )
        row = result.one()

        total = row.total_attempts or 0
        solved = row.solved_attempts or 0

        return {
            "puzzle_id": str(puzzle_id),
            "total_attempts": total,
            "solved_attempts": solved,
            "solve_rate": round(solved / total * 100, 1) if total > 0 else 0,
            "authenticated_attempts": row.authenticated_attempts or 0,
            "anonymous_attempts": row.anonymous_attempts or 0,
            "avg_duration_seconds": round(row.avg_duration_seconds, 1) if row.avg_duration_seconds else None,
            "min_duration_seconds": round(row.min_duration_seconds, 1) if row.min_duration_seconds else None,
            "max_duration_seconds": round(row.max_duration_seconds, 1) if row.max_duration_seconds else None,
            "unique_devices": row.unique_devices or 0,
            "unique_users": row.unique_users or 0,
        }

    # --- write operations ---

    async def create_freeplay_attempt(self, attempt_data, device_id: uuid.UUID, user=None) -> FreeplayPuzzleAttempt:
        """create a new freeplay puzzle attempt."""
        puzzle = await self.db.scalar(select(Puzzle).where(Puzzle.id == attempt_data.puzzle_id))
        if not puzzle:
            raise HTTPException(status_code=404, detail=f"Puzzle with id {attempt_data.puzzle_id} not found")

        attempt = FreeplayPuzzleAttempt(
            puzzle_id=attempt_data.puzzle_id,
            device_id=device_id,
            user_id=user.id if user else None,
            timestamp_start=attempt_data.timestamp_start,
            timestamp_finish=attempt_data.timestamp_finish,
            action_history=attempt_data.action_history,
            board_state=attempt_data.board_state,
            is_solved=attempt_data.is_solved,
            used_tutorial=attempt_data.used_tutorial,
        )

        self.db.add(attempt)
        await self.db.commit()
        await self.db.refresh(attempt)

        # link to puzzle_shown record if one exists
        await self.link_puzzle_shown_to_attempt(
            puzzle_id=attempt_data.puzzle_id,
            device_id=device_id,
            attempt_id=attempt.id,
        )

        return attempt

    async def record_puzzle_shown(
        self,
        device_id: uuid.UUID,
        user_id: Optional[uuid.UUID],
        puzzle_id: uuid.UUID,
        session_id: Optional[uuid.UUID] = None,
    ) -> PuzzleShown:
        """record that a puzzle was shown to a user/device, capturing priority status."""
        priority_record = await self.db.scalar(
            select(PuzzlePriority).where(
                PuzzlePriority.puzzle_id == puzzle_id,
                PuzzlePriority.removed_at == None,
            )
        )

        puzzle_shown = PuzzleShown(
            device_id=device_id,
            user_id=user_id,
            session_id=session_id,
            puzzle_id=puzzle_id,
            was_priority=priority_record is not None,
        )

        self.db.add(puzzle_shown)
        await self.db.commit()
        await self.db.refresh(puzzle_shown)
        return puzzle_shown

    async def link_puzzle_shown_to_attempt(
        self,
        puzzle_id: uuid.UUID,
        device_id: uuid.UUID,
        attempt_id: uuid.UUID,
    ) -> None:
        """link a puzzle_shown record to a freeplay attempt."""
        from sqlalchemy import desc

        puzzle_shown = await self.db.scalar(
            select(PuzzleShown)
            .where(
                PuzzleShown.puzzle_id == puzzle_id,
                PuzzleShown.device_id == device_id,
                PuzzleShown.attempt_id == None,
            )
            .order_by(desc(PuzzleShown.shown_at))
            .limit(1)
        )

        if puzzle_shown:
            puzzle_shown.attempt_id = attempt_id
            await self.db.commit()

    # --- private helpers ---

    async def _smallest_size(self, puzzle_type: str) -> Optional[str]:
        """get the smallest available active puzzle size for a type."""
        sizes = (
            await self.db.execute(
                select(Puzzle.puzzle_size)
                .where(Puzzle.puzzle_type == puzzle_type, Puzzle.is_active == True)
                .distinct()
            )
        ).scalars().all()

        if not sizes:
            return None
        return min(sizes, key=lambda x: int(x.split("x")[0]))

    @staticmethod
    def _apply_nonograms_filter(query, puzzle_type: str):
        """apply minimum black cells filter for nonograms."""
        if puzzle_type != "nonograms":
            return query
        count_black_cells = cast(Puzzle.puzzle_data["count_black_cells"].as_string(), Integer)
        rows = cast(Puzzle.puzzle_data["rows"].as_string(), Integer)
        cols = cast(Puzzle.puzzle_data["cols"].as_string(), Integer)
        return query.where(count_black_cells > (rows * cols * NONOGRAMS_MIN_BLACK_CELLS_PERCENTAGE))


def _sort_key(diff_combo):
    """sort key for (size, difficulty) tuples — by grid size then difficulty order."""
    size, difficulty = diff_combo
    try:
        size_value = int(size.split("x")[0]) if "x" in size else int(size)
    except (ValueError, AttributeError):
        size_value = 0

    difficulty_order = {"easy": 1, "hard": 2}
    diff_value = difficulty_order.get(difficulty.lower(), 999) if difficulty else 999
    return (size_value, diff_value)
