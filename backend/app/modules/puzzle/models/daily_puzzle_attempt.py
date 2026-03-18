from datetime import datetime, timezone
import uuid
from typing import Optional

from sqlalchemy import DateTime, UUID, text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class DailyPuzzleAttempt(Base):
    """
    Records each user/device attempt at a daily puzzle.
    One attempt per device per daily puzzle.
    """
    __tablename__ = "daily_puzzle_attempt"
    __table_args__ = (
        UniqueConstraint("device_id", "daily_puzzle_id", name="uq_daily_attempt_device_daily"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, server_default=text("uuidv7()"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(), ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(), ForeignKey("device.id", ondelete="CASCADE"), nullable=False)
    daily_puzzle_id: Mapped[uuid.UUID] = mapped_column(UUID(), ForeignKey("daily_puzzle.id", ondelete="CASCADE"), nullable=False)
    attempt_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(), ForeignKey("freeplay_puzzle_attempt.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", backref="daily_attempts")
    device: Mapped["Device"] = relationship("Device", backref="daily_attempts")
    daily_puzzle: Mapped["DailyPuzzle"] = relationship("DailyPuzzle", backref="attempts")
    attempt: Mapped[Optional["FreeplayPuzzleAttempt"]] = relationship("FreeplayPuzzleAttempt", backref="daily_attempt_record")
