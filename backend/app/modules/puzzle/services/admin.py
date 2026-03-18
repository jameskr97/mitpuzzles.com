"""admin service — priority queue management, exports, and game data summaries."""

import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List

from fastapi import HTTPException
from sqlalchemy import select, func, case, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.puzzle.models import (
    Puzzle,
    FreeplayPuzzleAttempt,
    PuzzlePriority,
    PuzzleShown,
)
from app.modules.puzzle.utils import is_research_format
from app.modules.tracking import Device
from app.modules.user_profile import UserProfile
from app.service.encoder import ResearchFormatTranslator
from app.utils import get_device_type_from_thumbmark


class PuzzleAdminService:
    """admin operations: priority queue, exports, and summaries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # --- game data summary ---

    async def get_game_data_summary(self) -> List[Dict[str, Any]]:
        """get summary of all game data grouped by puzzle type."""
        puzzle_counts_stmt = (
            select(Puzzle.puzzle_type, func.count(Puzzle.id).label("total_puzzles"))
            .group_by(Puzzle.puzzle_type)
            .order_by(Puzzle.puzzle_type)
        )

        attempt_counts_stmt = (
            select(
                Puzzle.puzzle_type,
                func.count(FreeplayPuzzleAttempt.id).label("total_attempts"),
                func.sum(case((FreeplayPuzzleAttempt.user_id.is_not(None), 1), else_=0)).label("authenticated_attempts"),
                func.sum(case((FreeplayPuzzleAttempt.user_id.is_(None), 1), else_=0)).label("anonymous_attempts"),
                func.sum(case((FreeplayPuzzleAttempt.is_solved == True, 1), else_=0)).label("solved_attempts"),
            )
            .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
            .group_by(Puzzle.puzzle_type)
            .order_by(Puzzle.puzzle_type)
        )

        puzzle_counts = {
            row.puzzle_type: row.total_puzzles
            for row in (await self.db.execute(puzzle_counts_stmt)).all()
        }
        attempt_counts = {
            row.puzzle_type: {
                "total_attempts": row.total_attempts,
                "authenticated_attempts": row.authenticated_attempts or 0,
                "anonymous_attempts": row.anonymous_attempts or 0,
                "solved_attempts": row.solved_attempts or 0,
            }
            for row in (await self.db.execute(attempt_counts_stmt)).all()
        }

        all_types = sorted(set(puzzle_counts.keys()) | set(attempt_counts.keys()))
        empty_attempts = {"total_attempts": 0, "authenticated_attempts": 0, "anonymous_attempts": 0, "solved_attempts": 0}

        return [
            {
                "puzzle_type": pt,
                "total_puzzles": puzzle_counts.get(pt, 0),
                **attempt_counts.get(pt, empty_attempts),
            }
            for pt in all_types
        ]

    # --- priority queue ---

    async def get_priority_puzzles(
        self,
        include_inactive: bool = False,
        puzzle_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """get list of priority puzzles with their statistics."""
        query = (
            select(PuzzlePriority)
            .options(selectinload(PuzzlePriority.puzzle))
            .join(Puzzle, PuzzlePriority.puzzle_id == Puzzle.id)
        )

        if not include_inactive:
            query = query.where(PuzzlePriority.removed_at == None)
        if puzzle_type:
            query = query.where(Puzzle.puzzle_type == puzzle_type)

        # total count
        count_query = select(func.count(PuzzlePriority.id)).join(Puzzle, PuzzlePriority.puzzle_id == Puzzle.id)
        if not include_inactive:
            count_query = count_query.where(PuzzlePriority.removed_at == None)
        if puzzle_type:
            count_query = count_query.where(Puzzle.puzzle_type == puzzle_type)
        total_count = await self.db.scalar(count_query)

        query = query.order_by(PuzzlePriority.added_at.desc()).limit(limit).offset(offset)
        priority_records = (await self.db.execute(query)).scalars().all()

        # batch fetch shown/solved counts
        puzzle_ids = [p.puzzle_id for p in priority_records]
        shown_counts = await self._batch_shown_counts(puzzle_ids)
        solved_counts = await self._batch_solved_counts(puzzle_ids)

        priorities_data = []
        for priority in priority_records:
            puzzle = priority.puzzle
            priorities_data.append({
                "id": priority.id,
                "puzzle_id": puzzle.id,
                "puzzle_type": puzzle.puzzle_type,
                "puzzle_size": puzzle.puzzle_size,
                "puzzle_difficulty": puzzle.puzzle_difficulty,
                "added_at": priority.added_at,
                "is_active": priority.is_active,
                "times_shown": shown_counts.get(puzzle.id, 0),
                "times_solved": solved_counts.get(puzzle.id, 0),
            })

        return {"priorities": priorities_data, "total_count": total_count}

    async def get_priority_puzzles_grouped(
        self,
        include_inactive: bool = False,
    ) -> Dict[str, Any]:
        """get priority puzzles grouped by type/size/difficulty with statistics."""
        query = (
            select(PuzzlePriority)
            .options(selectinload(PuzzlePriority.puzzle))
            .join(Puzzle, PuzzlePriority.puzzle_id == Puzzle.id)
        )

        if not include_inactive:
            query = query.where(PuzzlePriority.removed_at == None)

        query = query.order_by(
            Puzzle.puzzle_type, Puzzle.puzzle_size, Puzzle.puzzle_difficulty, PuzzlePriority.added_at.desc()
        )

        priority_records = (await self.db.execute(query)).scalars().all()

        # batch fetch all counts upfront
        all_puzzle_ids = [p.puzzle_id for p in priority_records]
        shown_counts = await self._batch_shown_counts(all_puzzle_ids)
        solved_counts = await self._batch_solved_counts(all_puzzle_ids)

        # group by type/size/difficulty
        groups: Dict[tuple, list] = defaultdict(list)
        for priority in priority_records:
            puzzle = priority.puzzle
            key = (puzzle.puzzle_type, puzzle.puzzle_size, puzzle.puzzle_difficulty)
            groups[key].append(priority)

        groups_data = []
        total_puzzles = 0

        for (pt, ps, pd), priorities in groups.items():
            group_shown = 0
            group_solved = 0
            puzzles_data = []

            for priority in priorities:
                pid = priority.puzzle.id
                ts = shown_counts.get(pid, 0)
                tsv = solved_counts.get(pid, 0)
                group_shown += ts
                group_solved += tsv

                puzzles_data.append({
                    "id": priority.id,
                    "puzzle_id": pid,
                    "added_at": priority.added_at,
                    "is_active": priority.is_active,
                    "times_shown": ts,
                    "times_solved": tsv,
                })

            groups_data.append({
                "puzzle_type": pt,
                "puzzle_size": ps,
                "puzzle_difficulty": pd,
                "total_puzzles": len(priorities),
                "total_shown": group_shown,
                "total_solved": group_solved,
                "puzzles": puzzles_data,
            })
            total_puzzles += len(priorities)

        return {
            "groups": groups_data,
            "total_groups": len(groups_data),
            "total_puzzles": total_puzzles,
        }

    async def add_priority_puzzle(self, puzzle_id: uuid.UUID) -> PuzzlePriority:
        """add a puzzle to the priority queue."""
        puzzle = await self.db.scalar(select(Puzzle).where(Puzzle.id == puzzle_id))
        if not puzzle:
            raise HTTPException(status_code=404, detail=f"Puzzle with id {puzzle_id} not found")

        existing = await self.db.scalar(
            select(PuzzlePriority).where(
                PuzzlePriority.puzzle_id == puzzle_id,
                PuzzlePriority.removed_at == None,
            )
        )
        if existing:
            raise HTTPException(status_code=400, detail="Puzzle is already in the priority queue")

        priority = PuzzlePriority(puzzle_id=puzzle_id, added_at=datetime.now(timezone.utc))
        self.db.add(priority)
        await self.db.commit()
        await self.db.refresh(priority)
        return priority

    async def remove_priority_puzzle(self, priority_id: uuid.UUID) -> PuzzlePriority:
        """remove a puzzle from the priority queue by marking it as removed."""
        priority = await self.db.scalar(
            select(PuzzlePriority).where(PuzzlePriority.id == priority_id)
        )
        if not priority:
            raise HTTPException(status_code=404, detail=f"Priority record with id {priority_id} not found")
        if priority.removed_at is not None:
            raise HTTPException(status_code=400, detail="Priority record is already removed")

        priority.removed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(priority)
        return priority

    async def get_priority_puzzle_definition(self, priority_id: uuid.UUID) -> Optional[Puzzle]:
        """get the puzzle associated with a priority record."""
        query = (
            select(PuzzlePriority)
            .options(selectinload(PuzzlePriority.puzzle))
            .where(PuzzlePriority.id == priority_id)
        )
        priority = await self.db.scalar(query)
        if not priority:
            return None
        return priority.puzzle

    # --- exports ---

    async def export_game_data(self, puzzle_type: str, user_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """export game data for a puzzle type as a list of attempt dicts."""
        stmt = (
            select(FreeplayPuzzleAttempt)
            .options(
                selectinload(FreeplayPuzzleAttempt.puzzle),
                selectinload(FreeplayPuzzleAttempt.user),
                selectinload(FreeplayPuzzleAttempt.device).selectinload(Device.thumbmarks),
            )
            .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
            .where(Puzzle.puzzle_type == puzzle_type)
        )

        if user_type == "authenticated":
            stmt = stmt.where(FreeplayPuzzleAttempt.user_id.is_not(None))
        elif user_type == "anonymous":
            stmt = stmt.where(FreeplayPuzzleAttempt.user_id.is_(None))

        stmt = stmt.order_by(FreeplayPuzzleAttempt.created_at.desc())

        result = await self.db.execute(stmt)
        attempts = result.scalars().all()

        if not attempts:
            raise HTTPException(status_code=404, detail=f"no attempts found for puzzle type {puzzle_type}")

        return [_format_attempt_for_export(a) for a in attempts]

    async def export_freeplay_data(
        self,
        puzzle_types: Optional[List[str]] = None,
        puzzle_sizes: Optional[List[str]] = None,
        puzzle_difficulties: Optional[List[str]] = None,
        user_type: Optional[str] = None,
        filter_user_id: Optional[uuid.UUID] = None,
        filter_device_id: Optional[uuid.UUID] = None,
        solved_filter: Optional[str] = None,
        date_start: Optional[str] = None,
        date_end: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """export freeplay data with flexible filtering."""
        stmt = (
            select(FreeplayPuzzleAttempt)
            .options(
                selectinload(FreeplayPuzzleAttempt.puzzle),
                selectinload(FreeplayPuzzleAttempt.user),
                selectinload(FreeplayPuzzleAttempt.device).selectinload(Device.thumbmarks),
            )
            .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
        )

        if puzzle_types:
            stmt = stmt.where(Puzzle.puzzle_type.in_(puzzle_types))
        if puzzle_sizes:
            stmt = stmt.where(Puzzle.puzzle_size.in_(puzzle_sizes))
        if puzzle_difficulties:
            stmt = stmt.where(Puzzle.puzzle_difficulty.in_(puzzle_difficulties))
        if filter_user_id:
            stmt = stmt.where(FreeplayPuzzleAttempt.user_id == filter_user_id)
        if filter_device_id:
            stmt = stmt.where(FreeplayPuzzleAttempt.device_id == filter_device_id)
        if solved_filter == "solved":
            stmt = stmt.where(FreeplayPuzzleAttempt.is_solved == True)
        elif solved_filter == "unsolved":
            stmt = stmt.where(FreeplayPuzzleAttempt.is_solved == False)
        if user_type == "authenticated":
            stmt = stmt.where(FreeplayPuzzleAttempt.user_id.is_not(None))
        elif user_type == "anonymous":
            stmt = stmt.where(FreeplayPuzzleAttempt.user_id.is_(None))
        if date_start:
            stmt = stmt.where(FreeplayPuzzleAttempt.created_at >= datetime.strptime(date_start, "%Y-%m-%d"))
        if date_end:
            stmt = stmt.where(FreeplayPuzzleAttempt.created_at < datetime.strptime(date_end, "%Y-%m-%d") + timedelta(days=1))

        stmt = stmt.order_by(FreeplayPuzzleAttempt.created_at.desc())

        result = await self.db.execute(stmt)
        attempts = result.scalars().all()

        if not attempts:
            raise HTTPException(status_code=404, detail="No attempts found matching the specified filters")

        # batch fetch user profiles
        user_ids = [a.user_id for a in attempts if a.user_id]
        user_profiles = {}
        if user_ids:
            profile_result = await self.db.execute(
                select(UserProfile).where(UserProfile.user_id.in_(user_ids))
            )
            user_profiles = {p.user_id: p for p in profile_result.scalars().all()}

        return [_format_attempt_for_export(a, user_profiles) for a in attempts]

    # --- private helpers ---

    async def _batch_shown_counts(self, puzzle_ids: List[uuid.UUID]) -> Dict[uuid.UUID, int]:
        """batch fetch priority-shown counts for a list of puzzle ids."""
        if not puzzle_ids:
            return {}
        result = await self.db.execute(
            select(PuzzleShown.puzzle_id, func.count(PuzzleShown.id))
            .where(PuzzleShown.puzzle_id.in_(puzzle_ids), PuzzleShown.was_priority == True)
            .group_by(PuzzleShown.puzzle_id)
        )
        return dict(result.all())

    async def _batch_solved_counts(self, puzzle_ids: List[uuid.UUID]) -> Dict[uuid.UUID, int]:
        """batch fetch solved counts for a list of puzzle ids."""
        if not puzzle_ids:
            return {}
        result = await self.db.execute(
            select(FreeplayPuzzleAttempt.puzzle_id, func.count(FreeplayPuzzleAttempt.id))
            .where(FreeplayPuzzleAttempt.puzzle_id.in_(puzzle_ids), FreeplayPuzzleAttempt.is_solved == True)
            .group_by(FreeplayPuzzleAttempt.puzzle_id)
        )
        return dict(result.all())


# --- export formatting ---


def _translate_attempt_data(puzzle_type: str, board_state, action_history):
    """translate board state and action history to research format if needed."""
    if is_research_format(board_state, action_history):
        return board_state, action_history

    try:
        translator = ResearchFormatTranslator(puzzle_type)
        translated_board = translator.translate_grid(board_state) if board_state else board_state
        translated_history = translator.translate_action_history(action_history) if action_history else action_history
        return translated_board, translated_history
    except ValueError:
        return board_state, action_history


def _format_attempt_for_export(attempt, user_profiles: Optional[Dict] = None) -> Dict[str, Any]:
    """format a single attempt for export."""
    puzzle_type = attempt.puzzle.puzzle_type
    translated_board, translated_history = _translate_attempt_data(
        puzzle_type, attempt.board_state, attempt.action_history
    )

    data = {
        "id": str(attempt.id),
        "created_at": attempt.created_at.isoformat(),
        "timestamp_start": attempt.timestamp_start,
        "timestamp_finish": attempt.timestamp_finish,
        "action_history": translated_history,
        "board_state": translated_board,
        "used_tutorial": attempt.used_tutorial,
        "is_solved": attempt.is_solved,
        "device_id": str(attempt.device_id) if attempt.device_id else None,
        "puzzle": {
            "id": str(attempt.puzzle.id),
            **attempt.puzzle.puzzle_data,
        },
    }

    if attempt.user:
        user_data = {
            "id": str(attempt.user.id),
            "username": attempt.user.username,
            "email": attempt.user.email,
        }
        if user_profiles and attempt.user_id in user_profiles:
            profile = user_profiles[attempt.user_id]
            user_data["profile"] = {
                "age": profile.age,
                "gender": profile.gender,
                "education_level": profile.education_level,
                "game_experience": profile.game_experience,
            }
        data["user"] = user_data

    if attempt.device and attempt.device.thumbmarks:
        latest_thumbmark = attempt.device.thumbmarks[-1]
        data["device_type"] = get_device_type_from_thumbmark(latest_thumbmark.thumbmark_data)
    else:
        data["device_type"] = "desktop"

    return data
