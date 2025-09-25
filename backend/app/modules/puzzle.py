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
        puzzle_data = puzzle.puzzle_data

        if "size" in puzzle_data:
            puzzle_data["rows"] = puzzle_data["size"]
            puzzle_data["cols"] = puzzle_data["size"]

        # Extract meta by removing fields that go to top level
        meta = puzzle_data.copy()
        meta.pop("rows", None)
        meta.pop("cols", None)
        meta.pop("game_state", None)
        meta.pop("game_board", None)
        meta.pop("id", None)
        meta.pop("difficulty", None)
        meta.pop("idx", None)
        meta.pop("priority", None)
        meta.pop("size", None)

        return {
            "id": puzzle.id,
            "puzzle_type": puzzle.puzzle_type,
            "rows": puzzle_data["rows"],
            "cols": puzzle_data["cols"],
            "initial_state": puzzle_data["game_state"],
            "solution": puzzle_data["game_board"],
            "solution_hash": self.calculate_puzzle_solution_hash_rle(puzzle.puzzle_type, puzzle_data["game_board"]),
            "meta": meta,
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
