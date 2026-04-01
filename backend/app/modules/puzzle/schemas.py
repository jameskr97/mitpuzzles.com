import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.errors import ErrorResponse


class PuzzleMetrics(BaseModel):
    """Structural metrics for a puzzle definition."""
    # common
    min_actions: int
    board_size: int
    empty_cells: int
    clue_cells: int
    solution_density: float

    # type-specific
    mine_count: Optional[int] = None      # minesweeper
    given_count: Optional[int] = None     # sudoku
    bulb_count: Optional[int] = None      # lightup
    tent_count: Optional[int] = None      # tents
    water_cells: Optional[int] = None     # aquarium
    black_cells: Optional[int] = None     # kakurasu, nonograms
    shaded_cells: Optional[int] = None    # mosaic
    bridge_count: Optional[int] = None    # hashi


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
    puzzle_size: str
    puzzle_difficulty: Optional[str] = None
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


class PlaybackFrame(BaseModel):
    """a single frame in a playback — the board state after an action"""
    board: List[List[int]]
    timestamp: int
    action: str
    cell: Optional[Dict[str, int]] = None


class AttemptPlaybackResponse(BaseModel):
    """schema for attempt playback — precomputed board frames"""
    id: uuid.UUID
    puzzle_definition: PuzzleDefinitionResponse
    frames: List[PlaybackFrame]
    timestamp_start: int
    timestamp_finish: Optional[int] = None
    is_solved: bool


class LeaderboardEntryResponse(BaseModel):
    """Schema for leaderboard entry responses"""
    model_config = ConfigDict(from_attributes=True)

    rank: int
    duration_display: str
    username: str
    is_current_user: bool = False
    attempt_id: Optional[str] = None


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
    """status of today's daily puzzle for a user/device."""
    puzzle_type: str
    puzzle_size: str
    puzzle_difficulty: Optional[str]
    puzzle_id: str
    daily_puzzle_id: str
    is_solved: bool
    completion_time: Optional[str]
    board_state: Optional[List[Any]] = None


class DailyTodayResponse(BaseModel):
    """response for today's daily puzzle status."""
    date: str
    puzzle: DailyPuzzleStatus


class PuzzleSubmitResponse(BaseModel):
    """response for puzzle submission endpoints."""
    status: str
    id: str


class AddPriorityRequest(BaseModel):
    """schema for adding a puzzle to priority."""
    puzzle_id: uuid.UUID


# -- user profile --

class PuzzleTypeStatsEntry(BaseModel):
    """per-type solve stats."""
    puzzle_type: str
    solved_count: int
    attempt_count: int
    best_time: Optional[float] = None
    avg_time: Optional[float] = None


class DailyStreakStats(BaseModel):
    """daily challenge streak info."""
    current_streak: int
    longest_streak: int
    total_dailies_solved: int
    fastest_daily_count: int


class SolveTimePoint(BaseModel):
    """single data point for the solve time chart."""
    date: str
    avg_time: float


class SolveTimeSeriesEntry(BaseModel):
    """solve time history for one puzzle type."""
    puzzle_type: str
    data: List[SolveTimePoint]


class ActivityEntry(BaseModel):
    """single activity entry within a day."""
    icon: str
    text: str
    detail: Optional[str] = None


class ActivityDay(BaseModel):
    """grouped activity for a single day."""
    date: str
    entries: List[ActivityEntry]


class GameLogEntry(BaseModel):
    """a single recent game entry."""
    attempt_id: str
    puzzle_type: str
    puzzle_size: str
    puzzle_difficulty: Optional[str] = None
    time: Optional[float] = None
    solved: bool
    date: str


class FeaturedSolve(BaseModel):
    """fastest solve for a puzzle type, with attempt_id for playback."""
    puzzle_type: str
    attempt_id: str
    best_time: float


class UserProfileResponse(BaseModel):
    """full user profile stats."""
    username: str
    member_since: str
    is_own_profile: bool

    # aggregates
    total_puzzles_solved: int
    total_puzzles_attempted: int
    total_time_seconds: float

    # per-type breakdown
    puzzle_type_stats: List[PuzzleTypeStatsEntry]

    # daily streak
    daily_streak: DailyStreakStats

    # solve time chart
    solve_time_history: List[SolveTimeSeriesEntry]

    # activity feed
    activity_feed: List[ActivityDay]

    # recent games
    game_log: List[GameLogEntry]

    # featured fastest solves (top 2 most-played)
    featured_solves: List[FeaturedSolve]
