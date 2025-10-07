"""
Puzzles module for managing puzzle data and tracking puzzle attempts.
Stores pre-generated puzzles and tracks user/device attempts at solving them.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException, Query, Request, Response, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import String, DateTime, Index, UUID, ForeignKey, Boolean, BigInteger, text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, declared_attr, relationship
from sqlalchemy.sql.functions import count
from sqlalchemy.types import JSON

from app.dependencies import AsyncDatabase, get_device_id
from app.models import Base
from app.modules.authentication import User, fastapi_users
from app.service.encoder import PrecisePuzzleEncoder
from app.modules.device_tracking import Device
from app.utils import get_device_type_from_thumbmark


# Models
class Puzzle(Base):
    """
    Stores pre-generated puzzles of all types.
    Puzzles are created offline and loaded into the database.
    """

    __tablename__ = "puzzle"
    __table_args__ = (
        Index("idx_puzzle_type", "puzzle_type"),
        Index("idx_puzzle_difficulty", "puzzle_difficulty"),
        Index("idx_puzzle_type_size_difficulty", "puzzle_type", "puzzle_size", "puzzle_difficulty"),
    )

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, server_default=text("uuidv7()"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # semantic ids
    complete_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    definition_id: Mapped[str] = mapped_column(String(36), nullable=False)
    solution_id: Mapped[str] = mapped_column(String(36), nullable=False)

    # puzzle metadata + normalizied data
    puzzle_type: Mapped[str] = mapped_column(String(32), nullable=False)  # minesweeper, sudoku, tents, battleship...
    puzzle_size: Mapped[str] = mapped_column(String(32), nullable=False)  # 5x5, 9x9, 10x10...
    puzzle_difficulty: Mapped[str] = mapped_column(String(32), nullable=True)  # easy, medium, hard...
    puzzle_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)  # JSON Field for puzzle data

    def __repr__(self):
        return f"<Puzzle(id={self.id}, type={self.puzzle_type}, difficulty={self.puzzle_difficulty})>"


class FreeplayPuzzleAttempt(Base):
    """
    Records each attempt a user makes at solving a puzzle in freeplay mode.
    This is used for puzzles that do not have a specific completion condition.
    """

    __tablename__ = "freeplay_puzzle_attempt"
    __table_args__ = (
        Index("idx_freeplay_device_puzzle", "device_id", "puzzle_id"),
        Index("idx_freeplay_is_solved", "is_solved"),
    )  # Primary key and timestamps
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuidv7()"))
    created_at: Mapped[DateTime] = mapped_column(DateTime(), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # identifiers
    device_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("device.id", ondelete="CASCADE"), nullable=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True)

    # puzzle reference
    puzzle_id: Mapped[uuid.UUID] = mapped_column(UUID(), ForeignKey("puzzle.id", ondelete="RESTRICT"), nullable=True)

    # attempt specific
    timestamp_start: Mapped[int] = mapped_column(BigInteger, nullable=False)
    timestamp_finish: Mapped[int] = mapped_column(BigInteger, nullable=True)
    action_history: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    board_state: Mapped[List[Any]] = mapped_column(JSON, default=list, nullable=False)
    used_tutorial: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_solved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Use declared_attr for relationships that need table name
    @declared_attr
    def device(cls) -> Mapped["Device"]:
        return relationship("Device", backref=f"{cls.__tablename__}_attempts")

    @declared_attr
    def user(cls) -> Mapped[Optional["User"]]:
        return relationship("User", backref=f"{cls.__tablename__}_attempts")

    @declared_attr
    def puzzle(cls) -> Mapped["Puzzle"]:
        return relationship("Puzzle", backref=f"{cls.__tablename__}_attempts")

    @hybrid_property
    def is_authenticated(self) -> bool:
        """Returns True if attempt is from an authenticated user."""
        return self.user_id is not None


# Schemas
class PuzzleDefinitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    puzzle_type: str
    rows: int
    cols: int
    initial_state: List[List[int]]
    solution_hash: str
    meta: Dict[str, Any]


class PuzzleDefinitionSolution(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    puzzle_type: str
    rows: int
    cols: int
    initial_state: List[List[int]]
    solution: List[List[int]]
    solution_hash: str
    meta: Dict[str, Any]


class FreeplayAttemptCreate(BaseModel):
    """Schema for creating freeplay puzzle attempts"""

    puzzle_id: uuid.UUID = Field(..., description="ID of the associated puzzle")
    timestamp_start: int = Field(description="Start time of the attempt")
    timestamp_finish: int = Field(default=None, description="Finish time of the attempt")
    action_history: List[Dict[str, Any]] = Field(default_factory=list, description="History of user actions")
    board_state: List[List[int]] = Field(default_factory=list, description="Final board state")
    is_solved: bool = Field(default=False, description="Whether the puzzle was solved")
    used_tutorial: bool = Field(default=False, description="Whether tutorial was used")


class PuzzleResponse(BaseModel):
    """Schema for puzzle responses"""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    puzzle_hash: str
    puzzle_type: str
    puzzle_size: str
    puzzle_difficulty: str
    puzzle_data: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class LeaderboardEntryResponse(BaseModel):
    """Schema for leaderboard entry responses"""

    rank: int
    duration_display: str
    username: str

    model_config = ConfigDict(from_attributes=True)


class LeaderboardResponse(BaseModel):
    """Schema for leaderboard responses"""

    leaderboard: List[LeaderboardEntryResponse]
    count: int

    model_config = ConfigDict(from_attributes=True)


class PuzzleIdResponse(BaseModel):
    """Schema for puzzle ID only responses"""

    puzzle_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


# Service
class PuzzleService:
    """Service for managing puzzle operations"""

    def __init__(self, db: AsyncDatabase):
        self.db = db

    def _sort_key(self, diff_combo):
        size, difficulty = diff_combo
        # Extract first number from size (e.g., 9 from "9x9")
        try:
            size_value = int(size.split("x")[0]) if "x" in size else int(size)
        except (ValueError, AttributeError):
            size_value = 0  # Fallback for unexpected formats

        # Map difficulty to numeric value for sorting
        difficulty_order = {"easy": 1, "hard": 2}
        diff_value = difficulty_order.get(difficulty.lower(), 999) if difficulty else 999
        return (size_value, diff_value)

    async def get_types(self):
        from sqlalchemy import select

        types_config = {}

        # Get distinct puzzle types from database
        puzzle_types = (await self.db.scalars(select(Puzzle.puzzle_type).distinct())).all()
        for puzzle_type in puzzle_types:
            # query + sort difficulties
            query = (
                select(Puzzle.puzzle_size, Puzzle.puzzle_difficulty)
                .distinct(Puzzle.puzzle_size, Puzzle.puzzle_difficulty)
                .where(Puzzle.puzzle_type == puzzle_type)
                .order_by(Puzzle.puzzle_size)
            )
            difficulty_combinations_rows = (await self.db.execute(query)).all()
            difficulty_combinations = [tuple(row) for row in difficulty_combinations_rows]
            difficulty_combinations.sort(key=self._sort_key)

            # query for number of puzzles
            num_puzzles = await self.db.scalar(select(count(Puzzle.id)).where(Puzzle.puzzle_type == puzzle_type))
            types_config[puzzle_type] = {
                "available_difficulties": difficulty_combinations,
                "default_difficulty": difficulty_combinations[0],
                "total_puzzles": num_puzzles,
            }
        return types_config

    async def get_puzzle_by_id(self, puzzle_id: uuid.UUID):
        from sqlalchemy import select

        return await self.db.scalar(select(Puzzle).where(Puzzle.id == puzzle_id))

    async def get_random_puzzle(self, puzzle_type: str, puzzle_size: Optional[str] = None, puzzle_difficulty: Optional[str] = None) -> Optional[Puzzle]:
        """
        Get a random puzzle of the specified type, size, and difficulty.
        If size is not specified, uses the smallest available size for that type.
        """
        from sqlalchemy import select, func

        # Start with base query
        query = select(Puzzle).where(Puzzle.puzzle_type == puzzle_type)

        # Handle size selection
        if puzzle_size:
            query = query.where(Puzzle.puzzle_size == puzzle_size)
        else:
            # Get all available sizes for this puzzle type
            size_query = select(Puzzle.puzzle_size).where(Puzzle.puzzle_type == puzzle_type).distinct()
            sizes_result = await self.db.execute(size_query)
            all_sizes = sizes_result.scalars().all()

            if all_sizes:
                # Parse sizes like "5x5" and get the smallest one based on first number
                smallest_size = min(all_sizes, key=lambda x: int(x.split("x")[0]))
                query = query.where(Puzzle.puzzle_size == smallest_size)

        # Add difficulty filter if specified
        if puzzle_difficulty:
            query = query.where(Puzzle.puzzle_difficulty == puzzle_difficulty)

        # Order by random
        query = query.order_by(func.random())
        return await self.db.scalar(query)

    def calculate_puzzle_solution_hash_rle(self, puzzle_type, solution_state):
        ppe = PrecisePuzzleEncoder(puzzle_type)
        return ppe.create_run_length_encoding(solution_state)

    def format_puzzle_for_frontend(self, puzzle: Puzzle) -> Dict[str, Any]:
        """Transform database puzzle format to frontend format"""
        puzzle_data = puzzle.puzzle_data

        # Extract meta by removing fields that go to top level
        meta = puzzle_data.copy()
        meta.pop("puzzle_type", None)
        meta.pop("puzzle_size", None)
        meta.pop("puzzle_difficulty", None)
        meta.pop("definition_id", None)
        meta.pop("solution_id", None)
        meta.pop("complete_id", None)
        meta.pop("rows", None)
        meta.pop("cols", None)
        meta.pop("initial_state", None)
        meta.pop("solution", None)
        meta.pop("difficulty_label", None)

        return {
            "id": puzzle.id,
            "puzzle_type": puzzle.puzzle_type,
            "rows": puzzle_data["rows"],
            "cols": puzzle_data["cols"],
            "initial_state": puzzle_data["initial_state"],
            "solution_hash": self.calculate_puzzle_solution_hash_rle(puzzle.puzzle_type, puzzle_data["solution"]),
            "meta": meta,
        }

    def format_puzzle_with_solution_for_admin(self, puzzle: Puzzle) -> Dict[str, Any]:
        """Transform database puzzle format to admin format with actual solution"""
        res = self.format_puzzle_for_frontend(puzzle)
        res["solution"] = puzzle.puzzle_data["solution"]
        puzzle_data = puzzle.puzzle_data
        return res


    async def create_freeplay_attempt(self, attempt_data: FreeplayAttemptCreate, device_id: uuid.UUID, user: Optional[User] = None) -> FreeplayPuzzleAttempt:
        """Create new freeplay puzzle attempt with required device tracking and optional user."""
        from sqlalchemy import select

        # Verify puzzle exists
        puzzle = await self.db.scalar(select(Puzzle).where(Puzzle.id == attempt_data.puzzle_id))
        if not puzzle:
            raise HTTPException(status_code=404, detail=f"Puzzle with id {attempt_data.puzzle_id} not found")

        # Create the attempt
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
        return attempt

    async def get_freeplay_leaderboard(self, puzzle_type: str, puzzle_size: str, puzzle_difficulty: str, limit: int = 10) -> Dict[str, Any]:
        """get leaderboard for freeplay puzzles by type, size, and difficulty. only includes authenticated users"""
        from sqlalchemy import select, func, and_

        # create subquery to get best time per user for each (type X size X difficulty)
        # timestamps are stored as milliseconds, so convert to seconds for readability
        best_times_subquery = (
            select(
                FreeplayPuzzleAttempt.user_id,
                func.min((FreeplayPuzzleAttempt.timestamp_finish - FreeplayPuzzleAttempt.timestamp_start) / 1000.0).label("best_time_seconds"),
            )
            .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
            .where(
                and_(
                    FreeplayPuzzleAttempt.is_solved == True,  # noqa: E712, == True is intentional here
                    FreeplayPuzzleAttempt.user_id.is_not(None),  # only authenticated users
                    Puzzle.puzzle_type == puzzle_type,
                    Puzzle.puzzle_size == puzzle_size,
                    Puzzle.puzzle_difficulty == puzzle_difficulty,
                    FreeplayPuzzleAttempt.timestamp_finish.is_not(None),
                    FreeplayPuzzleAttempt.timestamp_start.is_not(None),
                    FreeplayPuzzleAttempt.used_tutorial == False,
                )
            )
            .group_by(FreeplayPuzzleAttempt.user_id)
            .subquery()
        )

        # main query to get leaderboard with user info
        query = (
            select(((FreeplayPuzzleAttempt.timestamp_finish - FreeplayPuzzleAttempt.timestamp_start) / 1000.0).label("completion_time_seconds"), User.username)
            .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
            .join(User, FreeplayPuzzleAttempt.user_id == User.id)
            .join(
                best_times_subquery,
                and_(
                    FreeplayPuzzleAttempt.user_id == best_times_subquery.c.user_id,
                    ((FreeplayPuzzleAttempt.timestamp_finish - FreeplayPuzzleAttempt.timestamp_start) / 1000.0) == best_times_subquery.c.best_time_seconds,
                ),
            )
            .where(
                and_(
                    FreeplayPuzzleAttempt.is_solved == True,  # noqa: E712, == True is intentional here
                    FreeplayPuzzleAttempt.user_id.is_not(None),
                    Puzzle.puzzle_type == puzzle_type,
                    Puzzle.puzzle_size == puzzle_size,
                    Puzzle.puzzle_difficulty == puzzle_difficulty,
                )
            )
            .order_by(((FreeplayPuzzleAttempt.timestamp_finish - FreeplayPuzzleAttempt.timestamp_start) / 1000.0).asc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.all()

        # Format leaderboard entries
        leaderboard_entries = []
        for rank, row in enumerate(rows, 1):
            # format duration (time_seconds is already in seconds from database)
            time_seconds = row.completion_time_seconds
            if time_seconds >= 60:  # more than 1 minute
                minutes = int(time_seconds // 60)
                seconds = time_seconds % 60
                duration_display = f"{minutes}:{seconds:05.2f}"
            else:
                duration_display = f"{time_seconds:.2f}s"

            leaderboard_entries.append({"rank": rank, "duration_display": duration_display, "username": row.username})

        return {"leaderboard": leaderboard_entries, "count": len(leaderboard_entries)}

    async def browse_puzzles(
        self,
        puzzle_types: Optional[List[str]] = None,
        puzzle_sizes: Optional[List[str]] = None,
        puzzle_difficulties: Optional[List[str]] = None,
        has_attempts: Optional[str] = None,
        limit: int = 36,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Browse puzzles with optional filtering and pagination.
        Returns formatted puzzles for frontend display.
        """
        from sqlalchemy import select, func, exists

        # Exclude certain puzzle types from browse
        excluded_types = ['battleships', 'hashi', 'norinori']

        # Build filter conditions that will be applied to both queries
        filter_conditions = [
            ~Puzzle.puzzle_type.in_(excluded_types)  # Exclude certain puzzle types
        ]

        if puzzle_types and len(puzzle_types) > 0:
            filter_conditions.append(Puzzle.puzzle_type.in_(puzzle_types))
        if puzzle_sizes and len(puzzle_sizes) > 0:
            filter_conditions.append(Puzzle.puzzle_size.in_(puzzle_sizes))
        if puzzle_difficulties and len(puzzle_difficulties) > 0:
            filter_conditions.append(Puzzle.puzzle_difficulty.in_(puzzle_difficulties))

        # Handle attempts filter
        if has_attempts == 'with_attempts':
            # Only puzzles that have attempts
            filter_conditions.append(exists().where(FreeplayPuzzleAttempt.puzzle_id == Puzzle.id))
        elif has_attempts == 'without_attempts':
            # Only puzzles that have no attempts
            filter_conditions.append(~exists().where(FreeplayPuzzleAttempt.puzzle_id == Puzzle.id))

        # Start with base query and apply all filters
        query = select(Puzzle)
        for condition in filter_conditions:
            query = query.where(condition)

        # Get total count with exactly the same filters
        count_query = select(func.count(Puzzle.id))
        for condition in filter_conditions:
            count_query = count_query.where(condition)

        total_count = await self.db.scalar(count_query)

        # If no puzzles match the filter, return empty result
        if total_count == 0:
            return {
                "puzzles": [],
                "total_count": 0,
                "offset": offset,
                "limit": limit,
                "has_more": False
            }

        # Apply pagination and ordering
        query = query.order_by(Puzzle.puzzle_type).limit(limit).offset(offset)

        # Execute query
        result = await self.db.execute(query)
        puzzles = result.scalars().all()

        # Format puzzles for frontend
        formatted_puzzles = [self.format_puzzle_for_frontend(puzzle) for puzzle in puzzles]

        return {
            "puzzles": formatted_puzzles,
            "total_count": total_count,
            "offset": offset,
            "limit": limit,
            "has_more": offset + limit < total_count
        }

    async def get_game_data_summary(self):
        """get summary of all game data grouped by puzzle type"""
        from sqlalchemy import select, func, case

        # get puzzle counts by type
        puzzle_counts_stmt = (
            select(
                Puzzle.puzzle_type,
                func.count(Puzzle.id).label('total_puzzles')
            )
            .group_by(Puzzle.puzzle_type)
            .order_by(Puzzle.puzzle_type)
        )

        # get attempt counts by puzzle type
        attempt_counts_stmt = (
            select(
                Puzzle.puzzle_type,
                func.count(FreeplayPuzzleAttempt.id).label('total_attempts'),
                func.sum(case((FreeplayPuzzleAttempt.user_id.is_not(None), 1), else_=0)).label('authenticated_attempts'),
                func.sum(case((FreeplayPuzzleAttempt.user_id.is_(None), 1), else_=0)).label('anonymous_attempts'),
                func.sum(case((FreeplayPuzzleAttempt.is_solved == True, 1), else_=0)).label('solved_attempts')
            )
            .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
            .group_by(Puzzle.puzzle_type)
            .order_by(Puzzle.puzzle_type)
        )

        puzzle_counts_result = await self.db.execute(puzzle_counts_stmt)
        puzzle_counts = {row.puzzle_type: row.total_puzzles for row in puzzle_counts_result.all()}

        attempt_counts_result = await self.db.execute(attempt_counts_stmt)
        attempt_counts = {row.puzzle_type: {
            'total_attempts': row.total_attempts,
            'authenticated_attempts': row.authenticated_attempts or 0,
            'anonymous_attempts': row.anonymous_attempts or 0,
            'solved_attempts': row.solved_attempts or 0
        } for row in attempt_counts_result.all()}

        # combine data
        summary_data = []
        all_types = set(puzzle_counts.keys()) | set(attempt_counts.keys())

        for puzzle_type in sorted(all_types):
            puzzle_count = puzzle_counts.get(puzzle_type, 0)
            attempt_data = attempt_counts.get(puzzle_type, {
                'total_attempts': 0,
                'authenticated_attempts': 0,
                'anonymous_attempts': 0,
                'solved_attempts': 0
            })

            summary_data.append({
                'puzzle_type': puzzle_type,
                'total_puzzles': puzzle_count,
                'total_attempts': attempt_data['total_attempts'],
                'authenticated_attempts': attempt_data['authenticated_attempts'],
                'anonymous_attempts': attempt_data['anonymous_attempts'],
                'solved_attempts': attempt_data['solved_attempts']
            })

        return summary_data

    async def export_game_data(self, puzzle_type: str, user_type: Optional[str] = None):
        """export game data as json"""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        # export freeplay attempts
        stmt = (
            select(FreeplayPuzzleAttempt)
            .options(
                selectinload(FreeplayPuzzleAttempt.puzzle),
                selectinload(FreeplayPuzzleAttempt.user),
                selectinload(FreeplayPuzzleAttempt.device).selectinload(Device.thumbmarks)
            )
            .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
            .where(Puzzle.puzzle_type == puzzle_type)
        )

        # filter by user type if specified
        if user_type == 'authenticated':
            stmt = stmt.where(FreeplayPuzzleAttempt.user_id.is_not(None))
        elif user_type == 'anonymous':
            stmt = stmt.where(FreeplayPuzzleAttempt.user_id.is_(None))

        stmt = stmt.order_by(FreeplayPuzzleAttempt.created_at.desc())

        result = await self.db.execute(stmt)
        attempts = result.scalars().all()

        if not attempts:
            raise HTTPException(status_code=404, detail=f"no attempts found for puzzle type {puzzle_type}")

        export_data = []
        for attempt in attempts:
            attempt_data = {
                'id': str(attempt.id),
                'created_at': attempt.created_at.isoformat(),
                'timestamp_start': attempt.timestamp_start,
                'timestamp_finish': attempt.timestamp_finish,
                'action_history': attempt.action_history,
                'board_state': attempt.board_state,
                'used_tutorial': attempt.used_tutorial,
                'is_solved': attempt.is_solved,
                'device_id': str(attempt.device_id) if attempt.device_id else None,
                'user_id': str(attempt.user_id) if attempt.user_id else None,
                'puzzle': {
                    'id': str(attempt.puzzle.id),
                    'puzzle_type': attempt.puzzle.puzzle_type,
                    'puzzle_size': attempt.puzzle.puzzle_size,
                    'puzzle_difficulty': attempt.puzzle.puzzle_difficulty,
                    'complete_id': attempt.puzzle.complete_id
                }
            }

            # add user info if available
            if attempt.user:
                attempt_data['user'] = {
                    'id': str(attempt.user.id),
                    'username': attempt.user.username,
                    'email': attempt.user.email
                }

            # add device type from latest thumbmark
            if attempt.device and attempt.device.thumbmarks:
                # get the most recent thumbmark
                latest_thumbmark = attempt.device.thumbmarks[-1]
                device_type = get_device_type_from_thumbmark(latest_thumbmark.thumbmark_data)
                attempt_data['device_type'] = device_type
            else:
                attempt_data['device_type'] = 'desktop'  # fallback

            export_data.append(attempt_data)

        return export_data

    async def get_dynamic_filter_options(
        self,
        puzzle_types: Optional[List[str]] = None,
        puzzle_sizes: Optional[List[str]] = None,
        puzzle_difficulties: Optional[List[str]] = None,
        has_attempts: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get available filter options with counts based on current selections.
        Returns what filter values are possible given the current filter state.
        """
        from sqlalchemy import select, func, distinct, exists

        # Exclude certain puzzle types from browse
        excluded_types = ['battleships', 'hashi', 'norinori']

        # Build base filter conditions (everything except the dimension we're calculating)
        def get_base_conditions(exclude_dimension: str):
            conditions = [
                ~Puzzle.puzzle_type.in_(excluded_types)  # Always exclude certain puzzle types
            ]

            if exclude_dimension != 'puzzle_type' and puzzle_types and len(puzzle_types) > 0:
                conditions.append(Puzzle.puzzle_type.in_(puzzle_types))
            if exclude_dimension != 'puzzle_size' and puzzle_sizes and len(puzzle_sizes) > 0:
                conditions.append(Puzzle.puzzle_size.in_(puzzle_sizes))
            if exclude_dimension != 'puzzle_difficulty' and puzzle_difficulties and len(puzzle_difficulties) > 0:
                conditions.append(Puzzle.puzzle_difficulty.in_(puzzle_difficulties))

            # Handle attempts filter
            if exclude_dimension != 'has_attempts' and has_attempts:
                if has_attempts == 'with_attempts':
                    conditions.append(exists().where(FreeplayPuzzleAttempt.puzzle_id == Puzzle.id))
                elif has_attempts == 'without_attempts':
                    conditions.append(~exists().where(FreeplayPuzzleAttempt.puzzle_id == Puzzle.id))

            return conditions

        # Get ALL puzzle types with their counts (including 0), excluding certain types
        all_types_query = select(Puzzle.puzzle_type).distinct().where(~Puzzle.puzzle_type.in_(excluded_types))
        all_types_result = await self.db.execute(all_types_query)
        all_types = [row.puzzle_type for row in all_types_result.all()]

        # Get counts for each type with current filters
        available_types = []
        for puzzle_type in all_types:
            count_query = select(func.count(Puzzle.id)).where(Puzzle.puzzle_type == puzzle_type)
            for condition in get_base_conditions('puzzle_type'):
                count_query = count_query.where(condition)
            count = await self.db.scalar(count_query)
            available_types.append({"value": puzzle_type, "count": count})

        # Get ALL puzzle sizes with their counts (including 0), excluding certain types
        all_sizes_query = select(Puzzle.puzzle_size).distinct().where(~Puzzle.puzzle_type.in_(excluded_types))
        all_sizes_result = await self.db.execute(all_sizes_query)
        all_sizes = [row.puzzle_size for row in all_sizes_result.all()]

        # Get counts for each size with current filters
        available_sizes = []
        for puzzle_size in all_sizes:
            count_query = select(func.count(Puzzle.id)).where(Puzzle.puzzle_size == puzzle_size)
            for condition in get_base_conditions('puzzle_size'):
                count_query = count_query.where(condition)
            count = await self.db.scalar(count_query)
            available_sizes.append({"value": puzzle_size, "count": count})

        # Get ALL puzzle difficulties with their counts (including 0), excluding certain types
        all_difficulties_query = select(Puzzle.puzzle_difficulty).distinct().where(
            Puzzle.puzzle_difficulty.is_not(None) & ~Puzzle.puzzle_type.in_(excluded_types)
        )
        all_difficulties_result = await self.db.execute(all_difficulties_query)
        all_difficulties = [row.puzzle_difficulty for row in all_difficulties_result.all()]

        # Get counts for each difficulty with current filters
        available_difficulties = []
        for puzzle_difficulty in all_difficulties:
            count_query = select(func.count(Puzzle.id)).where(Puzzle.puzzle_difficulty == puzzle_difficulty)
            for condition in get_base_conditions('puzzle_difficulty'):
                count_query = count_query.where(condition)
            count = await self.db.scalar(count_query)
            available_difficulties.append({"value": puzzle_difficulty, "count": count})

        # Get attempts filter counts
        base_conditions = get_base_conditions('has_attempts')

        # Total count
        total_query = select(func.count(Puzzle.id))
        for condition in base_conditions:
            total_query = total_query.where(condition)
        total_count = await self.db.scalar(total_query)

        # With attempts count
        with_attempts_query = select(func.count(Puzzle.id)).where(
            exists().where(FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
        )
        for condition in base_conditions:
            with_attempts_query = with_attempts_query.where(condition)
        with_attempts_count = await self.db.scalar(with_attempts_query)

        # Without attempts count
        without_attempts_count = total_count - with_attempts_count

        attempts_options = [
            {"value": "all", "count": total_count},
            {"value": "with_attempts", "count": with_attempts_count},
            {"value": "without_attempts", "count": without_attempts_count}
        ]

        return {
            "puzzle_types": available_types,
            "puzzle_sizes": available_sizes,
            "puzzle_difficulties": available_difficulties,
            "attempts_options": attempts_options
        }


# routes
router = APIRouter(prefix="/api/puzzle", tags=["Puzzles"])


@router.get("/definition/random", response_model=PuzzleIdResponse)
async def get_random_puzzle(
    db: AsyncDatabase,
    puzzle_type: str = Query(..., description="Type of puzzle"),
    puzzle_size: Optional[str] = Query(None, description="Size of puzzle"),
    puzzle_difficulty: Optional[str] = Query(None, description="Difficulty level"),
) -> Optional[PuzzleIdResponse]:
    """
    Get a random puzzle ID matching the specified criteria.

    - If size is not specified, returns the smallest available size
    - Returns 404 if no matching puzzle is found
    - Returns only the puzzle ID - use /api/puzzle/definition/{puzzle_id} to get full definition

    Example: GET /api/puzzles/random?puzzle_type=sudoku&puzzle_difficulty=easy
    """
    service = PuzzleService(db)
    puzzle = await service.get_random_puzzle(puzzle_type=puzzle_type, puzzle_size=puzzle_size, puzzle_difficulty=puzzle_difficulty)

    if not puzzle:
        raise HTTPException(status_code=404, detail=f"No puzzle found for type='{puzzle_type}', size='{puzzle_size}', difficulty='{puzzle_difficulty}'")

    return PuzzleIdResponse(puzzle_id=puzzle.id)


@router.get("/definition/types", description="Get puzzle type metadata")
async def get_types(db: AsyncDatabase, response: Response, request: Request):
    puzzle = PuzzleService(db)
    return await puzzle.get_types()


@router.get("/filter-options")
async def get_filter_options(
    db: AsyncDatabase,
    puzzle_type: Optional[List[str]] = Query(default=None, description="Current puzzle type selections"),
    puzzle_size: Optional[List[str]] = Query(default=None, description="Current puzzle size selections"),
    puzzle_difficulty: Optional[List[str]] = Query(default=None, description="Current difficulty selections"),
    has_attempts: Optional[str] = Query(default=None, description="Current attempts filter"),
):
    """
    Get available filter options with counts based on current filter selections.

    Returns dynamic filter options showing:
    - Available values for each filter dimension
    - Count of puzzles for each option
    - Only shows combinations that actually exist in the database

    Example: GET /api/puzzle/filter-options?puzzle_type=sudoku
    """
    service = PuzzleService(db)
    return await service.get_dynamic_filter_options(
        puzzle_types=puzzle_type,
        puzzle_sizes=puzzle_size,
        puzzle_difficulties=puzzle_difficulty,
        has_attempts=has_attempts
    )


@router.get("/browse")
async def browse_puzzles(
    db: AsyncDatabase,
    puzzle_type: Optional[List[str]] = Query(default=None, description="Filter by puzzle types (can specify multiple)"),
    puzzle_size: Optional[List[str]] = Query(default=None, description="Filter by puzzle sizes (can specify multiple)"),
    puzzle_difficulty: Optional[List[str]] = Query(default=None, description="Filter by difficulty levels (can specify multiple)"),
    has_attempts: Optional[str] = Query(default=None, description="Filter by attempt status: 'with_attempts', 'without_attempts', or null for all"),
    limit: int = Query(64, description="Number of puzzles to return", ge=1, le=100),
    offset: int = Query(0, description="Number of puzzles to skip", ge=0),
):
    """
    Browse puzzles with optional filtering and pagination.

    Returns a paginated list of puzzles that can be filtered by:
    - puzzle_type: minesweeper, sudoku, tents, etc. (can specify multiple)
    - puzzle_size: 5x5, 9x9, etc. (can specify multiple)
    - puzzle_difficulty: easy, medium, hard (can specify multiple)

    Examples:
    - GET /api/puzzle/browse?puzzle_type=sudoku&puzzle_type=minesweeper&limit=12
    - GET /api/puzzle/browse?puzzle_size=9x9&puzzle_size=5x5&puzzle_difficulty=easy&puzzle_difficulty=hard
    """
    service = PuzzleService(db)
    return await service.browse_puzzles(
        puzzle_types=puzzle_type,
        puzzle_sizes=puzzle_size,
        puzzle_difficulties=puzzle_difficulty,
        has_attempts=has_attempts,
        limit=limit,
        offset=offset
    )


@router.get("/definition/{puzzle_id}")
async def get_puzzle(
    db: AsyncDatabase,
    puzzle_id: uuid.UUID,
    include_solution: bool = Query(False, description="Include actual solution (admin only)"),
    user: Optional[User] = Depends(fastapi_users.current_user(optional=True)),
):
    """
    Get puzzle definition.

    - By default returns puzzle with solution_hash only
    - Admins can use ?include_solution=true to get actual solution_state
    - Non-admins requesting include_solution=true will get 403 Forbidden
    """
    service = PuzzleService(db)
    puzzle = await service.get_puzzle_by_id(puzzle_id)
    if not puzzle:
        raise HTTPException(status_code=404, detail=f"No puzzle found with id {puzzle_id}")

    # check if admin solution is requested
    if include_solution:
        if not user or not user.is_superuser:
            raise HTTPException(status_code=403, detail="Admin privileges required to include solution")
        formatted = service.format_puzzle_with_solution_for_admin(puzzle)
        return PuzzleDefinitionSolution.model_validate(formatted)

    formatted = service.format_puzzle_for_frontend(puzzle)
    return PuzzleDefinitionResponse.model_validate(formatted)


@router.post("/freeplay/submit", status_code=201)
async def submit_freeplay_attempt(
    attempt_data: FreeplayAttemptCreate,
    db: AsyncDatabase,
    device_id: uuid.UUID = Depends(get_device_id),
    user: Optional[User] = Depends(fastapi_users.current_user(optional=True)),
):
    """
    Submit a freeplay puzzle attempt with device tracking and optional user authentication.

    - Device ID is always required (from cookie)
    - User is included if authenticated
    - Returns success status with attempt ID

    Example request body:
    ```json
    {
        "puzzle_id": 123,
        "completion_time_client_ms": 45000,
        "action_history": [...],
        "board_state": [[1,2,3], [4,5,6]],
        "is_solved": true,
        "used_tutorial": false
    }
    ```
    """
    service = PuzzleService(db)
    attempt = await service.create_freeplay_attempt(attempt_data=attempt_data, device_id=device_id, user=user)

    return {"status": "Puzzle submitted.", "id": str(attempt.id)}


@router.get("/freeplay/leaderboard", response_model=LeaderboardResponse)
async def get_freeplay_leaderboard(
    db: AsyncDatabase,
    puzzle_type: str = Query(..., description="Type of puzzle"),
    puzzle_size: str = Query(..., description="Size of puzzle"),
    puzzle_difficulty: str = Query(..., description="Difficulty level"),
    limit: int = Query(10, description="Maximum number of entries to return", ge=1, le=100),
) -> LeaderboardResponse:
    """
    Get leaderboard for freeplay puzzles by type, size, and difficulty.

    Only includes entries from authenticated users with their best completion times.

    Example: GET /api/puzzle/freeplay/leaderboard/?puzzle_type=sudoku&puzzle_size=9x9&puzzle_difficulty=easy&limit=10
    """
    service = PuzzleService(db)
    leaderboard_data = await service.get_freeplay_leaderboard(
        puzzle_type=puzzle_type, puzzle_size=puzzle_size, puzzle_difficulty=puzzle_difficulty, limit=limit
    )

    return LeaderboardResponse.model_validate(leaderboard_data)


@router.get("/admin/summary")
async def get_game_data_summary(
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user())
):
    """
    get summary of all game data for admin users.

    returns list of puzzle types with puzzle counts and attempt statistics.
    requires admin authentication.
    """
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="admin access required")

    service = PuzzleService(db)
    return await service.get_game_data_summary()


@router.get("/admin/{puzzle_type}/export")
async def export_game_data(
    puzzle_type: str,
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user()),
    user_type: Optional[str] = Query(None, description="Filter by user type: authenticated or anonymous")
):
    """
    export game data as json download.

    optionally filter by user_type (authenticated, anonymous).
    returns json file download with all freeplay attempt data.
    requires admin authentication.
    """
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="admin access required")

    service = PuzzleService(db)
    data = await service.export_game_data(puzzle_type, user_type)

    # create filename
    user_type_suffix = f"_{user_type}" if user_type else ""
    filename = f"{puzzle_type}{user_type_suffix}_game_export.json"

    from fastapi.responses import JSONResponse
    return JSONResponse(
        content=data,
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "application/json"
        }
    )
