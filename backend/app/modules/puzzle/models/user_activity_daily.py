"""stores one row per user per active day, summarizing what they did."""

from datetime import date, datetime
import uuid
from typing import Dict, Any

from sqlalchemy import Date, DateTime, UUID, text, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class UserActivityDaily(Base):
    __tablename__ = "user_activity_daily"
    __table_args__ = (
        UniqueConstraint("user_id", "activity_date", name="uq_user_activity_daily"),
        Index("idx_user_activity_daily_user_date", "user_id", "activity_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, server_default=text("uuidv7()"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    activity_date: Mapped[date] = mapped_column(Date, nullable=False)
    data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
