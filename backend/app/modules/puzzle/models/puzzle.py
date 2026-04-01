from datetime import datetime, timezone
import uuid
from typing import Dict, Any, Optional

from sqlalchemy import String, DateTime, Index, UUID, Boolean, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.models import Base

class Puzzle(Base):
    """stores pre-generated puzzles of all types"""

    __tablename__ = "puzzle"
    __table_args__ = (
        Index("idx_puzzle_type", "puzzle_type"),
        Index("idx_puzzle_difficulty", "puzzle_difficulty"),
        Index("idx_puzzle_type_size_difficulty", "puzzle_type", "puzzle_size", "puzzle_difficulty"),
    )

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, server_default=text("uuidv7()"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # semantic ids
    complete_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    definition_id: Mapped[str] = mapped_column(String(36), nullable=False)
    solution_id: Mapped[str] = mapped_column(String(36), nullable=False)

    # puzzle metadata + normalized data
    puzzle_type: Mapped[str] = mapped_column(String(32), nullable=False)  # minesweeper, sudoku, tents, battleship...
    puzzle_size: Mapped[str] = mapped_column(String(32), nullable=False)  # 5x5, 9x9, 10x10...
    puzzle_difficulty: Mapped[str] = mapped_column(String(32), nullable=True)  # easy, medium, hard...
    puzzle_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)  # JSON Field for puzzle data

    # structure metrics
    metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Distribution control
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<Puzzle(id={self.id}, type={self.puzzle_type}, difficulty={self.puzzle_difficulty})>"
