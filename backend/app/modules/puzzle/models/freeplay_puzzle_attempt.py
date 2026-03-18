from datetime import datetime, timezone
import uuid
from typing import Dict, Any, Optional, List

from sqlalchemy import DateTime, Index, UUID, Boolean, text, ForeignKey, BigInteger
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr
from sqlalchemy.types import JSON

from app.models import Base

class FreeplayPuzzleAttempt(Base):
    """records each attempt a user makes at solving a puzzle in freeplay mode."""
    __tablename__ = "freeplay_puzzle_attempt"
    __table_args__ = (
        Index("idx_freeplay_device_puzzle", "device_id", "puzzle_id"),
        Index("idx_freeplay_is_solved", "is_solved"),
    )

    # primary key and timestamps
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuidv7()"))
    created_at: Mapped[DateTime] = mapped_column(DateTime(), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # identifiers
    device_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("device.id", ondelete="CASCADE"), nullable=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True)

    # puzzle reference
    puzzle_id: Mapped[uuid.UUID] = mapped_column(UUID(), ForeignKey("puzzle.id", ondelete="RESTRICT"), nullable=True)

    # attempt specific
    timestamp_start: Mapped[int] = mapped_column(BigInteger, nullable=False)
    timestamp_finish: Mapped[int] = mapped_column(BigInteger, nullable=True)
    action_history: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    board_state: Mapped[List[Any]] = mapped_column(JSON, default=list, nullable=False)
    used_tutorial: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_solved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Use declared_attr for relationships that need table name
    @declared_attr
    def device(cls) -> Mapped["Device"]:
        return relationship("Device", backref=f"{cls.__tablename__}_attempts")

    @declared_attr
    def user(cls) -> Mapped[Optional["User"]]:
        return relationship("User", backref=f"{cls.__tablename__}_attempts")

    @declared_attr
    def puzzle(cls) -> Mapped["Puzzle"]:
        return relationship("Puzzle", backref=f"{cls.__tablename__}_attempts")

    @hybrid_property
    def is_authenticated(self) -> bool:
        """Returns True if attempt is from an authenticated user."""
        return self.user_id is not None
