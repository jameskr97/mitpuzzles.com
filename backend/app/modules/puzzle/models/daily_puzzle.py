from datetime import datetime, timezone
import uuid

from sqlalchemy import DateTime, UUID, text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base
from .puzzle import Puzzle


class DailyPuzzle(Base):
    """
    stores what puzzle is associated with what day
    all users see the same puzzles for a given date.
    """
    __tablename__ = "daily_puzzle"
    __table_args__ = (
        UniqueConstraint("puzzle_date", "puzzle_id", name="uq_daily_puzzle_date_puzzle"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, server_default=text("uuidv7()"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

    puzzle_date: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    puzzle_id: Mapped[uuid.UUID] = mapped_column(UUID(), ForeignKey("puzzle.id", ondelete="RESTRICT"), nullable=False)

    # Relationships
    puzzle: Mapped["Puzzle"] = relationship("Puzzle", backref="daily_records")
