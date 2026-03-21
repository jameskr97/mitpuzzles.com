import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.errors import ErrorResponse


class FilterOption(BaseModel):
    """a single filter option with its count."""
    value: str
    count: int


class FilterOptionsResponse(BaseModel):
    """available filter options with counts."""
    puzzle_types: List[FilterOption]
    puzzle_sizes: List[FilterOption]
    puzzle_difficulties: List[FilterOption]
    attempts_options: List[FilterOption]


class PuzzleVariant(BaseModel):
    """a size/difficulty combination for a puzzle type."""
    size: str
    difficulty: Optional[str] = None


class PuzzleTypeConfig(BaseModel):
    """metadata for a single puzzle type."""
    available_difficulties: List[PuzzleVariant]
    default_difficulty: PuzzleVariant
    total_puzzles: int


PuzzleTypesResponse = Dict[str, PuzzleTypeConfig]


class PuzzleDefinitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    puzzle_type: str
    rows: int
    cols: int
    initial_state: List[List[int]]
    solution: Optional[List[List[int]]] = None
    solution_hash: str
    meta: Dict[str, Any]

class PuzzleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    puzzle_hash: str
    puzzle_type: str
    puzzle_size: str
    puzzle_difficulty: str
    puzzle_data: Dict[str, Any]

class PuzzleIdResponse(BaseModel):
    """Schema for puzzle ID only responses"""
    model_config = ConfigDict(from_attributes=True)

    puzzle_id: uuid.UUID

class PriorityPuzzleResponse(BaseModel):
    """Schema for priority puzzle responses"""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    puzzle_id: uuid.UUID
    puzzle_type: str
    puzzle_size: str
    puzzle_difficulty: Optional[str]
    added_at: datetime
    is_active: bool
    times_shown: int
    times_solved: int


class FreeplayAttemptCreate(BaseModel):
    """Schema for creating freeplay puzzle attempts"""
    puzzle_id: uuid.UUID = Field(..., description="ID of the associated puzzle")
    timestamp_start: int = Field(description="Start time of the attempt")
    timestamp_finish: int = Field(default=None, description="Finish time of the attempt")
    action_history: List[Dict[str, Any]] = Field(default_factory=list, description="History of user actions")
    board_state: List[List[int]] = Field(default_factory=list, description="Final board state")
    is_solved: bool = Field(default=False, description="Whether the puzzle was solved")
    used_tutorial: bool = Field(default=False, description="Whether tutorial was used")


class LeaderboardEntryResponse(BaseModel):
    """Schema for leaderboard entry responses"""
    model_config = ConfigDict(from_attributes=True)

    rank: int
    duration_display: str
    username: str
    is_current_user: bool = False


class LeaderboardResponse(BaseModel):
    """Schema for leaderboard responses"""
    model_config = ConfigDict(from_attributes=True)

    leaderboard: List[LeaderboardEntryResponse]
    count: int

class PriorityPuzzleSummary(BaseModel):
    """Schema for priority puzzle summary (without full definition)"""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    puzzle_id: uuid.UUID
    added_at: datetime
    is_active: bool
    times_shown: int
    times_solved: int

class PriorityGroupResponse(BaseModel):
    """Schema for a group of priority puzzles by type/size/difficulty"""
    model_config = ConfigDict(from_attributes=True)

    puzzle_type: str
    puzzle_size: str
    puzzle_difficulty: Optional[str]
    total_puzzles: int
    total_shown: int
    total_solved: int
    puzzles: List[PriorityPuzzleSummary]


class PriorityGroupedListResponse(BaseModel):
    """Schema for grouped list of priority puzzles"""
    model_config = ConfigDict(from_attributes=True)

    groups: List[PriorityGroupResponse]
    total_groups: int
    total_puzzles: int



class PriorityPuzzleListResponse(BaseModel):
    """Schema for list of priority puzzles"""
    model_config = ConfigDict(from_attributes=True)

    priorities: List[PriorityPuzzleResponse]
    total_count: int



class PuzzleStatsResponse(BaseModel):
    """statistics for a specific puzzle."""
    puzzle_id: str
    total_attempts: int
    solved_attempts: int
    solve_rate: float
    authenticated_attempts: int
    anonymous_attempts: int
    avg_duration_seconds: Optional[float]
    min_duration_seconds: Optional[float]
    max_duration_seconds: Optional[float]
    unique_devices: int
    unique_users: int


class PaginatedPuzzlesResponse(BaseModel):
    """paginated puzzle browse results."""
    puzzles: List[PuzzleDefinitionResponse]
    total_count: int
    offset: int
    limit: int
    has_more: bool


class DailyPuzzleStatus(BaseModel):
    """status of a single daily puzzle for a user/device."""
    puzzle_type: str
    puzzle_id: str
    daily_puzzle_id: str
    is_solved: bool
    completion_time: Optional[str]


class DailyTodayResponse(BaseModel):
    """response for today's daily puzzle status."""
    date: str
    puzzles: List[DailyPuzzleStatus]


class PuzzleSubmitResponse(BaseModel):
    """response for puzzle submission endpoints."""
    status: str
    id: str


class AddPriorityRequest(BaseModel):
    """schema for adding a puzzle to priority."""
    puzzle_id: uuid.UUID
