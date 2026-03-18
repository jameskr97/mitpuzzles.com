import uuid
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query, Depends

from app.dependencies import AsyncDatabase, get_device_id
from app.modules.authentication import User, fastapi_users
from app.modules.puzzle.schemas import (
    PuzzleDefinitionResponse,
    PuzzleDefinitionSolution,
    PuzzleIdResponse,
    FreeplayAttemptCreate,
    LeaderboardResponse,
)
from app.modules.puzzle.services import PuzzleService, LeaderboardService
from app.modules.puzzle.formatting import format_puzzle_for_frontend, format_puzzle_with_solution

router = APIRouter()


@router.get("/definition/random", response_model=PuzzleIdResponse)
async def get_random_puzzle(
    db: AsyncDatabase,
    puzzle_type: str = Query(..., description="Type of puzzle"),
    puzzle_size: Optional[str] = Query(None, description="Size of puzzle"),
    puzzle_difficulty: Optional[str] = Query(None, description="Difficulty level"),
):
    """get a random puzzle ID matching the specified criteria."""
    service = PuzzleService(db)
    puzzle = await service.get_random_puzzle(puzzle_type=puzzle_type, puzzle_size=puzzle_size, puzzle_difficulty=puzzle_difficulty)
    if not puzzle:
        raise HTTPException(status_code=404, detail=f"No puzzle found for type='{puzzle_type}', size='{puzzle_size}', difficulty='{puzzle_difficulty}'")
    return PuzzleIdResponse(puzzle_id=puzzle.id)


@router.get("/next", response_model=PuzzleIdResponse)
async def get_next_puzzle(
    db: AsyncDatabase,
    device_id: uuid.UUID = Depends(get_device_id),
    user: Optional[User] = Depends(fastapi_users.current_user(optional=True)),
    puzzle_type: str = Query(..., description="Type of puzzle"),
    puzzle_size: Optional[str] = Query(None, description="Size of puzzle"),
    puzzle_difficulty: Optional[str] = Query(None, description="Difficulty level"),
    session_id: Optional[uuid.UUID] = Query(None, description="Current session ID"),
):
    """get the next puzzle for this user/device with priority and uniqueness enforcement."""
    service = PuzzleService(db)
    user_id = user.id if user else None

    puzzle = await service.get_next_puzzle(
        device_id=device_id, user_id=user_id,
        puzzle_type=puzzle_type, puzzle_size=puzzle_size, puzzle_difficulty=puzzle_difficulty,
    )

    if not puzzle:
        puzzle = await service.get_next_puzzle(
            device_id=device_id, user_id=user_id,
            puzzle_type=puzzle_type, puzzle_size=puzzle_size, puzzle_difficulty=puzzle_difficulty,
            ignore_seen=True,
        )

    if not puzzle:
        raise HTTPException(
            status_code=404,
            detail=f"No available puzzles for type='{puzzle_type}', size='{puzzle_size}', difficulty='{puzzle_difficulty}'",
        )

    await service.record_puzzle_shown(device_id=device_id, user_id=user_id, puzzle_id=puzzle.id, session_id=session_id)
    return PuzzleIdResponse(puzzle_id=puzzle.id)


@router.get("/definition/types")
async def get_types(db: AsyncDatabase):
    """get puzzle type metadata."""
    return await PuzzleService(db).get_types()


@router.get("/filter-options")
async def get_filter_options(
    db: AsyncDatabase,
    puzzle_type: Optional[List[str]] = Query(default=None),
    puzzle_size: Optional[List[str]] = Query(default=None),
    puzzle_difficulty: Optional[List[str]] = Query(default=None),
    has_attempts: Optional[str] = Query(default=None),
    filter_user_id: Optional[uuid.UUID] = Query(default=None),
    filter_device_id: Optional[uuid.UUID] = Query(default=None),
):
    """get available filter options with counts based on current selections."""
    return await PuzzleService(db).get_dynamic_filter_options(
        puzzle_types=puzzle_type, puzzle_sizes=puzzle_size, puzzle_difficulties=puzzle_difficulty,
        has_attempts=has_attempts, filter_user_id=filter_user_id, filter_device_id=filter_device_id,
    )


@router.get("/browse")
async def browse_puzzles(
    db: AsyncDatabase,
    puzzle_id: Optional[str] = Query(default=None),
    puzzle_type: Optional[List[str]] = Query(default=None),
    puzzle_size: Optional[List[str]] = Query(default=None),
    puzzle_difficulty: Optional[List[str]] = Query(default=None),
    has_attempts: Optional[str] = Query(default=None),
    include_solution: bool = Query(default=False),
    limit: int = Query(64, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """browse puzzles with optional filtering and pagination."""
    return await PuzzleService(db).browse_puzzles(
        puzzle_id=puzzle_id, puzzle_types=puzzle_type, puzzle_sizes=puzzle_size,
        puzzle_difficulties=puzzle_difficulty, has_attempts=has_attempts,
        include_solution=include_solution, limit=limit, offset=offset,
    )


@router.get("/definition/{puzzle_id}")
async def get_puzzle(
    db: AsyncDatabase,
    puzzle_id: uuid.UUID,
    include_solution: bool = Query(False),
    user: Optional[User] = Depends(fastapi_users.current_user(optional=True)),
):
    """get puzzle definition."""
    service = PuzzleService(db)
    puzzle = await service.get_puzzle_by_id(puzzle_id)
    if not puzzle:
        raise HTTPException(status_code=404, detail=f"No puzzle found with id {puzzle_id}")

    if include_solution:
        if not user or not user.is_superuser:
            raise HTTPException(status_code=403, detail="Admin privileges required to include solution")
        return PuzzleDefinitionSolution.model_validate(format_puzzle_with_solution(puzzle))

    return PuzzleDefinitionResponse.model_validate(format_puzzle_for_frontend(puzzle))


@router.get("/stats/{puzzle_id}")
async def get_puzzle_stats(db: AsyncDatabase, puzzle_id: uuid.UUID):
    """get statistics for a specific puzzle."""
    service = PuzzleService(db)
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
    """submit a freeplay puzzle attempt."""
    attempt = await PuzzleService(db).create_freeplay_attempt(attempt_data=attempt_data, device_id=device_id, user=user)
    return {"status": "Puzzle submitted.", "id": str(attempt.id)}


@router.get("/freeplay/leaderboard", response_model=LeaderboardResponse)
async def get_freeplay_leaderboard(
    db: AsyncDatabase,
    puzzle_type: str = Query(...),
    puzzle_size: str = Query(...),
    puzzle_difficulty: str = Query(...),
    limit: int = Query(10, ge=1, le=100),
    time_period: str = Query("all_time"),
    scoring_method: str = Query("best"),
    user: Optional[User] = Depends(fastapi_users.current_user(optional=True)),
):
    """get leaderboard for freeplay puzzles."""
    valid_periods = ["all_time", "today", "weekly", "monthly"]
    if time_period not in valid_periods:
        raise HTTPException(status_code=400, detail=f"Invalid time_period. Must be one of: {', '.join(valid_periods)}")

    valid_scoring = ["best", "ao_n"]
    if scoring_method not in valid_scoring:
        raise HTTPException(status_code=400, detail=f"Invalid scoring_method. Must be one of: {', '.join(valid_scoring)}")

    service = LeaderboardService(db)
    if scoring_method == "ao_n":
        data = await service.get_freeplay_leaderboard_ao_n(
            puzzle_type=puzzle_type, puzzle_size=puzzle_size, puzzle_difficulty=puzzle_difficulty,
            limit=limit, user=user, time_period=time_period,
        )
    else:
        data = await service.get_freeplay_leaderboard(
            puzzle_type=puzzle_type, puzzle_size=puzzle_size, puzzle_difficulty=puzzle_difficulty,
            limit=limit, user=user, time_period=time_period,
        )

    return LeaderboardResponse.model_validate(data)
