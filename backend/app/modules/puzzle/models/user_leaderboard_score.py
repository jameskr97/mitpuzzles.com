from datetime import datetime
import uuid

from sqlalchemy import String, DateTime, Float, Index, UUID, text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class UserLeaderboardScore(Base):
    """precomputed best average-of-n scores per user per puzzle category."""
    __tablename__ = "user_leaderboard_score"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "puzzle_type", "puzzle_size", "puzzle_difficulty", "score_type",
            name="uq_user_leaderboard_score",
        ),
        Index("idx_leaderboard_lookup", "puzzle_type", "puzzle_size", "puzzle_difficulty", "score_type", "time_ms"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuidv7()"))
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    puzzle_type: Mapped[str] = mapped_column(String(50), nullable=False)
    puzzle_size: Mapped[str] = mapped_column(String(20), nullable=False)
    puzzle_difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    score_type: Mapped[str] = mapped_column(String(10), nullable=False)  # ao3, ao5, ao12
    time_ms: Mapped[float] = mapped_column(Float, nullable=False)

    user: Mapped["User"] = relationship("User", backref="leaderboard_scores")
