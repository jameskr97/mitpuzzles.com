"""user profile routes — public stats page."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
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
    """get public profile stats for a user."""
    # look up user by username
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")

    stats_service = UserStatsService(db)
    profile = await stats_service.get_user_profile(user)

    profile["is_own_profile"] = current_user is not None and current_user.id == user.id

    return UserProfileResponse.model_validate(profile)
