from datetime import datetime, timezone
import uuid
from typing import Dict, Any, Optional

from sqlalchemy import String, DateTime, Index, UUID, Boolean, text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models import Base
from .puzzle import Puzzle
from .freeplay_puzzle_attempt import FreeplayPuzzleAttempt


class PuzzleShown(Base):
    """
    Records every puzzle shown to a user/device.
    Enforces: logged-in users can't see same puzzle on ANY device,
             anonymous users can't see same puzzle on THEIR device.
    """
    __tablename__ = "puzzle_shown"
    __table_args__ = (
        Index("idx_shown_device_puzzle", "device_id", "puzzle_id"),
        Index("idx_shown_user_puzzle", "user_id", "puzzle_id"),
        Index("idx_shown_session", "session_id"),
        Index("idx_shown_at", "shown_at"),
        Index("idx_shown_device_unique", "device_id", "puzzle_id",
              unique=True,
              postgresql_where=text("user_id IS NULL")),
        Index("idx_shown_user_unique", "user_id", "puzzle_id",
              unique=True,
              postgresql_where=text("user_id IS NOT NULL")),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, server_default=text("uuidv7()"))
    shown_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)

    # User/device/session identifiers
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(), ForeignKey("device.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(), ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(), nullable=True)

    # Puzzle reference
    puzzle_id: Mapped[uuid.UUID] = mapped_column(UUID(), ForeignKey("puzzle.id", ondelete="RESTRICT"), nullable=False)

    # Link to attempt (if user submitted a solution)
    attempt_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(),
        ForeignKey("freeplay_puzzle_attempt.id", ondelete="SET NULL"),
        nullable=True,
        unique=True  # one-to-one relationship
    )

    # Denormalized for analytics
    was_priority: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    device: Mapped["Device"] = relationship("Device", backref="puzzles_shown")
    user: Mapped[Optional["User"]] = relationship("User", backref="puzzles_shown")
    puzzle: Mapped["Puzzle"] = relationship("Puzzle", backref="shown_records")
    attempt: Mapped[Optional["FreeplayPuzzleAttempt"]] = relationship("FreeplayPuzzleAttempt", backref="shown_record")

