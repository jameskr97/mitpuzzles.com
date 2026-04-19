"""user statistics routes — own profile only."""

from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import AsyncDatabase
from app.modules.authentication import User, fastapi_users
from app.modules.puzzle.schemas import (
    ErrorResponse,
    UserProfileResponse,
)
from app.modules.puzzle.services.user_stats import UserStatsService

router = APIRouter(prefix="/api/me", tags=["User Statistics"])


@router.get(
    "/stats",
    response_model=UserProfileResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_my_stats(
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user()),
):
    """get statistics for the current user."""
    stats_service = UserStatsService(db)
    profile = await stats_service.get_user_profile(user)
    profile["is_own_profile"] = True

    return UserProfileResponse.model_validate(profile)


@router.get("/solve-history")
async def get_my_solve_history(
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user()),
    puzzle_type: Optional[List[str]] = Query(default=None),
    puzzle_size: Optional[List[str]] = Query(default=None),
    puzzle_difficulty: Optional[List[str]] = Query(default=None),
):
    """get solve time history for the current user."""
    service = UserStatsService(db)
    history = await service.get_user_solve_history(
        user_id=user.id,
        puzzle_types=puzzle_type,
        puzzle_sizes=puzzle_size,
        puzzle_difficulties=puzzle_difficulty,
    )

    # group by puzzle_type for chart consumption
    by_type: dict[str, list] = {}
    for entry in history:
        pt = entry["puzzle_type"]
        if pt not in by_type:
            by_type[pt] = []
        by_type[pt].append({"date": str(entry["finished_at"])[:10], "avg_time": entry["duration"]})

    return [{"puzzle_type": pt, "data": points} for pt, points in by_type.items()]
