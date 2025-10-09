"""
Feedback module for collecting user/device feedback.
Every feedback entry requires a device ID for tracking, with optional user association.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

import uuid6
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.types import JSON

from app.dependencies import AsyncDatabase, get_device_id
from app.models import Base
from app.modules.authentication import User, fastapi_users
from app.modules.tracking import Device


# Models
class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid6.uuid7)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # feedback content
    message: Mapped[str] = mapped_column(String, nullable=False)
    feedback_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # identifiers
    device_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("device.id", ondelete="CASCADE"), nullable=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True)

    # relationships
    device: Mapped["Device"] = relationship("Device", backref="feedback_items")
    user: Mapped[Optional["User"]] = relationship("User", backref="feedback_items")

    @hybrid_property
    def is_authenticated(self) -> bool:
        """Returns True if feedback is from an authenticated user."""
        return self.user_id is not None

    def __repr__(self):
        user_info = f", user={self.user_id}" if self.user_id else ""
        return f"<Feedback(id={self.id}, device={self.device_id}{user_info}, message={self.message[:50]}...)>"


### Schemas
class FeedbackCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="The feedback message")
    feedback_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class FeedbackResponse(BaseModel):
    """Schema for feedback responses."""

    id: uuid.UUID
    created_at: datetime
    message: str
    feedback_metadata: Optional[Dict[str, Any]]
    device_id: uuid.UUID
    user_id: Optional[uuid.UUID]
    is_authenticated: bool

    model_config = ConfigDict(from_attributes=True)


### Service
class FeedbackService:
    """Service for managing feedback operations."""

    def __init__(self, db: AsyncDatabase):
        self.db = db

    async def create_feedback(self, feedback_data: FeedbackCreate, device_id: uuid.UUID, user: Optional[User] = None) -> Feedback:
        """
        Create new feedback with required device tracking and optional user.
        """
        feedback = Feedback(
            message=feedback_data.message, feedback_metadata=feedback_data.feedback_metadata, device_id=device_id, user_id=user.id if user else None
        )

        self.db.add(feedback)
        await self.db.commit()
        await self.db.refresh(feedback)
        return feedback


### Routes
router = APIRouter(prefix="/api/feedback", tags=["Feedback"])


@router.post("", response_model=FeedbackResponse, status_code=201)
async def create_feedback(
    feedback_data: FeedbackCreate,
    db: AsyncDatabase,
    device_id: uuid.UUID = Depends(get_device_id),  # Always required from cookie
    user: Optional[User] = Depends(fastapi_users.current_user(optional=True)),  # Optional authentication
):
    """
    Submit feedback with device tracking and optional user authentication.

    - Device ID is always required (from cookie)
    - User is included if authenticated
    - Returns 400 if device cookie is missing

    Example request body:
    ```json
    {
        "message": "wow nice puzzle",
        "feedback_metadata": {
            "page": "/sudoku",
            "puzzle_id": "1234"
        }
    }
    ```
    """
    service = FeedbackService(db)
    feedback = await service.create_feedback(feedback_data=feedback_data, device_id=device_id, user=user)

    return FeedbackResponse.model_validate(feedback)
