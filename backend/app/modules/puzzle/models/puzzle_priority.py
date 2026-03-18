from datetime import datetime, timezone
import uuid
from typing import Dict, Any, Optional

from sqlalchemy import String, DateTime, Index, UUID, Boolean, text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models import Base
from .puzzle import Puzzle

class PuzzlePriority(Base):
    """
    Tracks puzzles that should be served with priority.
    Priority puzzles are served randomly first, then regular puzzles.
    """
    __tablename__ = "puzzle_priority"
    __table_args__ = (
        Index("idx_priority_active", "puzzle_id", "added_at", "removed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, server_default=text("uuidv7()"))

    # Puzzle reference
    puzzle_id: Mapped[uuid.UUID] = mapped_column(UUID(), ForeignKey("puzzle.id", ondelete="CASCADE"), nullable=False)

    # Temporal tracking
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)
    removed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True)

    # Relationships
    puzzle: Mapped["Puzzle"] = relationship("Puzzle", backref="priority_records")

    @property
    def is_active(self) -> bool:
        """Returns True if this priority is currently active"""
        return self.removed_at is None
