"""
Experiments module for tracking research participants and experiment data.
Supports Prolific integration and general experiment tracking.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

import uuid6
from fastapi import APIRouter, Depends, Response, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint, Index, select, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.types import JSON

from app.dependencies import AsyncDatabase, get_device_id
from app.models import Base
from app.modules.authentication import User, fastapi_users
from app.modules.tracking import Device


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

    async def get_experiments_summary(self):
        """get summary of all experiments grouped by experiment_id"""
        from sqlalchemy import case

        # get basic counts first
        stmt = (
            select(
                ExperimentRun.experiment_id,
                func.count().label('total_runs'),
                func.sum(case((ExperimentRun.recruitment_platform == 'direct', 1), else_=0)).label('direct_runs'),
                func.sum(case((ExperimentRun.recruitment_platform == 'prolific', 1), else_=0)).label('prolific_runs')
            )
            .group_by(ExperimentRun.experiment_id)
            .order_by(ExperimentRun.experiment_id)
        )

        result = await self.db.execute(stmt)
        experiments = result.all()

        # calculate average duration for each experiment manually
        summary_data = []
        for exp in experiments:
            # get all runs for this experiment to calculate average duration
            duration_stmt = select(ExperimentRun).where(ExperimentRun.experiment_id == exp.experiment_id)
            duration_result = await self.db.execute(duration_stmt)
            runs = duration_result.scalars().all()

            total_duration = 0
            valid_runs = 0

            for run in runs:
                experiment_data = run.experiment_data.get('experiment', {})
                start_time = experiment_data.get('timestamp_start')
                end_time = experiment_data.get('timestamp_end')

                if start_time and end_time:
                    duration = (end_time - start_time) / 1000  # convert to seconds
                    total_duration += duration
                    valid_runs += 1

            avg_duration = round(total_duration / valid_runs) if valid_runs > 0 else 0

            summary_data.append({
                'experiment_id': exp.experiment_id,
                'total_runs': exp.total_runs,
                'direct_runs': exp.direct_runs or 0,
                'prolific_runs': exp.prolific_runs or 0,
                'avg_duration_seconds': avg_duration
            })

        return summary_data

    async def get_experiment_details(self, experiment_id: str):
        """get detailed experiment info with node statistics"""
        # get all runs for this experiment
        stmt = (
            select(ExperimentRun)
            .where(ExperimentRun.experiment_id == experiment_id)
            .order_by(ExperimentRun.created_at.desc())
        )
        result = await self.db.execute(stmt)
        runs = result.scalars().all()

        if not runs:
            raise HTTPException(status_code=404, detail=f"experiment {experiment_id} not found")

        # calculate node statistics
        node_stats = {}
        total_duration = 0
        run_count = len(runs)

        for run in runs:
            nodes = run.experiment_data.get('nodes', [])
            experiment_data = run.experiment_data.get('experiment', {})

            # calculate total duration for this run
            start_time = experiment_data.get('timestamp_start', 0)
            end_time = experiment_data.get('timestamp_end', 0)
            if start_time and end_time:
                total_duration += (end_time - start_time) / 1000  # convert to seconds

            # process each node
            for node in nodes:
                node_name = node.get('name', 'unknown')
                node_start = node.get('timestamp_start', 0)
                node_end = node.get('timestamp_end', 0)

                if node_start and node_end:
                    duration = (node_end - node_start) / 1000  # convert to seconds

                    if node_name not in node_stats:
                        node_stats[node_name] = {'total_time': 0, 'count': 0}

                    node_stats[node_name]['total_time'] += duration
                    node_stats[node_name]['count'] += 1

        # calculate averages
        avg_node_stats = [
            {
                'node_name': name,
                'avg_time_seconds': round(stats['total_time'] / stats['count']) if stats['count'] > 0 else 0
            }
            for name, stats in node_stats.items()
        ]

        # separate runs by platform
        direct_runs = [run for run in runs if run.recruitment_platform == 'direct']
        prolific_runs = [run for run in runs if run.recruitment_platform == 'prolific']

        return {
            'experiment_id': experiment_id,
            'total_runs': run_count,
            'direct_runs': len(direct_runs),
            'prolific_runs': len(prolific_runs),
            'avg_duration_seconds': round(total_duration / run_count) if run_count > 0 else 0,
            'node_stats': avg_node_stats
        }

    async def export_experiment_data(self, experiment_id: str, platform: Optional[str] = None):
        """export experiment data as json"""
        from sqlalchemy.orm import selectinload

        stmt = (
            select(ExperimentRun)
            .options(selectinload(ExperimentRun.prolific))
            .where(ExperimentRun.experiment_id == experiment_id)
        )

        if platform:
            stmt = stmt.where(ExperimentRun.recruitment_platform == platform)

        stmt = stmt.order_by(ExperimentRun.created_at.desc())

        result = await self.db.execute(stmt)
        runs = result.scalars().all()
        print(result)

        if not runs:
            raise HTTPException(status_code=404, detail=f"no data found for experiment {experiment_id}")

        export_data = []
        for run in runs:
            run_data = {
                'id': str(run.id),
                'experiment_id': run.experiment_id,
                'recruitment_platform': run.recruitment_platform,
                'created_at': run.created_at.isoformat(),
                'experiment_data': run.experiment_data,
                'device_id': str(run.device_id),
                'user_id': str(run.user_id) if run.user_id else None
            }

            # add prolific data if available
            if run.prolific:
                run_data['prolific_data'] = {
                    'prolific_pid': run.prolific.prolific_pid,
                    'study_id': run.prolific.study_id,
                    'session_id': run.prolific.session_id
                }

            export_data.append(run_data)

        return export_data



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


@router.get("/admin/summary")
async def get_experiments_summary(
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user())
):
    """
    get summary of all experiments for admin users.

    returns list of experiments with run counts and basic stats.
    requires admin authentication.
    """
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="admin access required")

    service = ExperimentService(db)
    return await service.get_experiments_summary()


@router.get("/admin/{experiment_id}")
async def get_experiment_details(
    experiment_id: str,
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user())
):
    """
    get detailed experiment info with node statistics.

    returns experiment details including averaged node times.
    requires admin authentication.
    """
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="admin access required")

    service = ExperimentService(db)
    return await service.get_experiment_details(experiment_id)


@router.get("/admin/{experiment_id}/export")
async def export_experiment_data(
    experiment_id: str,
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user()),
    platform: Optional[str] = Query(None, description="Filter by platform: direct or prolific")
):
    """
    export experiment data as json download.

    optionally filter by platform (direct, prolific).
    returns json file download with all experiment run data.
    requires admin authentication.
    """
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="admin access required")

    service = ExperimentService(db)
    data = await service.export_experiment_data(experiment_id, platform)

    # create filename
    platform_suffix = f"_{platform}" if platform else ""
    filename = f"{experiment_id}{platform_suffix}_export.json"

    return JSONResponse(
        content=data,
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "application/json"
        }
    )
