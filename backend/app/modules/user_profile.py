from sqlalchemy import String, Integer, JSON, select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from app.models import Base
from app.dependencies import get_async_session, AsyncSession
from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
import uuid

# SQLAlchemy Model
class UserProfile(Base):
    __tablename__ = "user_profile"

    # Primary key is also foreign key to user
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), primary_key=True)

    # Audit fields
    date_created: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    date_updated: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Profile fields
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(length=50), nullable=True)
    education_level: Mapped[Optional[str]] = mapped_column(String(length=100), nullable=True)
    game_experience: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)

    # Relationship back to user
    # user: Mapped["User"] = relationship("User", back_populates="profile")


# Pydantic Schemas
class UserProfileRead(BaseModel):
    user_id: uuid.UUID
    age: Optional[int] = None
    gender: Optional[str] = None
    education_level: Optional[str] = None
    game_experience: Optional[Dict[str, str]] = None

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    education_level: Optional[str] = None
    game_experience: Optional[Dict[str, str]] = None


# Router
router_profile = APIRouter(tags=["User Profile"])


# Import at module level
from app.modules.authentication import fastapi_users, User

@router_profile.get("/api/profile/me", response_model=UserProfileRead)
async def get_my_profile(
    current_user: User = Depends(fastapi_users.current_user()),
    session: AsyncSession = Depends(get_async_session),
):
    """Get current user's profile"""
    statement = select(UserProfile).where(UserProfile.user_id == current_user.id)
    result = await session.execute(statement)
    profile = result.scalar_one_or_none()

    if not profile:
        # Create empty profile if doesn't exist
        profile = UserProfile(user_id=current_user.id)
        session.add(profile)
        await session.commit()
        await session.refresh(profile)

    return profile


@router_profile.patch("/api/profile/me", response_model=UserProfileRead)
async def update_my_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(fastapi_users.current_user()),
    session: AsyncSession = Depends(get_async_session),
):
    """Update current user's profile"""
    statement = select(UserProfile).where(UserProfile.user_id == current_user.id)
    result = await session.execute(statement)
    profile = result.scalar_one_or_none()

    if not profile:
        # Create profile if doesn't exist
        profile = UserProfile(user_id=current_user.id)
        session.add(profile)

    # Update fields
    if profile_update.age is not None:
        profile.age = profile_update.age
    if profile_update.gender is not None:
        profile.gender = profile_update.gender
    if profile_update.education_level is not None:
        profile.education_level = profile_update.education_level
    if profile_update.game_experience is not None:
        profile.game_experience = profile_update.game_experience

    profile.date_updated = datetime.utcnow()

    await session.commit()
    await session.refresh(profile)

    return profile
