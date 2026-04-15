"""user profile routes — public stats page."""

import uuid
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import AsyncDatabase
from app.modules.authentication import User, fastapi_users
from app.modules.puzzle.schemas import (
    ErrorResponse,
    UserProfileResponse,
)
from app.modules.puzzle.services.user_stats import UserStatsService

router = APIRouter(prefix="/api", tags=["User Profile"])


@router.get(
    "/users/{username}/stats",
    response_model=UserProfileResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_user_profile_stats(
    username: str,
    db: AsyncDatabase,
    current_user: Optional[User] = Depends(fastapi_users.current_user(optional=True)),
):
    """get public profile stats for a user by username."""
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="user not found")

    stats_service = UserStatsService(db)
    profile = await stats_service.get_user_profile(user)

    profile["is_own_profile"] = current_user is not None and current_user.id == user.id

    return UserProfileResponse.model_validate(profile)


@router.get("/users/{username}/solve-history")
async def get_user_solve_history(
    username: str,
    db: AsyncDatabase,
    puzzle_type: Optional[List[str]] = Query(default=None),
    puzzle_size: Optional[List[str]] = Query(default=None),
    puzzle_difficulty: Optional[List[str]] = Query(default=None),
):
    """get solve time history for a user, filterable by type/size/difficulty."""
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="user not found")

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
