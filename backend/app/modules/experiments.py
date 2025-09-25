"""
Experiments module for tracking research participants and experiment data.
Supports Prolific integration and general experiment tracking.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

import uuid6
from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.types import JSON

from app.dependencies import AsyncDatabase, get_device_id
from app.models import Base
from app.modules.authentication import User, fastapi_users
from app.modules.device_tracking import Device


# Models
class ExperimentRun(Base):
    """Generic tracking for experiment participants from any platform"""

    __tablename__ = "experiment_run"
    __table_args__ = (
        # index for faster lookups
        Index("idx_experiment_id", "experiment_id"),
        Index("idx_recruitment_platform", "recruitment_platform"),
        Index("idx_device_id", "device_id"),
    )

    # id + audit
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid6.uuid7)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # core identifiers
    experiment_id: Mapped[str] = mapped_column(String(100), nullable=False)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("device.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True)

    # platform identification
    recruitment_platform: Mapped[str] = mapped_column(String(50), nullable=False)  # 'prolific', 'direct', 'mturk', etc.

    # experiment data (same structure for all platforms)
    experiment_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    # relationships
    device: Mapped["Device"] = relationship("Device", backref="experiment_participations")
    user: Mapped[Optional["User"]] = relationship("User", backref="experiment_participations")
    prolific: Mapped[Optional["ExperimentProlificData"]] = relationship("ExperimentProlificData", back_populates="run", uselist=False)

    @hybrid_property
    def is_authenticated(self) -> bool:
        return self.user_id is not None

    def __repr__(self):
        return f"<ExperimentRun(id={self.id}, experiment={self.experiment_id}, platform={self.recruitment_platform})>"


class ExperimentProlificData(Base):
    """Platform-specific data for Prolific participants"""

    __tablename__ = "experiment_run_prolific_data"
    __table_args__ = (
        # ensure unique participation per study/session/subject combo
        UniqueConstraint("prolific_pid", "study_id", "session_id", name="unique_prolific_participation"),
        # index for faster lookups
        Index("idx_prolific_pid", "prolific_pid"),
        Index("idx_study_id", "study_id"),
    )

    # primary key is the participation id
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("experiment_run.id", ondelete="CASCADE"), primary_key=True)

    # prolific identifiers from URL parameters
    prolific_pid: Mapped[str] = mapped_column(String(100), nullable=False)
    study_id: Mapped[str] = mapped_column(String(100), nullable=False)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False)

    # relationship back to participation
    run: Mapped["ExperimentRun"] = relationship("ExperimentRun", back_populates="prolific")

    def __repr__(self):
        return f"<ProlificData(run_id={self.run_id}, pid={self.prolific_pid}, study={self.study_id})>"


# Keep old model for backwards compatibility during migration
# class ProlificParticipation(Base):
#     """Legacy Prolific participation model - DEPRECATED, use ExperimentParticipation + ProlificData"""
#
#     __tablename__ = "prolific_participation"
#     __table_args__ = (
#         # ensure unique participation per study/session/subject combo
#         UniqueConstraint("prolific_subject_id", "prolific_study_id", "prolific_session_id", name="unique_prolific_participation"),
#         # index for faster lookups
#         Index("idx_prolific_subject", "prolific_subject_id"),
#         Index("idx_prolific_study", "prolific_study_id"),
#     )
#
#     # id + audit
#     id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid6.uuid7)
#     created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow, nullable=False)
#     updated_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
#
#     # website identifiers
#     device_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("device.id", ondelete="CASCADE"), nullable=True)
#     user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
#
#     # prolific identifiers from URL parameters
#     prolific_subject_id: Mapped[str] = mapped_column(String(100), nullable=False)
#     prolific_study_id: Mapped[str] = mapped_column(String(100), nullable=False)
#     prolific_session_id: Mapped[str] = mapped_column(String(100), nullable=False)
#
#     # study tracking
#     experiment_id: Mapped[str] = mapped_column(String(100), nullable=False)
#     survey_response: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
#     experiment_data: Mapped[List[Any]] = mapped_column(JSON, default=dict, nullable=False)
#
#     # Relationships
#     device: Mapped["Device"] = relationship("Device", backref="prolific_participations")
#     user: Mapped[Optional["User"]] = relationship("User", backref="prolific_participations")
#
#     @hybrid_property
#     def is_authenticated(self) -> bool:
#         return self.user_id is not None
#
#     def __repr__(self):
#         return f"<ProlificParticipation(id={self.id}, subject={self.prolific_subject_id}, study={self.prolific_study_id})>"
#


### Schemas
class ExperimentRunExperimentData(BaseModel):
    """Schema representing experiment run data"""

    identifier: str = Field(..., max_length=100, description="Internal experiment identifier")
    timestamp_start: int = Field(..., description="Experiment start timestamp")
    timestamp_end: int = Field(..., description="Experiment end timestamp")


class ExperimentRunCreate(BaseModel):
    """Schema for creating new experiment participation"""

    experiment: ExperimentRunExperimentData = Field(ExperimentRunExperimentData, description="Internal experiment identifier")
    participant: Dict[str, Any] = Field(description="Participant info (prolific, direct, etc.)")
    nodes: List[Dict[str, Any]] = Field(description="Experiment nodes data")


class ProlificParticipationCreate(BaseModel):
    """Legacy schema for Prolific participation - DEPRECATED"""

    prolific_study_id: str = Field(..., max_length=100, description="Prolific study ID")
    prolific_participant_id: str = Field(..., max_length=100, description="Prolific participant ID")
    prolific_session_id: str = Field(..., max_length=100, description="Prolific session ID")
    experiment_id: str = Field(..., max_length=100, description="Internal experiment identifier")
    experiment_data: List[Any] = Field(description="Initial experiment data")
    survey: Dict[str, Any] = Field(default=None, description="Survey response data")


### Service
class ExperimentService:
    """Service for managing experiment operations"""

    def __init__(self, db: AsyncDatabase):
        self.db = db

    async def create_experiment_participation(self, run_data: ExperimentRunCreate, device_id: uuid.UUID, user: Optional[User] = None) -> ExperimentRun:
        """
        create experiment participation record for any platform.
        rejects duplicates for prolific participants to prevent data modification.
        """
        from sqlalchemy import select
        from fastapi import HTTPException

        participant_data = run_data.participant
        recruitment_platform = participant_data.get("recruitment_platform")

        # initialize prolific variables
        prolific_pid = None
        study_id = None
        session_id = None

        # for prolific participants, check for existing participation and reject
        if recruitment_platform == "prolific":
            try:
                prolific_pid = participant_data["prolific_pid"]
                study_id = participant_data["study_id"]
                session_id = participant_data["session_id"]
            except KeyError as e:
                raise HTTPException(status_code=400, detail=f"missing required prolific parameter: {e.args[0]}")

            # check for existing prolific participation
            stmt = (
                select(ExperimentRun)
                .join(ExperimentProlificData)
                .where(
                    ExperimentProlificData.prolific_pid == prolific_pid,
                    ExperimentProlificData.study_id == study_id,
                    ExperimentProlificData.session_id == session_id,
                    ExperimentRun.experiment_id == run_data.experiment.identifier,
                )
            )
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                raise HTTPException(status_code=409, detail=f"experiment already completed for prolific session {session_id}")

        # create new participation
        participation = ExperimentRun(
            experiment_id=run_data.experiment.identifier,
            experiment_data=run_data.model_dump(),
            recruitment_platform=recruitment_platform,
            device_id=device_id,
            user_id=user.id if user else None,
        )

        self.db.add(participation)
        await self.db.flush()

        # create platform-specific data if needed
        if recruitment_platform == "prolific":
            # prolific data should already be validated above, but be explicit
            prolific_data = ExperimentProlificData(
                run_id=participation.id,
                prolific_pid=prolific_pid,
                study_id=study_id,
                session_id=session_id,
            )
            self.db.add(prolific_data)

        await self.db.commit()
        await self.db.refresh(participation)
        return participation


### Routes
router = APIRouter(prefix="/api/experiment", tags=["Experiments"])


@router.post("", status_code=201)
async def create_experiment_participation(
    run_data: ExperimentRunCreate,
    db: AsyncDatabase,
    device_id: uuid.UUID = Depends(get_device_id),
    user: Optional[User] = Depends(fastapi_users.current_user(optional=True)),
):
    """
    Create experiment participation record for any platform.

    Handles participants from:
    - Prolific (with prolific_pid, study_id, session_id)
    - Direct website visitors
    - Future platforms (MTurk, SONA, etc.)

    Rejects duplicate submissions for Prolific participants.

    Example request body:
    ```json
    {
        "experiment_id": "blind-sudoku",
        "experiment_data": {
            "experiment_id": "blind-sudoku",
            "participant_data": {
                "recruitment_platform": "prolific",
                "prolific_pid": "5f3a8b2c9d4e7a001b3c5d8f",
                "study_id": "64a9c3d8e1f2b5001c8d3a7b",
                "session_id": "7b2d4f8a3c9e5b001d6a8c3f"
            },
            "timestamps": {...},
            "nodes": [...]
        },
        "participant_data": {
            "recruitment_platform": "prolific",
            "prolific_pid": "5f3a8b2c9d4e7a001b3c5d8f",
            "study_id": "64a9c3d8e1f2b5001c8d3a7b",
            "session_id": "7b2d4f8a3c9e5b001d6a8c3f"
        }
    }
    ```
    """
    service = ExperimentService(db)
    await service.create_experiment_participation(run_data=run_data, device_id=device_id, user=user)
    return Response(status_code=201)
