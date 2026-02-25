"""
Puzzles module for managing puzzle data and tracking puzzle attempts.
Stores pre-generated puzzles and tracks user/device attempts at solving them.
"""

import uuid
from datetime import datetime, timedelta
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
from app.service.encoder import PrecisePuzzleEncoder, ResearchFormatTranslator
from app.modules.tracking import Device
from app.modules.user_profile import UserProfile
from app.utils import get_device_type_from_thumbmark


LEADERBOARD_TOP_N_AVERAGE = 3


def format_duration(time_seconds: float) -> str:
    parts = []
    remaining = int(time_seconds)
    days = remaining // 86400
    remaining %= 86400
    hours = remaining // 3600
    remaining %= 3600
    minutes = remaining // 60
    seconds = time_seconds % 60
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or hours > 0 or days > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds:.2f}s")
    return ":".join(parts)


def is_research_format(board_state, action_history):
    """Check if data is already in research format by looking for -1 (empty cell marker)."""
    # Check board_state for -1
    if board_state:
        for row in board_state:
            if isinstance(row, list) and -1 in row:
                return True

    # Check action_history old_value/new_value for -1
    if action_history:
        for action in action_history:
            if action.get('old_value') == -1 or action.get('new_value') == -1:
                return True

    return False


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

    # Distribution control
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

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


class PuzzlePriority(Base):
    """
    Tracks puzzles that should be served with priority.
    Priority puzzles are served randomly first, then regular puzzles.
    """
    __tablename__ = "puzzle_priority"
    __table_args__ = (
        Index("idx_priority_active", "puzzle_id", "added_at", "removed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, server_default=text("uuidv7()"))

    # Puzzle reference
    puzzle_id: Mapped[uuid.UUID] = mapped_column(UUID(), ForeignKey("puzzle.id", ondelete="CASCADE"), nullable=False)

    # Temporal tracking
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)
    removed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True)

    # Relationships
    puzzle: Mapped["Puzzle"] = relationship("Puzzle", backref="priority_records")

    @property
    def is_active(self) -> bool:
        """Returns True if this priority is currently active"""
        return self.removed_at is None


class PuzzleShown(Base):
    """
    Records every puzzle shown to a user/device.
    Enforces: logged-in users can't see same puzzle on ANY device,
             anonymous users can't see same puzzle on THEIR device.
    """
    __tablename__ = "puzzle_shown"
    __table_args__ = (
        Index("idx_shown_device_puzzle", "device_id", "puzzle_id"),
        Index("idx_shown_user_puzzle", "user_id", "puzzle_id"),
        Index("idx_shown_session", "session_id"),
        Index("idx_shown_at", "shown_at"),
        Index("idx_shown_device_unique", "device_id", "puzzle_id",
              unique=True,
              postgresql_where=text("user_id IS NULL")),
        Index("idx_shown_user_unique", "user_id", "puzzle_id",
              unique=True,
              postgresql_where=text("user_id IS NOT NULL")),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, server_default=text("uuidv7()"))
    shown_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)

    # User/device/session identifiers
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(), ForeignKey("device.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(), ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(), nullable=True)

    # Puzzle reference
    puzzle_id: Mapped[uuid.UUID] = mapped_column(UUID(), ForeignKey("puzzle.id", ondelete="RESTRICT"), nullable=False)

    # Link to attempt (if user submitted a solution)
    attempt_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(),
        ForeignKey("freeplay_puzzle_attempt.id", ondelete="SET NULL"),
        nullable=True,
        unique=True  # one-to-one relationship
    )

    # Denormalized for analytics
    was_priority: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    device: Mapped["Device"] = relationship("Device", backref="puzzles_shown")
    user: Mapped[Optional["User"]] = relationship("User", backref="puzzles_shown")
    puzzle: Mapped["Puzzle"] = relationship("Puzzle", backref="shown_records")
    attempt: Mapped[Optional["FreeplayPuzzleAttempt"]] = relationship("FreeplayPuzzleAttempt", backref="shown_record")


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
    is_current_user: bool = False

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


class PriorityPuzzleResponse(BaseModel):
    """Schema for priority puzzle responses"""
    id: uuid.UUID
    puzzle_id: uuid.UUID
    puzzle_type: str
    puzzle_size: str
    puzzle_difficulty: Optional[str]
    added_at: datetime
    is_active: bool
    times_shown: int
    times_solved: int

    model_config = ConfigDict(from_attributes=True)


class PriorityPuzzleSummary(BaseModel):
    """Schema for priority puzzle summary (without full definition)"""
    id: uuid.UUID
    puzzle_id: uuid.UUID
    added_at: datetime
    is_active: bool
    times_shown: int
    times_solved: int

    model_config = ConfigDict(from_attributes=True)


class PriorityGroupResponse(BaseModel):
    """Schema for a group of priority puzzles by type/size/difficulty"""
    puzzle_type: str
    puzzle_size: str
    puzzle_difficulty: Optional[str]
    total_puzzles: int
    total_shown: int
    total_solved: int
    puzzles: List[PriorityPuzzleSummary]

    model_config = ConfigDict(from_attributes=True)


class PriorityGroupedListResponse(BaseModel):
    """Schema for grouped list of priority puzzles"""
    groups: List[PriorityGroupResponse]
    total_groups: int
    total_puzzles: int

    model_config = ConfigDict(from_attributes=True)


class PriorityPuzzleListResponse(BaseModel):
    """Schema for list of priority puzzles"""
    priorities: List[PriorityPuzzleResponse]
    total_count: int

    model_config = ConfigDict(from_attributes=True)


class AddPriorityRequest(BaseModel):
    """Schema for adding a puzzle to priority"""
    puzzle_id: uuid.UUID


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
        from sqlalchemy import select, func, Integer, cast

        # Start with base query - only active puzzles
        query = select(Puzzle).where(Puzzle.puzzle_type == puzzle_type).where(Puzzle.is_active == True)

        # Handle size selection
        if puzzle_size:
            query = query.where(Puzzle.puzzle_size == puzzle_size)
        else:
            # Get all available sizes for this puzzle type (only active puzzles)
            size_query = select(Puzzle.puzzle_size).where(Puzzle.puzzle_type == puzzle_type).where(Puzzle.is_active == True).distinct()
            sizes_result = await self.db.execute(size_query)
            all_sizes = sizes_result.scalars().all()

            if all_sizes:
                # Parse sizes like "5x5" and get the smallest one based on first number
                smallest_size = min(all_sizes, key=lambda x: int(x.split("x")[0]))
                query = query.where(Puzzle.puzzle_size == smallest_size)

        # Add difficulty filter if specified
        if puzzle_difficulty:
            query = query.where(Puzzle.puzzle_difficulty == puzzle_difficulty)

        if puzzle_type == "nonograms":
            NONOGRAMS_MIN_BLACK_CELLS_PERCENTAGE = 0.1 # >10% must be black cells
            count_black_cells = cast(Puzzle.puzzle_data['count_black_cells'].as_string(), Integer)
            rows = cast(Puzzle.puzzle_data['rows'].as_string(), Integer)
            cols = cast(Puzzle.puzzle_data['cols'].as_string(), Integer)
            query = query.where(count_black_cells > (rows * cols * NONOGRAMS_MIN_BLACK_CELLS_PERCENTAGE))

        # Order by random
        query = query.order_by(func.random())
        return await self.db.scalar(query)

    async def get_next_puzzle(
        self,
        device_id: uuid.UUID,
        user_id: Optional[uuid.UUID],
        puzzle_type: str,
        puzzle_size: Optional[str] = None,
        puzzle_difficulty: Optional[str] = None
    ) -> Optional[Puzzle]:
        """
        Get next puzzle for user, enforcing uniqueness rules.
        Prioritizes unshown priority puzzles, then random unshown puzzles.

        Rules:
        - Logged in users: can't see same puzzle on ANY device
        - Anonymous users: can't see same puzzle on THEIR device
        """
        from sqlalchemy import select, func, or_, and_
        from sqlalchemy.orm import aliased

        # Build base query - only active puzzles
        query = select(Puzzle).where(Puzzle.puzzle_type == puzzle_type).where(Puzzle.is_active == True)

        # Apply size/difficulty filters
        if puzzle_size:
            query = query.where(Puzzle.puzzle_size == puzzle_size)
        else:
            # Get smallest available size (same logic as get_random_puzzle, only active puzzles)
            size_query = select(Puzzle.puzzle_size).where(Puzzle.puzzle_type == puzzle_type).where(Puzzle.is_active == True).distinct()
            sizes_result = await self.db.execute(size_query)
            all_sizes = sizes_result.scalars().all()

            if all_sizes:
                smallest_size = min(all_sizes, key=lambda x: int(x.split("x")[0]))
                query = query.where(Puzzle.puzzle_size == smallest_size)

        if puzzle_difficulty:
            query = query.where(Puzzle.puzzle_difficulty == puzzle_difficulty)

        # Apply nonograms filter (same as get_random_puzzle)
        if puzzle_type == "nonograms":
            from sqlalchemy import Integer, cast
            NONOGRAMS_MIN_BLACK_CELLS_PERCENTAGE = 0.1
            count_black_cells = cast(Puzzle.puzzle_data['count_black_cells'].as_string(), Integer)
            rows = cast(Puzzle.puzzle_data['rows'].as_string(), Integer)
            cols = cast(Puzzle.puzzle_data['cols'].as_string(), Integer)
            query = query.where(count_black_cells > (rows * cols * NONOGRAMS_MIN_BLACK_CELLS_PERCENTAGE))

        # Left join with active priority records
        PriorityAlias = aliased(PuzzlePriority)
        query = query.outerjoin(
            PriorityAlias,
            and_(
                Puzzle.id == PriorityAlias.puzzle_id,
                PriorityAlias.removed_at == None
            )
        )

        # Exclude puzzles based on uniqueness rules
        ShownAlias = aliased(PuzzleShown)
        if user_id:
            # Logged in: exclude any puzzle this user has seen on ANY device
            query = query.outerjoin(
                ShownAlias,
                and_(
                    Puzzle.id == ShownAlias.puzzle_id,
                    ShownAlias.user_id == user_id
                )
            )
        else:
            # Anonymous: exclude puzzles THIS device has seen (while anonymous)
            query = query.outerjoin(
                ShownAlias,
                and_(
                    Puzzle.id == ShownAlias.puzzle_id,
                    ShownAlias.device_id == device_id,
                    ShownAlias.user_id == None
                )
            )

        query = query.where(ShownAlias.id == None)

        # Try to get a priority puzzle first
        priority_query = query.where(PriorityAlias.id.is_not(None)).order_by(func.random())
        priority_puzzle = await self.db.scalar(priority_query.limit(1))

        if priority_puzzle:
            return priority_puzzle

        # No priority puzzles left, get any random puzzle
        random_query = query.order_by(func.random())
        return await self.db.scalar(random_query.limit(1))

    async def record_puzzle_shown(
        self,
        device_id: uuid.UUID,
        user_id: Optional[uuid.UUID],
        puzzle_id: uuid.UUID,
        session_id: Optional[uuid.UUID] = None,
    ) -> PuzzleShown:
        """
        Record that a puzzle was shown to a user/device.
        Captures priority status at time of showing.
        """
        from sqlalchemy import select, and_

        # Check if puzzle is currently a priority
        priority_query = select(PuzzlePriority).where(
            and_(
                PuzzlePriority.puzzle_id == puzzle_id,
                PuzzlePriority.removed_at == None
            )
        )
        priority_record = await self.db.scalar(priority_query)

        was_priority = priority_record is not None

        # Create shown record
        puzzle_shown = PuzzleShown(
            device_id=device_id,
            user_id=user_id,
            session_id=session_id,
            puzzle_id=puzzle_id,
            was_priority=was_priority,
        )

        self.db.add(puzzle_shown)
        await self.db.commit()
        await self.db.refresh(puzzle_shown)
        return puzzle_shown

    async def link_puzzle_shown_to_attempt(
        self,
        puzzle_id: uuid.UUID,
        device_id: uuid.UUID,
        attempt_id: uuid.UUID
    ) -> None:
        """
        Link a puzzle_shown record to a freeplay attempt.
        Finds the most recent shown record for this puzzle/device and links it.
        """
        from sqlalchemy import select, and_, desc

        # Find the most recent shown record for this puzzle and device
        query = select(PuzzleShown).where(
            and_(
                PuzzleShown.puzzle_id == puzzle_id,
                PuzzleShown.device_id == device_id,
                PuzzleShown.attempt_id == None  # not already linked
            )
        ).order_by(desc(PuzzleShown.shown_at)).limit(1)

        puzzle_shown = await self.db.scalar(query)

        if puzzle_shown:
            puzzle_shown.attempt_id = attempt_id
            await self.db.commit()

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

    async def get_puzzle_stats(self, puzzle_id: uuid.UUID) -> Dict[str, Any]:
        """Get statistics for a specific puzzle."""
        from sqlalchemy import select, func, case

        # Duration in seconds (timestamps are in milliseconds)
        duration_expr = (FreeplayPuzzleAttempt.timestamp_finish - FreeplayPuzzleAttempt.timestamp_start) / 1000.0

        # Get attempt stats
        stats_query = select(
            func.count(FreeplayPuzzleAttempt.id).label('total_attempts'),
            func.sum(case((FreeplayPuzzleAttempt.is_solved == True, 1), else_=0)).label('solved_attempts'),
            func.sum(case((FreeplayPuzzleAttempt.user_id.is_not(None), 1), else_=0)).label('authenticated_attempts'),
            func.sum(case((FreeplayPuzzleAttempt.user_id.is_(None), 1), else_=0)).label('anonymous_attempts'),
            func.avg(duration_expr).label('avg_duration_seconds'),
            func.min(duration_expr).label('min_duration_seconds'),
            func.max(duration_expr).label('max_duration_seconds'),
            func.count(func.distinct(FreeplayPuzzleAttempt.device_id)).label('unique_devices'),
            func.count(func.distinct(FreeplayPuzzleAttempt.user_id)).label('unique_users'),
        ).where(
            FreeplayPuzzleAttempt.puzzle_id == puzzle_id,
            FreeplayPuzzleAttempt.timestamp_finish.is_not(None),
        )

        result = await self.db.execute(stats_query)
        row = result.one()

        total_attempts = row.total_attempts or 0
        solved_attempts = row.solved_attempts or 0

        return {
            "puzzle_id": str(puzzle_id),
            "total_attempts": total_attempts,
            "solved_attempts": solved_attempts,
            "solve_rate": round(solved_attempts / total_attempts * 100, 1) if total_attempts > 0 else 0,
            "authenticated_attempts": row.authenticated_attempts or 0,
            "anonymous_attempts": row.anonymous_attempts or 0,
            "avg_duration_seconds": round(row.avg_duration_seconds, 1) if row.avg_duration_seconds else None,
            "min_duration_seconds": round(row.min_duration_seconds, 1) if row.min_duration_seconds else None,
            "max_duration_seconds": round(row.max_duration_seconds, 1) if row.max_duration_seconds else None,
            "unique_devices": row.unique_devices or 0,
            "unique_users": row.unique_users or 0,
        }

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

        # Link to puzzle_shown record if one exists
        await self.link_puzzle_shown_to_attempt(
            puzzle_id=attempt_data.puzzle_id,
            device_id=device_id,
            attempt_id=attempt.id
        )

        return attempt

    async def get_freeplay_leaderboard(self, puzzle_type: str, puzzle_size: str, puzzle_difficulty: str, limit: int = 10, user: Optional[User] = None, time_period: str = "all_time") -> Dict[str, Any]:
        """get leaderboard for freeplay puzzles by type, size, and difficulty. only includes authenticated users.
        if user is logged in, they will always appear in the leaderboard with their position.

        time_period options: 'all_time', 'today' (last 24 hours), 'weekly' (last 7 days), 'monthly' (last 30 days)"""
        from sqlalchemy import select, func, and_

        # calculate cutoff datetime based on time_period (rolling windows)
        cutoff = None
        if time_period == "today":
            cutoff = datetime.utcnow() - timedelta(hours=24)
        elif time_period == "weekly":
            cutoff = datetime.utcnow() - timedelta(days=7)
        elif time_period == "monthly":
            cutoff = datetime.utcnow() - timedelta(days=30)
        # all_time has no cutoff

        # build base where conditions
        base_conditions = [
            FreeplayPuzzleAttempt.is_solved == True,  # noqa: E712, == True is intentional here
            FreeplayPuzzleAttempt.user_id.is_not(None),  # only authenticated users
            Puzzle.puzzle_type == puzzle_type,
            Puzzle.puzzle_size == puzzle_size,
            Puzzle.puzzle_difficulty == puzzle_difficulty,
            FreeplayPuzzleAttempt.timestamp_finish.is_not(None),
            FreeplayPuzzleAttempt.timestamp_start.is_not(None),
            FreeplayPuzzleAttempt.used_tutorial == False,
        ]

        # add time filter if applicable
        if cutoff:
            base_conditions.append(FreeplayPuzzleAttempt.created_at >= cutoff)

        # create subquery to get best time per user for each (type X size X difficulty)
        # timestamps are stored as milliseconds, so convert to seconds for readability
        best_times_subquery = (
            select(
                FreeplayPuzzleAttempt.user_id,
                func.min((FreeplayPuzzleAttempt.timestamp_finish - FreeplayPuzzleAttempt.timestamp_start) / 1000.0).label("best_time_seconds"),
            )
            .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
            .where(and_(*base_conditions))
            .group_by(FreeplayPuzzleAttempt.user_id)
            .subquery()
        )

        # build main query where conditions (slightly different - no timestamp_finish/start checks)
        main_query_conditions = [
            FreeplayPuzzleAttempt.is_solved == True,  # noqa: E712, == True is intentional here
            FreeplayPuzzleAttempt.user_id.is_not(None),
            Puzzle.puzzle_type == puzzle_type,
            Puzzle.puzzle_size == puzzle_size,
            Puzzle.puzzle_difficulty == puzzle_difficulty,
        ]

        if cutoff:
            main_query_conditions.append(FreeplayPuzzleAttempt.created_at >= cutoff)

        # main query to get leaderboard with user info
        query = (
            select(
                FreeplayPuzzleAttempt.user_id,
                ((FreeplayPuzzleAttempt.timestamp_finish - FreeplayPuzzleAttempt.timestamp_start) / 1000.0).label("completion_time_seconds"),
                User.username
            )
            .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
            .join(User, FreeplayPuzzleAttempt.user_id == User.id)
            .join(
                best_times_subquery,
                and_(
                    FreeplayPuzzleAttempt.user_id == best_times_subquery.c.user_id,
                    ((FreeplayPuzzleAttempt.timestamp_finish - FreeplayPuzzleAttempt.timestamp_start) / 1000.0) == best_times_subquery.c.best_time_seconds,
                ),
            )
            .where(and_(*main_query_conditions))
            .order_by(((FreeplayPuzzleAttempt.timestamp_finish - FreeplayPuzzleAttempt.timestamp_start) / 1000.0).asc())
        )

        result = await self.db.execute(query)
        all_rows = result.all()

        # get current user's position if logged in
        current_user_entry = None
        current_user_rank = None
        if user:
            for idx, row in enumerate(all_rows, 1):
                if row.user_id == user.id:
                    current_user_rank = idx
                    current_user_entry = row
                    break

        # get top N entries
        top_entries = all_rows[:limit]

        # format leaderboard entries
        leaderboard_entries = []
        current_user_in_top = False

        for rank, row in enumerate(top_entries, 1):
            is_current = bool(user and row.user_id == user.id)
            if is_current:
                current_user_in_top = True

            leaderboard_entries.append({
                "rank": rank,
                "duration_display": format_duration(row.completion_time_seconds),
                "username": row.username,
                "is_current_user": is_current
            })

        # if current user is not in top N but has a score, add them at the end
        if user and current_user_entry and not current_user_in_top:
            leaderboard_entries.append({
                "rank": current_user_rank,
                "duration_display": format_duration(current_user_entry.completion_time_seconds),
                "username": current_user_entry.username,
                "is_current_user": True
            })

        return {"leaderboard": leaderboard_entries, "count": len(leaderboard_entries)}

    async def get_freeplay_leaderboard_ao_n(self, puzzle_type: str, puzzle_size: str, puzzle_difficulty: str, limit: int = 10, user: Optional[User] = None, time_period: str = "all_time") -> Dict[str, Any]:
        """get leaderboard using average of best N times for freeplay puzzles.
        users must have at least N solves to appear. N is defined by LEADERBOARD_TOP_N_AVERAGE."""
        from sqlalchemy import select, func, and_

        n = LEADERBOARD_TOP_N_AVERAGE

        # calculate cutoff datetime based on time_period
        cutoff = None
        if time_period == "today":
            cutoff = datetime.utcnow() - timedelta(hours=24)
        elif time_period == "weekly":
            cutoff = datetime.utcnow() - timedelta(days=7)
        elif time_period == "monthly":
            cutoff = datetime.utcnow() - timedelta(days=30)

        # build base conditions
        base_conditions = [
            FreeplayPuzzleAttempt.is_solved == True,  # noqa: E712
            FreeplayPuzzleAttempt.user_id.is_not(None),
            Puzzle.puzzle_type == puzzle_type,
            Puzzle.puzzle_size == puzzle_size,
            Puzzle.puzzle_difficulty == puzzle_difficulty,
            FreeplayPuzzleAttempt.timestamp_finish.is_not(None),
            FreeplayPuzzleAttempt.timestamp_start.is_not(None),
            FreeplayPuzzleAttempt.used_tutorial == False,
        ]
        if cutoff:
            base_conditions.append(FreeplayPuzzleAttempt.created_at >= cutoff)

        completion_time = (FreeplayPuzzleAttempt.timestamp_finish - FreeplayPuzzleAttempt.timestamp_start) / 1000.0

        # rank each user's solves by time
        ranked = (
            select(
                FreeplayPuzzleAttempt.user_id,
                completion_time.label("completion_time_seconds"),
                func.row_number().over(
                    partition_by=FreeplayPuzzleAttempt.user_id,
                    order_by=completion_time.asc()
                ).label("rn"),
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

        # join with User table
        query = (
            select(
                avg_subquery.c.user_id,
                avg_subquery.c.avg_time_seconds.label("completion_time_seconds"),
                User.username,
            )
            .join(User, avg_subquery.c.user_id == User.id)
            .order_by(avg_subquery.c.avg_time_seconds.asc())
        )

        result = await self.db.execute(query)
        all_rows = result.all()

        # find current user position
        current_user_entry = None
        current_user_rank = None
        if user:
            for idx, row in enumerate(all_rows, 1):
                if row.user_id == user.id:
                    current_user_rank = idx
                    current_user_entry = row
                    break

        top_entries = all_rows[:limit]

        leaderboard_entries = []
        current_user_in_top = False

        for rank, row in enumerate(top_entries, 1):
            is_current = bool(user and row.user_id == user.id)
            if is_current:
                current_user_in_top = True
            leaderboard_entries.append({
                "rank": rank,
                "duration_display": format_duration(row.completion_time_seconds),
                "username": row.username,
                "is_current_user": is_current,
            })

        if user and current_user_entry and not current_user_in_top:
            leaderboard_entries.append({
                "rank": current_user_rank,
                "duration_display": format_duration(current_user_entry.completion_time_seconds),
                "username": current_user_entry.username,
                "is_current_user": True,
            })

        return {"leaderboard": leaderboard_entries, "count": len(leaderboard_entries)}

    async def browse_puzzles(
        self,
        puzzle_id: Optional[str] = None,
        puzzle_types: Optional[List[str]] = None,
        puzzle_sizes: Optional[List[str]] = None,
        puzzle_difficulties: Optional[List[str]] = None,
        has_attempts: Optional[str] = None,
        include_solution: bool = False,
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

        if puzzle_id:
            filter_conditions.append(Puzzle.id == uuid.UUID(puzzle_id))
        if puzzle_types and len(puzzle_types) > 0:
            filter_conditions.append(Puzzle.puzzle_type.in_(puzzle_types))
        if puzzle_sizes and len(puzzle_sizes) > 0:
            filter_conditions.append(Puzzle.puzzle_size.in_(puzzle_sizes))
        if puzzle_difficulties and len(puzzle_difficulties) > 0:
            filter_conditions.append(Puzzle.puzzle_difficulty.in_(puzzle_difficulties))

        # Handle attempts filter
        if has_attempts == 'with_attempts':
            # Only puzzles that have attempts
            attempts_subquery = select(FreeplayPuzzleAttempt.id).where(FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
            filter_conditions.append(exists(attempts_subquery))
        elif has_attempts == 'without_attempts':
            # Only puzzles that have no attempts
            attempts_subquery = select(FreeplayPuzzleAttempt.id).where(FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
            filter_conditions.append(~exists(attempts_subquery))

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
        format_fn = self.format_puzzle_with_solution_for_admin if include_solution else self.format_puzzle_for_frontend
        formatted_puzzles = [format_fn(puzzle) for puzzle in puzzles]

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
            # Only translate if data is in old enum format (no -1 values found)
            if is_research_format(attempt.board_state, attempt.action_history):
                translated_board_state = attempt.board_state
                translated_action_history = attempt.action_history
            else:
                try:
                    translator = ResearchFormatTranslator(puzzle_type)
                    translated_board_state = translator.translate_grid(attempt.board_state) if attempt.board_state else attempt.board_state
                    translated_action_history = translator.translate_action_history(attempt.action_history) if attempt.action_history else attempt.action_history
                except ValueError:
                    # Unknown puzzle type, use original data
                    translated_board_state = attempt.board_state
                    translated_action_history = attempt.action_history

            # Extract initial board from puzzle_data (already in research format)
            initial_board = None
            if attempt.puzzle.puzzle_data:
                initial_board = attempt.puzzle.puzzle_data.get('initial_state')

            attempt_data = {
                'id': str(attempt.id),
                'created_at': attempt.created_at.isoformat(),
                'timestamp_start': attempt.timestamp_start,
                'timestamp_finish': attempt.timestamp_finish,
                'action_history': translated_action_history,
                'board_state': translated_board_state,
                'used_tutorial': attempt.used_tutorial,
                'is_solved': attempt.is_solved,
                'device_id': str(attempt.device_id) if attempt.device_id else None,
                'puzzle': {
                    'id': str(attempt.puzzle.id),
                    **attempt.puzzle.puzzle_data,
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
    ):
        """Export freeplay data with flexible filtering for multiple types/sizes/difficulties."""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        # Build query with filters
        stmt = (
            select(FreeplayPuzzleAttempt)
            .options(
                selectinload(FreeplayPuzzleAttempt.puzzle),
                selectinload(FreeplayPuzzleAttempt.user),
                selectinload(FreeplayPuzzleAttempt.device).selectinload(Device.thumbmarks)
            )
            .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
        )

        # Apply filters
        if puzzle_types and len(puzzle_types) > 0:
            stmt = stmt.where(Puzzle.puzzle_type.in_(puzzle_types))
        if puzzle_sizes and len(puzzle_sizes) > 0:
            stmt = stmt.where(Puzzle.puzzle_size.in_(puzzle_sizes))
        if puzzle_difficulties and len(puzzle_difficulties) > 0:
            stmt = stmt.where(Puzzle.puzzle_difficulty.in_(puzzle_difficulties))

        # Filter by specific user or device
        if filter_user_id:
            stmt = stmt.where(FreeplayPuzzleAttempt.user_id == filter_user_id)
        if filter_device_id:
            stmt = stmt.where(FreeplayPuzzleAttempt.device_id == filter_device_id)

        # Filter by solved status
        if solved_filter == 'solved':
            stmt = stmt.where(FreeplayPuzzleAttempt.is_solved == True)
        elif solved_filter == 'unsolved':
            stmt = stmt.where(FreeplayPuzzleAttempt.is_solved == False)

        # Filter by user type if specified
        if user_type == 'authenticated':
            stmt = stmt.where(FreeplayPuzzleAttempt.user_id.is_not(None))
        elif user_type == 'anonymous':
            stmt = stmt.where(FreeplayPuzzleAttempt.user_id.is_(None))

        # Filter by date range
        if date_start:
            stmt = stmt.where(FreeplayPuzzleAttempt.created_at >= datetime.strptime(date_start, "%Y-%m-%d"))
        if date_end:
            stmt = stmt.where(FreeplayPuzzleAttempt.created_at < datetime.strptime(date_end, "%Y-%m-%d") + timedelta(days=1))

        stmt = stmt.order_by(FreeplayPuzzleAttempt.created_at.desc())

        result = await self.db.execute(stmt)
        attempts = result.scalars().all()

        if not attempts:
            raise HTTPException(status_code=404, detail="No attempts found matching the specified filters")

        # Fetch user profiles for all users with attempts
        user_ids = [a.user_id for a in attempts if a.user_id]
        user_profiles = {}
        if user_ids:
            profile_stmt = select(UserProfile).where(UserProfile.user_id.in_(user_ids))
            profile_result = await self.db.execute(profile_stmt)
            for profile in profile_result.scalars().all():
                user_profiles[profile.user_id] = profile

        export_data = []
        for attempt in attempts:
            puzzle_type = attempt.puzzle.puzzle_type

            # Only translate if data is in old enum format (no -1 values found)
            if is_research_format(attempt.board_state, attempt.action_history):
                translated_board_state = attempt.board_state
                translated_action_history = attempt.action_history
            else:
                try:
                    translator = ResearchFormatTranslator(puzzle_type)
                    translated_board_state = translator.translate_grid(attempt.board_state) if attempt.board_state else attempt.board_state
                    translated_action_history = translator.translate_action_history(attempt.action_history) if attempt.action_history else attempt.action_history
                except ValueError:
                    # Unknown puzzle type, use original data
                    translated_board_state = attempt.board_state
                    translated_action_history = attempt.action_history

            # Extract initial board from puzzle_data (already in research format)
            initial_board = None
            if attempt.puzzle.puzzle_data:
                initial_board = attempt.puzzle.puzzle_data.get('initial_state')

            attempt_data = {
                'id': str(attempt.id),
                'created_at': attempt.created_at.isoformat(),
                'timestamp_start': attempt.timestamp_start,
                'timestamp_finish': attempt.timestamp_finish,
                'action_history': translated_action_history,
                'board_state': translated_board_state,
                'used_tutorial': attempt.used_tutorial,
                'is_solved': attempt.is_solved,
                'device_id': str(attempt.device_id) if attempt.device_id else None,
                'puzzle': {
                    'id': str(attempt.puzzle.id),
                    **attempt.puzzle.puzzle_data,
                }
            }

            # Add user info if available
            if attempt.user:
                user_data = {
                    'id': str(attempt.user.id),
                    'username': attempt.user.username,
                    'email': attempt.user.email
                }
                # Add profile data if available
                profile = user_profiles.get(attempt.user_id)
                if profile:
                    user_data['profile'] = {
                        'age': profile.age,
                        'gender': profile.gender,
                        'education_level': profile.education_level,
                        'game_experience': profile.game_experience
                    }
                attempt_data['user'] = user_data

            # Add device type from latest thumbmark
            if attempt.device and attempt.device.thumbmarks:
                latest_thumbmark = attempt.device.thumbmarks[-1]
                device_type = get_device_type_from_thumbmark(latest_thumbmark.thumbmark_data)
                attempt_data['device_type'] = device_type
            else:
                attempt_data['device_type'] = 'desktop'

            export_data.append(attempt_data)

        return export_data

    async def get_priority_puzzles(
        self,
        include_inactive: bool = False,
        puzzle_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get list of priority puzzles with their statistics.
        Returns puzzle info, times shown, and times solved.
        """
        from sqlalchemy import select, func, case, and_
        from sqlalchemy.orm import selectinload

        # Build base query for priority puzzles
        query = (
            select(PuzzlePriority)
            .options(selectinload(PuzzlePriority.puzzle))
            .join(Puzzle, PuzzlePriority.puzzle_id == Puzzle.id)
        )

        # Filter by active status
        if not include_inactive:
            query = query.where(PuzzlePriority.removed_at == None)

        # Filter by puzzle type
        if puzzle_type:
            query = query.where(Puzzle.puzzle_type == puzzle_type)

        # Get total count for pagination
        count_query = select(func.count(PuzzlePriority.id)).join(Puzzle, PuzzlePriority.puzzle_id == Puzzle.id)
        if not include_inactive:
            count_query = count_query.where(PuzzlePriority.removed_at == None)
        if puzzle_type:
            count_query = count_query.where(Puzzle.puzzle_type == puzzle_type)
        total_count = await self.db.scalar(count_query)

        # Apply pagination and ordering
        query = query.order_by(PuzzlePriority.added_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        priority_records = result.scalars().all()

        # Get statistics for each priority puzzle
        priorities_data = []
        for priority in priority_records:
            puzzle = priority.puzzle

            # Count times shown (where was_priority=True for this puzzle)
            shown_count_query = select(func.count(PuzzleShown.id)).where(
                and_(
                    PuzzleShown.puzzle_id == puzzle.id,
                    PuzzleShown.was_priority == True
                )
            )
            times_shown = await self.db.scalar(shown_count_query) or 0

            # Count times solved
            solved_count_query = select(func.count(FreeplayPuzzleAttempt.id)).where(
                and_(
                    FreeplayPuzzleAttempt.puzzle_id == puzzle.id,
                    FreeplayPuzzleAttempt.is_solved == True
                )
            )
            times_solved = await self.db.scalar(solved_count_query) or 0

            priorities_data.append({
                "id": priority.id,
                "puzzle_id": puzzle.id,
                "puzzle_type": puzzle.puzzle_type,
                "puzzle_size": puzzle.puzzle_size,
                "puzzle_difficulty": puzzle.puzzle_difficulty,
                "added_at": priority.added_at,
                "is_active": priority.is_active,
                "times_shown": times_shown,
                "times_solved": times_solved,
            })

        return {
            "priorities": priorities_data,
            "total_count": total_count
        }

    async def get_priority_puzzles_grouped(
        self,
        include_inactive: bool = False,
    ) -> Dict[str, Any]:
        """
        Get priority puzzles grouped by type/size/difficulty with statistics.
        Returns puzzle IDs only - definitions should be fetched separately.
        """
        from sqlalchemy import select, func, and_
        from sqlalchemy.orm import selectinload
        from collections import defaultdict

        # Build base query for priority puzzles
        query = (
            select(PuzzlePriority)
            .options(selectinload(PuzzlePriority.puzzle))
            .join(Puzzle, PuzzlePriority.puzzle_id == Puzzle.id)
        )

        # Filter by active status
        if not include_inactive:
            query = query.where(PuzzlePriority.removed_at == None)

        # Order by puzzle type, size, difficulty, then added_at
        query = query.order_by(
            Puzzle.puzzle_type,
            Puzzle.puzzle_size,
            Puzzle.puzzle_difficulty,
            PuzzlePriority.added_at.desc()
        )

        result = await self.db.execute(query)
        priority_records = result.scalars().all()

        # Group by type/size/difficulty
        groups: Dict[tuple, list] = defaultdict(list)
        for priority in priority_records:
            puzzle = priority.puzzle
            key = (puzzle.puzzle_type, puzzle.puzzle_size, puzzle.puzzle_difficulty)
            groups[key].append(priority)

        # Build response with stats for each group
        groups_data = []
        total_puzzles = 0

        for (puzzle_type, puzzle_size, puzzle_difficulty), priorities in groups.items():
            group_total_shown = 0
            group_total_solved = 0
            puzzles_data = []

            for priority in priorities:
                puzzle = priority.puzzle

                # Count times shown (where was_priority=True for this puzzle)
                shown_count_query = select(func.count(PuzzleShown.id)).where(
                    and_(
                        PuzzleShown.puzzle_id == puzzle.id,
                        PuzzleShown.was_priority == True
                    )
                )
                times_shown = await self.db.scalar(shown_count_query) or 0

                # Count times solved
                solved_count_query = select(func.count(FreeplayPuzzleAttempt.id)).where(
                    and_(
                        FreeplayPuzzleAttempt.puzzle_id == puzzle.id,
                        FreeplayPuzzleAttempt.is_solved == True
                    )
                )
                times_solved = await self.db.scalar(solved_count_query) or 0

                group_total_shown += times_shown
                group_total_solved += times_solved

                puzzles_data.append({
                    "id": priority.id,
                    "puzzle_id": puzzle.id,
                    "added_at": priority.added_at,
                    "is_active": priority.is_active,
                    "times_shown": times_shown,
                    "times_solved": times_solved,
                })

            groups_data.append({
                "puzzle_type": puzzle_type,
                "puzzle_size": puzzle_size,
                "puzzle_difficulty": puzzle_difficulty,
                "total_puzzles": len(priorities),
                "total_shown": group_total_shown,
                "total_solved": group_total_solved,
                "puzzles": puzzles_data,
            })
            total_puzzles += len(priorities)

        return {
            "groups": groups_data,
            "total_groups": len(groups_data),
            "total_puzzles": total_puzzles
        }

    async def add_priority_puzzle(self, puzzle_id: uuid.UUID) -> PuzzlePriority:
        """
        Add a puzzle to the priority queue.
        If it was previously removed, creates a new priority record.
        """
        from sqlalchemy import select, and_

        # Verify puzzle exists
        puzzle = await self.get_puzzle_by_id(puzzle_id)
        if not puzzle:
            raise HTTPException(status_code=404, detail=f"Puzzle with id {puzzle_id} not found")

        # Check if puzzle is already in active priority
        existing_query = select(PuzzlePriority).where(
            and_(
                PuzzlePriority.puzzle_id == puzzle_id,
                PuzzlePriority.removed_at == None
            )
        )
        existing = await self.db.scalar(existing_query)

        if existing:
            raise HTTPException(status_code=400, detail="Puzzle is already in the priority queue")

        # Create new priority record
        priority = PuzzlePriority(
            puzzle_id=puzzle_id,
            added_at=datetime.utcnow()
        )

        self.db.add(priority)
        await self.db.commit()
        await self.db.refresh(priority)

        return priority

    async def remove_priority_puzzle(self, priority_id: uuid.UUID) -> PuzzlePriority:
        """
        Remove a puzzle from the priority queue by marking it as removed.
        """
        from sqlalchemy import select

        # Find the priority record
        query = select(PuzzlePriority).where(PuzzlePriority.id == priority_id)
        priority = await self.db.scalar(query)

        if not priority:
            raise HTTPException(status_code=404, detail=f"Priority record with id {priority_id} not found")

        if priority.removed_at is not None:
            raise HTTPException(status_code=400, detail="Priority record is already removed")

        # Mark as removed
        priority.removed_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(priority)

        return priority

    async def get_priority_puzzle_definition(self, priority_id: uuid.UUID) -> Optional[Puzzle]:
        """
        Get the puzzle associated with a priority record.
        """
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        query = (
            select(PuzzlePriority)
            .options(selectinload(PuzzlePriority.puzzle))
            .where(PuzzlePriority.id == priority_id)
        )
        priority = await self.db.scalar(query)

        if not priority:
            return None

        return priority.puzzle

    async def get_dynamic_filter_options(
        self,
        puzzle_types: Optional[List[str]] = None,
        puzzle_sizes: Optional[List[str]] = None,
        puzzle_difficulties: Optional[List[str]] = None,
        has_attempts: Optional[str] = None,
        filter_user_id: Optional[uuid.UUID] = None,
        filter_device_id: Optional[uuid.UUID] = None,
    ) -> Dict[str, Any]:
        """
        Get available filter options with counts based on current selections.
        Returns what filter values are possible given the current filter state.
        When filter_user_id or filter_device_id is specified, only shows puzzles
        that have been attempted by that user/device.
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
                attempts_subq = select(FreeplayPuzzleAttempt.id).where(FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
                if has_attempts == 'with_attempts':
                    conditions.append(exists(attempts_subq))
                elif has_attempts == 'without_attempts':
                    conditions.append(~exists(attempts_subq))

            # Filter to only puzzles attempted by specific user/device
            if filter_user_id:
                user_attempts_subq = select(FreeplayPuzzleAttempt.id).where(
                    FreeplayPuzzleAttempt.puzzle_id == Puzzle.id,
                    FreeplayPuzzleAttempt.user_id == filter_user_id
                )
                conditions.append(exists(user_attempts_subq))
            if filter_device_id:
                device_attempts_subq = select(FreeplayPuzzleAttempt.id).where(
                    FreeplayPuzzleAttempt.puzzle_id == Puzzle.id,
                    FreeplayPuzzleAttempt.device_id == filter_device_id
                )
                conditions.append(exists(device_attempts_subq))

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
        with_attempts_subq = select(FreeplayPuzzleAttempt.id).where(FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
        with_attempts_query = select(func.count(Puzzle.id)).where(exists(with_attempts_subq))
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


@router.get("/next", response_model=PuzzleIdResponse)
async def get_next_puzzle_endpoint(
    db: AsyncDatabase,
    device_id: uuid.UUID = Depends(get_device_id),
    user: Optional[User] = Depends(fastapi_users.current_user(optional=True)),
    puzzle_type: str = Query(..., description="Type of puzzle"),
    puzzle_size: Optional[str] = Query(None, description="Size of puzzle"),
    puzzle_difficulty: Optional[str] = Query(None, description="Difficulty level"),
    session_id: Optional[uuid.UUID] = Query(None, description="Current session ID"),
) -> PuzzleIdResponse:
    """
    Get the next puzzle for this user/device with priority and uniqueness enforcement.

    Prioritizes:
    1. Priority puzzles they haven't seen (in priority_order)
    2. Random puzzles they haven't seen

    Uniqueness rules:
    - Logged in users: can't see same puzzle on ANY device
    - Anonymous users: can't see same puzzle on THEIR device

    Automatically records the view in puzzle_shown table.

    Example: GET /api/puzzle/next?puzzle_type=sudoku&puzzle_difficulty=easy&session_id=...
    """
    service = PuzzleService(db)
    user_id = user.id if user else None

    # Get next puzzle
    puzzle = await service.get_next_puzzle(
        device_id=device_id,
        user_id=user_id,
        puzzle_type=puzzle_type,
        puzzle_size=puzzle_size,
        puzzle_difficulty=puzzle_difficulty
    )

    if not puzzle:
        raise HTTPException(
            status_code=404,
            detail=f"No available puzzles for type='{puzzle_type}', size='{puzzle_size}', difficulty='{puzzle_difficulty}' that you haven't seen"
        )

    # Record that this puzzle was shown
    await service.record_puzzle_shown(
        device_id=device_id,
        user_id=user_id,
        puzzle_id=puzzle.id,
        session_id=session_id
    )

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
    filter_user_id: Optional[uuid.UUID] = Query(default=None, description="Filter to puzzles attempted by specific user"),
    filter_device_id: Optional[uuid.UUID] = Query(default=None, description="Filter to puzzles attempted by specific device"),
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
        has_attempts=has_attempts,
        filter_user_id=filter_user_id,
        filter_device_id=filter_device_id
    )


@router.get("/browse")
async def browse_puzzles(
    db: AsyncDatabase,
    puzzle_id: Optional[str] = Query(default=None, description="Filter by exact puzzle ID"),
    puzzle_type: Optional[List[str]] = Query(default=None, description="Filter by puzzle types (can specify multiple)"),
    puzzle_size: Optional[List[str]] = Query(default=None, description="Filter by puzzle sizes (can specify multiple)"),
    puzzle_difficulty: Optional[List[str]] = Query(default=None, description="Filter by difficulty levels (can specify multiple)"),
    has_attempts: Optional[str] = Query(default=None, description="Filter by attempt status: 'with_attempts', 'without_attempts', or null for all"),
    include_solution: bool = Query(default=False, description="Include puzzle solutions in response"),
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
        puzzle_id=puzzle_id,
        puzzle_types=puzzle_type,
        puzzle_sizes=puzzle_size,
        puzzle_difficulties=puzzle_difficulty,
        has_attempts=has_attempts,
        include_solution=include_solution,
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


@router.get("/stats/{puzzle_id}")
async def get_puzzle_stats(
    db: AsyncDatabase,
    puzzle_id: uuid.UUID,
):
    """
    Get statistics for a specific puzzle.

    Returns:
    - total_attempts: Total number of attempts on this puzzle
    - solved_attempts: Number of successful solves
    - solve_rate: Percentage of attempts that were solved
    - authenticated_attempts: Attempts by logged-in users
    - anonymous_attempts: Attempts by anonymous users
    - avg_duration_seconds: Average solve time in seconds
    - min_duration_seconds: Fastest solve time
    - max_duration_seconds: Slowest solve time
    - unique_devices: Number of distinct devices that attempted
    - unique_users: Number of distinct users that attempted
    """
    service = PuzzleService(db)

    # Verify puzzle exists
    puzzle = await service.get_puzzle_by_id(puzzle_id)
    if not puzzle:
        raise HTTPException(status_code=404, detail=f"No puzzle found with id {puzzle_id}")

    return await service.get_puzzle_stats(puzzle_id)


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
    time_period: str = Query("all_time", description="Time period for leaderboard: all_time, today (24h), weekly (7d), monthly (30d)"),
    scoring_method: str = Query("best", description="Scoring method: best (single best time) or ao_n (average of best N)"),
    user: Optional[User] = Depends(fastapi_users.current_user(optional=True)),
) -> LeaderboardResponse:
    """
    Get leaderboard for freeplay puzzles by type, size, and difficulty.

    Only includes entries from authenticated users with their best completion times.
    If user is logged in, they will always appear in the leaderboard with their position.

    Time periods (rolling windows):
    - all_time: All attempts ever recorded
    - today: Last 24 hours
    - weekly: Last 7 days
    - monthly: Last 30 days
    """
    valid_periods = ["all_time", "today", "weekly", "monthly"]
    if time_period not in valid_periods:
        raise HTTPException(status_code=400, detail=f"Invalid time_period. Must be one of: {', '.join(valid_periods)}")

    valid_scoring = ["best", "ao_n"]
    if scoring_method not in valid_scoring:
        raise HTTPException(status_code=400, detail=f"Invalid scoring_method. Must be one of: {', '.join(valid_scoring)}")

    service = PuzzleService(db)
    if scoring_method == "ao_n":
        leaderboard_data = await service.get_freeplay_leaderboard_ao_n(
            puzzle_type=puzzle_type, puzzle_size=puzzle_size, puzzle_difficulty=puzzle_difficulty, limit=limit, user=user, time_period=time_period
        )
    else:
        leaderboard_data = await service.get_freeplay_leaderboard(
            puzzle_type=puzzle_type, puzzle_size=puzzle_size, puzzle_difficulty=puzzle_difficulty, limit=limit, user=user, time_period=time_period
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


@router.get("/admin/freeplay/preview")
async def preview_freeplay_export(
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user()),
    puzzle_type: Optional[List[str]] = Query(default=None, description="Filter by puzzle types"),
    puzzle_size: Optional[List[str]] = Query(default=None, description="Filter by puzzle sizes"),
    puzzle_difficulty: Optional[List[str]] = Query(default=None, description="Filter by difficulties"),
    filter_user_id: Optional[uuid.UUID] = Query(default=None, description="Filter by specific user ID"),
    filter_device_id: Optional[uuid.UUID] = Query(default=None, description="Filter by specific device ID"),
    solved_filter: Optional[str] = Query(default=None, description="Filter by solved status: solved, unsolved, or all"),
    date_start: Optional[str] = Query(default=None, description="Start date YYYY-MM-DD (inclusive)"),
    date_end: Optional[str] = Query(default=None, description="End date YYYY-MM-DD (inclusive)"),
):
    """
    Preview freeplay export counts without downloading.
    Returns counts for authenticated, anonymous, and total attempts matching filters.
    """
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="admin access required")

    from sqlalchemy import select, func, case

    # Build base query conditions
    conditions = []
    if puzzle_type and len(puzzle_type) > 0:
        conditions.append(Puzzle.puzzle_type.in_(puzzle_type))
    if puzzle_size and len(puzzle_size) > 0:
        conditions.append(Puzzle.puzzle_size.in_(puzzle_size))
    if puzzle_difficulty and len(puzzle_difficulty) > 0:
        conditions.append(Puzzle.puzzle_difficulty.in_(puzzle_difficulty))

    # Filter by user or device
    if filter_user_id:
        conditions.append(FreeplayPuzzleAttempt.user_id == filter_user_id)
    if filter_device_id:
        conditions.append(FreeplayPuzzleAttempt.device_id == filter_device_id)

    # Filter by solved status
    if solved_filter == 'solved':
        conditions.append(FreeplayPuzzleAttempt.is_solved == True)
    elif solved_filter == 'unsolved':
        conditions.append(FreeplayPuzzleAttempt.is_solved == False)

    # Filter by date range
    if date_start:
        conditions.append(FreeplayPuzzleAttempt.created_at >= datetime.strptime(date_start, "%Y-%m-%d"))
    if date_end:
        conditions.append(FreeplayPuzzleAttempt.created_at < datetime.strptime(date_end, "%Y-%m-%d") + timedelta(days=1))

    # Count query
    query = (
        select(
            func.count(FreeplayPuzzleAttempt.id).label('total'),
            func.sum(case((FreeplayPuzzleAttempt.user_id.is_not(None), 1), else_=0)).label('authenticated'),
            func.sum(case((FreeplayPuzzleAttempt.user_id.is_(None), 1), else_=0)).label('anonymous'),
        )
        .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
    )

    for condition in conditions:
        query = query.where(condition)

    result = await db.execute(query)
    row = result.one()

    return {
        "total": row.total or 0,
        "authenticated": row.authenticated or 0,
        "anonymous": row.anonymous or 0,
    }


@router.get("/admin/freeplay/export")
async def export_freeplay_data(
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user()),
    puzzle_type: Optional[List[str]] = Query(default=None, description="Filter by puzzle types"),
    puzzle_size: Optional[List[str]] = Query(default=None, description="Filter by puzzle sizes"),
    puzzle_difficulty: Optional[List[str]] = Query(default=None, description="Filter by difficulties"),
    user_type: Optional[str] = Query(None, description="Filter by user type: authenticated or anonymous"),
    filter_user_id: Optional[uuid.UUID] = Query(default=None, description="Filter by specific user ID"),
    filter_device_id: Optional[uuid.UUID] = Query(default=None, description="Filter by specific device ID"),
    solved_filter: Optional[str] = Query(default=None, description="Filter by solved status: solved, unsolved, or all"),
    date_start: Optional[str] = Query(default=None, description="Start date YYYY-MM-DD (inclusive)"),
    date_end: Optional[str] = Query(default=None, description="End date YYYY-MM-DD (inclusive)"),
):
    """
    Export freeplay game data as json download with flexible filtering.

    Supports multiple puzzle types, sizes, and difficulties.
    Optionally filter by user_type (authenticated, anonymous).
    Optionally filter by specific user_id or device_id.
    Optionally filter by solved status (solved, unsolved).
    Returns json file download with all matching freeplay attempt data.
    Requires admin authentication.
    """
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="admin access required")

    service = PuzzleService(db)
    data = await service.export_freeplay_data(
        puzzle_types=puzzle_type,
        puzzle_sizes=puzzle_size,
        puzzle_difficulties=puzzle_difficulty,
        user_type=user_type,
        filter_user_id=filter_user_id,
        filter_device_id=filter_device_id,
        solved_filter=solved_filter,
        date_start=date_start,
        date_end=date_end,
    )

    # create filename
    parts = ["freeplay"]
    if puzzle_type and len(puzzle_type) == 1:
        parts.append(puzzle_type[0])
    if user_type:
        parts.append(user_type)
    parts.append("export.json")
    filename = "_".join(parts)

    from fastapi.responses import JSONResponse
    return JSONResponse(
        content=data,
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "application/json"
        }
    )


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


# Priority puzzle management endpoints
@router.get("/admin/priority", response_model=PriorityPuzzleListResponse)
async def get_priority_puzzles(
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user()),
    include_inactive: bool = Query(False, description="Include removed priority puzzles"),
    puzzle_type: Optional[str] = Query(None, description="Filter by puzzle type"),
    limit: int = Query(100, description="Maximum number of entries to return", ge=1, le=500),
    offset: int = Query(0, description="Number of entries to skip", ge=0),
):
    """
    Get list of priority puzzles with statistics.

    Returns priority puzzles with:
    - Puzzle info (type, size, difficulty)
    - When it was added to priority queue
    - Times shown as a priority puzzle
    - Times solved

    Requires admin authentication.
    """
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="admin access required")

    service = PuzzleService(db)
    return await service.get_priority_puzzles(
        include_inactive=include_inactive,
        puzzle_type=puzzle_type,
        limit=limit,
        offset=offset
    )


@router.get("/admin/priority/grouped", response_model=PriorityGroupedListResponse)
async def get_priority_puzzles_grouped(
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user()),
    include_inactive: bool = Query(False, description="Include removed priority puzzles"),
):
    """
    Get priority puzzles grouped by type/size/difficulty with statistics.

    Returns groups of priority puzzles with:
    - Group totals (puzzles, shown, solved)
    - Individual puzzle definitions for rendering
    - Stats for each puzzle

    Requires admin authentication.
    """
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="admin access required")

    service = PuzzleService(db)
    return await service.get_priority_puzzles_grouped(include_inactive=include_inactive)


@router.post("/admin/priority", status_code=201)
async def add_priority_puzzle(
    request: AddPriorityRequest,
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user()),
):
    """
    Add a puzzle to the priority queue.

    Priority puzzles are served first to users who haven't seen them.
    Requires admin authentication.
    """
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="admin access required")

    service = PuzzleService(db)
    priority = await service.add_priority_puzzle(request.puzzle_id)

    return {
        "status": "success",
        "message": "Puzzle added to priority queue",
        "priority_id": str(priority.id),
        "puzzle_id": str(priority.puzzle_id)
    }


@router.delete("/admin/priority/{priority_id}")
async def remove_priority_puzzle(
    priority_id: uuid.UUID,
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user()),
):
    """
    Remove a puzzle from the priority queue.

    The puzzle will no longer be prioritized for new users.
    Requires admin authentication.
    """
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="admin access required")

    service = PuzzleService(db)
    priority = await service.remove_priority_puzzle(priority_id)

    return {
        "status": "success",
        "message": "Puzzle removed from priority queue",
        "priority_id": str(priority.id)
    }


@router.get("/admin/priority/group/export")
async def export_priority_group_attempts(
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user()),
    puzzle_type: str = Query(..., description="Puzzle type"),
    puzzle_size: str = Query(..., description="Puzzle size"),
    puzzle_difficulty: Optional[str] = Query(None, description="Puzzle difficulty"),
    solved_only: bool = Query(True, description="Only include solved attempts"),
):
    """
    Export all attempts for priority puzzles in a group (type+size+difficulty).

    Returns all solved attempts for puzzles in this group as a JSON download.
    Requires admin authentication.
    """
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="admin access required")

    from sqlalchemy import select, and_

    service = PuzzleService(db)

    # Find all active priority puzzle IDs for this group
    query = (
        select(PuzzlePriority.puzzle_id)
        .join(Puzzle, PuzzlePriority.puzzle_id == Puzzle.id)
        .where(
            and_(
                PuzzlePriority.removed_at == None,
                Puzzle.puzzle_type == puzzle_type,
                Puzzle.puzzle_size == puzzle_size,
            )
        )
    )
    if puzzle_difficulty:
        query = query.where(Puzzle.puzzle_difficulty == puzzle_difficulty)
    else:
        query = query.where(Puzzle.puzzle_difficulty == None)

    result = await db.execute(query)
    priority_puzzle_ids = [str(row[0]) for row in result.all()]

    if not priority_puzzle_ids:
        raise HTTPException(status_code=404, detail="No priority puzzles found for this group")

    # Export attempts for the group
    difficulties = [puzzle_difficulty] if puzzle_difficulty else None
    data = await service.export_freeplay_data(
        puzzle_types=[puzzle_type],
        puzzle_sizes=[puzzle_size],
        puzzle_difficulties=difficulties,
        solved_filter='solved' if solved_only else None,
    )

    # Filter to only priority puzzles in this group
    data = [attempt for attempt in data if attempt['puzzle']['id'] in priority_puzzle_ids]

    if not data:
        raise HTTPException(status_code=404, detail="No attempts found for this priority group")

    from fastapi.responses import JSONResponse
    difficulty_part = f"_{puzzle_difficulty}" if puzzle_difficulty else ""
    filename = f"priority_{puzzle_type}_{puzzle_size}{difficulty_part}_group_attempts.json"
    return JSONResponse(
        content=data,
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "application/json"
        }
    )


@router.get("/admin/priority/{priority_id}/export")
async def export_priority_puzzle_attempts(
    priority_id: uuid.UUID,
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user()),
    solved_only: bool = Query(True, description="Only include solved attempts"),
):
    """
    Export all attempts for a priority puzzle.

    Returns all solved attempts for this puzzle as a JSON download.
    Requires admin authentication.
    """
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="admin access required")

    service = PuzzleService(db)
    puzzle = await service.get_priority_puzzle_definition(priority_id)

    if not puzzle:
        raise HTTPException(status_code=404, detail=f"Priority record with id {priority_id} not found")

    # Export attempts for this specific puzzle
    data = await service.export_freeplay_data(
        puzzle_types=[puzzle.puzzle_type],
        puzzle_sizes=[puzzle.puzzle_size],
        puzzle_difficulties=[puzzle.puzzle_difficulty] if puzzle.puzzle_difficulty else None,
        solved_filter='solved' if solved_only else None,
    )

    # Filter to only this specific puzzle
    data = [attempt for attempt in data if attempt['puzzle']['id'] == str(puzzle.id)]

    if not data:
        raise HTTPException(status_code=404, detail="No attempts found for this puzzle")

    from fastapi.responses import JSONResponse
    filename = f"priority_{puzzle.puzzle_type}_{puzzle.puzzle_size}_{puzzle.id}_attempts.json"
    return JSONResponse(
        content=data,
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "application/json"
        }
    )
