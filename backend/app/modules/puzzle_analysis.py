"""
Puzzle Analysis module for managing puzzle analysis jobs.
Handles batch analysis of puzzles for uniqueness verification and duplicate detection.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from pydantic import BaseModel, ConfigDict
from sqlalchemy import String, DateTime, Index, UUID, ForeignKey, Boolean, Integer, text, select, desc
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload
from sqlalchemy.types import JSON
from app.dependencies import AsyncDatabase
from app.models import Base
from app.modules.authentication import User, fastapi_users


class BackgroundJob(Base):
    """
    Tracks background jobs for puzzle analysis.
    Each job processes multiple puzzles for uniqueness and duplicate checking.
    """

    __tablename__ = "background_job"
    __table_args__ = (
        Index("idx_background_job_status", "status"),
        Index("idx_background_job_created", "created_at"),
        Index("idx_background_job_type", "job_type"),
    )

    # Primary key and timestamps
    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, server_default=text("uuidv7()"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Job metadata
    job_type: Mapped[str] = mapped_column(String(32), default="file_upload", nullable=False)  # file_upload, database_audit
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)  # pending, running, completed, failed
    puzzle_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_data: Mapped[Optional[List[Any]]] = mapped_column(JSON, nullable=True)  # Original uploaded puzzles

    # Progress tracking
    total_puzzles: Mapped[int] = mapped_column(Integer, nullable=False)
    processed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Summary counts
    unique_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    multi_solution_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    invalid_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    disabled_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # For database_audit: count of already-disabled puzzles

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Completion
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True)

    # Relationships
    puzzles: Mapped[List["AnalysisJobPuzzle"]] = relationship("AnalysisJobPuzzle", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<BackgroundJob(id={self.id}, status={self.status}, type={self.puzzle_type}, progress={self.processed_count}/{self.total_puzzles})>"


class AnalysisJobPuzzle(Base):
    """
    Individual puzzle within an analysis job.
    Stores the puzzle data and analysis results.
    """

    __tablename__ = "analysis_job_puzzle"
    __table_args__ = (
        Index("idx_analysis_puzzle_job", "job_id"),
        Index("idx_analysis_puzzle_status", "status"),
        Index("idx_analysis_puzzle_result", "result"),
        Index("idx_analysis_puzzle_complete_id", "complete_id"),
    )

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, server_default=text("uuidv7()"))

    # Job reference
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(), ForeignKey("background_job.id", ondelete="CASCADE"), nullable=False)
    puzzle_index: Mapped[int] = mapped_column(Integer, nullable=False)  # Position in original upload

    # Puzzle data (normalized, ready for import)
    puzzle_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Semantic IDs for duplicate detection
    definition_id: Mapped[str] = mapped_column(String(36), nullable=False)  # Same puzzle definition
    solution_id: Mapped[str] = mapped_column(String(36), nullable=False)  # Same solution
    complete_id: Mapped[str] = mapped_column(String(36), nullable=False)  # Exact match (definition + solution)

    # Analysis status and results
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)  # pending, analyzing, done, error
    result: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # unique, multi_solution, invalid, duplicate, error

    # Multiple solutions (if found)
    solutions: Mapped[Optional[List[Any]]] = mapped_column(JSON, nullable=True)
    solution_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Error info
    error_message: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Import tracking
    imported: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    imported_puzzle_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(), ForeignKey("puzzle.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    job: Mapped["BackgroundJob"] = relationship("BackgroundJob", back_populates="puzzles")

    def __repr__(self):
        return f"<AnalysisJobPuzzle(id={self.id}, index={self.puzzle_index}, status={self.status}, result={self.result})>"


# ============================================================================
# Schemas
# ============================================================================

class BackgroundJobSummary(BaseModel):
    """Summary of an analysis job for list views."""
    id: uuid.UUID
    created_at: datetime
    job_type: str
    status: str
    puzzle_type: str
    source_filename: Optional[str]
    total_puzzles: int
    processed_count: int
    unique_count: int
    multi_solution_count: int
    invalid_count: int
    duplicate_count: int
    error_count: int
    disabled_count: int
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class AnalysisJobPuzzleResponse(BaseModel):
    """Individual puzzle result."""
    id: uuid.UUID
    puzzle_index: int
    puzzle_data: Dict[str, Any]
    definition_id: str
    solution_id: str
    complete_id: str
    status: str
    result: Optional[str]
    solutions: Optional[List[Any]]
    solution_count: Optional[int]
    error_message: Optional[str]
    imported: bool

    model_config = ConfigDict(from_attributes=True)


class BackgroundJobDetail(BaseModel):
    """Full job details including puzzles."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    job_type: str
    status: str
    puzzle_type: str
    source_filename: Optional[str]
    total_puzzles: int
    processed_count: int
    unique_count: int
    multi_solution_count: int
    invalid_count: int
    duplicate_count: int
    error_count: int
    disabled_count: int
    error_message: Optional[str]
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class PaginatedPuzzles(BaseModel):
    """Paginated puzzle results."""
    items: List[AnalysisJobPuzzleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# Routes
# ============================================================================

router = APIRouter(prefix="/api/analysis", tags=["Puzzle Analysis"])


@router.get("/jobs", response_model=List[BackgroundJobSummary])
async def list_analysis_jobs(
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user(active=True, superuser=True)),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
):
    """List all analysis jobs. Admin only."""
    query = select(BackgroundJob).order_by(desc(BackgroundJob.created_at)).limit(limit)

    if status:
        query = query.where(BackgroundJob.status == status)

    result = await db.execute(query)
    jobs = result.scalars().all()

    return [BackgroundJobSummary.model_validate(job) for job in jobs]


@router.get("/jobs/{job_id}", response_model=BackgroundJobDetail)
async def get_analysis_job(
    job_id: uuid.UUID,
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user(active=True, superuser=True)),
):
    """Get details of a specific analysis job. Admin only."""
    result = await db.execute(
        select(BackgroundJob).where(BackgroundJob.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return BackgroundJobDetail.model_validate(job)


@router.get("/jobs/{job_id}/puzzles", response_model=PaginatedPuzzles)
async def get_job_puzzles(
    job_id: uuid.UUID,
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user(active=True, superuser=True)),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    result_filter: Optional[str] = Query(None, description="Filter by result (unique, multi_solution, invalid, error)"),
):
    """Get paginated puzzles for a job. Admin only."""
    # Verify job exists
    job_result = await db.execute(
        select(BackgroundJob.id).where(BackgroundJob.id == job_id)
    )
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job not found")

    # Build query
    query = select(AnalysisJobPuzzle).where(AnalysisJobPuzzle.job_id == job_id)

    if result_filter:
        query = query.where(AnalysisJobPuzzle.result == result_filter)

    # Get total count
    count_query = select(AnalysisJobPuzzle.id).where(AnalysisJobPuzzle.job_id == job_id)
    if result_filter:
        count_query = count_query.where(AnalysisJobPuzzle.result == result_filter)
    count_result = await db.execute(count_query)
    total = len(count_result.all())

    # Paginate
    offset = (page - 1) * page_size
    query = query.order_by(AnalysisJobPuzzle.puzzle_index).offset(offset).limit(page_size)

    result = await db.execute(query)
    puzzles = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size

    return PaginatedPuzzles(
        items=[AnalysisJobPuzzleResponse.model_validate(p) for p in puzzles],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.delete("/jobs/{job_id}")
async def delete_analysis_job(
    job_id: uuid.UUID,
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user(active=True, superuser=True)),
):
    """Delete an analysis job and all its puzzles. Admin only."""
    result = await db.execute(
        select(BackgroundJob).where(BackgroundJob.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    await db.delete(job)
    await db.commit()

    return {"status": "deleted", "job_id": str(job_id)}


@router.post("/jobs/{job_id}/restart")
async def restart_analysis_job(
    job_id: uuid.UUID,
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user(active=True, superuser=True)),
):
    """Restart a failed or completed analysis job. Admin only."""
    from app.tasks import analyze_puzzle_batch

    result = await db.execute(
        select(BackgroundJob).where(BackgroundJob.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status == "running":
        raise HTTPException(status_code=400, detail="Job is already running")

    # Reset job state
    job.status = "pending"
    job.processed_count = 0
    job.unique_count = 0
    job.multi_solution_count = 0
    job.invalid_count = 0
    job.duplicate_count = 0
    job.error_count = 0
    job.error_message = None
    job.completed_at = None

    # Reset puzzle states
    puzzle_result = await db.execute(
        select(AnalysisJobPuzzle).where(AnalysisJobPuzzle.job_id == job_id)
    )
    puzzles = puzzle_result.scalars().all()
    for puzzle in puzzles:
        puzzle.status = "pending"
        puzzle.result = None
        puzzle.solutions = None
        puzzle.solution_count = None
        puzzle.error_message = None

    await db.commit()

    # Start task
    analyze_puzzle_batch.delay(str(job_id))

    return {"status": "restarted", "job_id": str(job_id)}


# ============================================================================
# Request Schemas for New Endpoints
# ============================================================================

class AnalyzeDatabaseRequest(BaseModel):
    """Request to analyze existing puzzles in database."""
    puzzle_type: str
    puzzle_size: Optional[str] = None
    puzzle_difficulty: Optional[str] = None
    limit: Optional[int] = None


# ============================================================================
# New Import/Analysis Endpoints
# ============================================================================

@router.post("/analyze-database")
async def analyze_database_puzzles(
    request: AnalyzeDatabaseRequest,
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user(active=True, superuser=True)),
):
    """
    Create analysis job for existing puzzles in database.
    Useful for auditing existing puzzles for uniqueness.
    Admin only.
    """
    from app.tasks import analyze_puzzle_batch
    from app.modules.puzzle import Puzzle
    from sqlalchemy import func

    # Count disabled puzzles first
    disabled_query = select(func.count()).select_from(Puzzle).where(
        Puzzle.puzzle_type == request.puzzle_type,
        Puzzle.is_active == False
    )
    disabled_result = await db.execute(disabled_query)
    disabled_count = disabled_result.scalar() or 0

    # Build query for active puzzles only
    query = select(Puzzle).where(
        Puzzle.puzzle_type == request.puzzle_type,
        Puzzle.is_active == True
    )

    if request.puzzle_size:
        query = query.where(Puzzle.puzzle_size == request.puzzle_size)
    if request.puzzle_difficulty:
        query = query.where(Puzzle.puzzle_difficulty == request.puzzle_difficulty)

    query = query.order_by(Puzzle.created_at)

    if request.limit:
        query = query.limit(request.limit)

    result = await db.execute(query)
    puzzles = result.scalars().all()

    if not puzzles:
        raise HTTPException(
            status_code=404,
            detail=f"No active puzzles found matching criteria ({disabled_count} disabled)"
        )

    # Build source filename description
    parts = [request.puzzle_type]
    if request.puzzle_size:
        parts.append(request.puzzle_size)
    if request.puzzle_difficulty:
        parts.append(request.puzzle_difficulty)
    source_name = f"db:{':'.join(parts)}"

    # Create job
    job = BackgroundJob(
        job_type="database_audit",
        status="pending",
        puzzle_type=request.puzzle_type,
        source_filename=source_name,
        source_data=None,
        total_puzzles=len(puzzles),
        disabled_count=disabled_count,
    )
    db.add(job)
    await db.flush()

    # Create puzzle records from existing puzzles
    for idx, puzzle in enumerate(puzzles):
        puzzle_record = AnalysisJobPuzzle(
            job_id=job.id,
            puzzle_index=idx,
            puzzle_data=puzzle.puzzle_data,
            definition_id=puzzle.definition_id,
            solution_id=puzzle.solution_id,
            complete_id=puzzle.complete_id,
            status="pending",
            imported=True,  # Already in database
            imported_puzzle_id=puzzle.id,
        )
        db.add(puzzle_record)

    await db.commit()

    # Start Celery task with skip_duplicate_check=True
    analyze_puzzle_batch.delay(str(job.id), skip_duplicate_check=True)

    return {
        "job_id": str(job.id),
        "total_puzzles": len(puzzles),
        "disabled_count": disabled_count,
        "source": source_name,
    }


@router.get("/puzzle-stats/{puzzle_type}")
async def get_puzzle_stats(
    puzzle_type: str,
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user(active=True, superuser=True)),
):
    """
    Get puzzle statistics for a puzzle type.
    Returns counts of active and disabled puzzles.
    Admin only.
    """
    from app.modules.puzzle import Puzzle
    from sqlalchemy import func

    # Count active puzzles
    active_query = select(func.count()).select_from(Puzzle).where(
        Puzzle.puzzle_type == puzzle_type,
        Puzzle.is_active == True
    )
    active_result = await db.execute(active_query)
    active_count = active_result.scalar() or 0

    # Count disabled puzzles
    disabled_query = select(func.count()).select_from(Puzzle).where(
        Puzzle.puzzle_type == puzzle_type,
        Puzzle.is_active == False
    )
    disabled_result = await db.execute(disabled_query)
    disabled_count = disabled_result.scalar() or 0

    return {
        "puzzle_type": puzzle_type,
        "active_count": active_count,
        "disabled_count": disabled_count,
        "total_count": active_count + disabled_count,
    }


@router.post("/jobs/{job_id}/import-unique")
async def import_unique_puzzles(
    job_id: uuid.UUID,
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user(active=True, superuser=True)),
):
    """
    Import all unique-result puzzles from a job to the puzzle table.
    Only imports puzzles that haven't been imported yet.
    Admin only.
    """
    from app.modules.puzzle import Puzzle

    # Get job
    job_result = await db.execute(
        select(BackgroundJob).where(BackgroundJob.id == job_id)
    )
    job = job_result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Job must be completed before importing")

    # Get unique puzzles that haven't been imported
    puzzles_result = await db.execute(
        select(AnalysisJobPuzzle).where(
            AnalysisJobPuzzle.job_id == job_id,
            AnalysisJobPuzzle.result == "unique",
            AnalysisJobPuzzle.imported == False,
        )
    )
    puzzles = puzzles_result.scalars().all()

    if not puzzles:
        return {"imported": 0, "message": "No unique puzzles to import"}

    imported_count = 0
    for puzzle_record in puzzles:
        # Create new Puzzle in main table
        puzzle_data = puzzle_record.puzzle_data
        new_puzzle = Puzzle(
            puzzle_type=job.puzzle_type,
            puzzle_size=puzzle_data.get("puzzle_size", "unknown"),
            puzzle_difficulty=puzzle_data.get("puzzle_difficulty"),
            puzzle_data=puzzle_data,
            definition_id=puzzle_record.definition_id,
            solution_id=puzzle_record.solution_id,
            complete_id=puzzle_record.complete_id,
            is_active=True,
        )
        db.add(new_puzzle)
        await db.flush()

        # Mark as imported
        puzzle_record.imported = True
        puzzle_record.imported_puzzle_id = new_puzzle.id
        imported_count += 1

    await db.commit()

    return {"imported": imported_count, "job_id": str(job_id)}


@router.post("/jobs/{job_id}/disable-non-unique")
async def disable_non_unique_puzzles(
    job_id: uuid.UUID,
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user(active=True, superuser=True)),
):
    """
    Disable (is_active=false) all puzzles that were found to have multiple solutions.
    Only affects puzzles that were already in the database (imported_puzzle_id is set).
    Admin only.
    """
    from app.modules.puzzle import Puzzle
    from sqlalchemy import update

    # Get job
    job_result = await db.execute(
        select(BackgroundJob).where(BackgroundJob.id == job_id)
    )
    job = job_result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Job must be completed before disabling puzzles")

    # Get multi-solution puzzles that have imported_puzzle_id
    puzzles_result = await db.execute(
        select(AnalysisJobPuzzle).where(
            AnalysisJobPuzzle.job_id == job_id,
            AnalysisJobPuzzle.result == "multi_solution",
            AnalysisJobPuzzle.imported_puzzle_id.isnot(None),
        )
    )
    puzzles = puzzles_result.scalars().all()

    if not puzzles:
        return {"disabled": 0, "message": "No multi-solution puzzles to disable"}

    # Collect puzzle IDs to disable
    puzzle_ids = [p.imported_puzzle_id for p in puzzles]

    # Update is_active to False for these puzzles
    await db.execute(
        update(Puzzle).where(Puzzle.id.in_(puzzle_ids)).values(is_active=False)
    )
    await db.commit()

    return {"disabled": len(puzzle_ids), "job_id": str(job_id)}


@router.post("/upload")
async def upload_puzzles(
    db: AsyncDatabase,
    file: UploadFile = File(...),
    user: User = Depends(fastapi_users.current_user(active=True, superuser=True)),
):
    """
    Upload a JSON file of puzzles for analysis.

    Expected filename format: {puzzle_type}_{size}_{difficulty}.json
    Example: kakurasu_5x5_easy.json

    JSON format: Array of puzzles in raw source format:
    [
      {
        "game_state": [...],      // Initial puzzle state
        "game_board": [...],      // Solution
        "rows": 5, "cols": 5,     // Dimensions
        // Puzzle-specific fields (row_hints, col_sums, etc.)
      },
      ...
    ]

    Returns: { job_id: str, total_puzzles: int }
    """
    from app.tasks import analyze_puzzle_batch
    from cli.normalizer import PuzzleNormalizer

    # Validate file type
    if not file.filename or not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="File must be a .json file")

    # Parse filename to extract metadata
    filename_stem = file.filename.rsplit(".", 1)[0]
    parts = filename_stem.split("_")

    if len(parts) < 2:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename format. Expected: {puzzle_type}_{size}_{difficulty}.json or {puzzle_type}_{size}.json"
        )

    puzzle_type = parts[0].lower()
    puzzle_size = parts[1].lower()
    puzzle_difficulty = parts[2].lower() if len(parts) > 2 else None

    # Read and parse JSON content
    try:
        content = await file.read()
        puzzles_raw = json.loads(content.decode("utf-8"))
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

    if not isinstance(puzzles_raw, list):
        raise HTTPException(status_code=400, detail="JSON must be an array of puzzles")

    if len(puzzles_raw) == 0:
        raise HTTPException(status_code=400, detail="JSON array is empty")

    # Normalize puzzles
    normalizer = PuzzleNormalizer()

    # Validate puzzle type is supported
    if puzzle_type not in normalizer.puzzle_definitions:
        supported = ", ".join(sorted(normalizer.puzzle_definitions.keys()))
        raise HTTPException(
            status_code=400,
            detail=f"Unknown puzzle type: {puzzle_type}. Supported types: {supported}"
        )

    # Process puzzles through normalizer
    puzzles_dict = {filename_stem: puzzles_raw}
    try:
        normalized_puzzles, duplicates = normalizer.process_all_puzzles(puzzles_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error normalizing puzzles: {str(e)}")

    if not normalized_puzzles:
        raise HTTPException(status_code=400, detail="No valid puzzles found in file")

    # Create analysis job
    job = BackgroundJob(
        job_type="file_upload",
        status="pending",
        puzzle_type=puzzle_type,
        source_filename=file.filename,
        source_data=puzzles_raw,
        total_puzzles=len(normalized_puzzles),
    )
    db.add(job)
    await db.flush()

    # Create puzzle records
    for idx, puzzle_data in enumerate(normalized_puzzles):
        puzzle_record = AnalysisJobPuzzle(
            job_id=job.id,
            puzzle_index=idx,
            puzzle_data=puzzle_data,
            definition_id=puzzle_data["definition_id"],
            solution_id=puzzle_data["solution_id"],
            complete_id=puzzle_data["complete_id"],
            status="pending",
        )
        db.add(puzzle_record)

    await db.commit()

    # Start Celery task
    analyze_puzzle_batch.delay(str(job.id))

    return {
        "job_id": str(job.id),
        "total_puzzles": len(normalized_puzzles),
        "duplicates_in_file": len(duplicates),
        "puzzle_type": puzzle_type,
        "puzzle_size": puzzle_size,
        "puzzle_difficulty": puzzle_difficulty,
    }
