import uuid
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select, func, case, text as sa_text

from app.dependencies import AsyncDatabase
from app.modules.authentication import User
from app.modules.puzzle.schemas import ErrorResponse, RecentGameEntry
from app.modules.puzzle.services import PuzzleAdminService
from app.modules.puzzle.models import Puzzle, FreeplayPuzzleAttempt
from app.modules.puzzle.routes.dependencies import require_admin

router = APIRouter()


@router.get("/admin/summary")
async def get_game_data_summary(db: AsyncDatabase, user: User = Depends(require_admin)):
    """get summary of all game data for admin users."""
    return await PuzzleAdminService(db).get_game_data_summary()



@router.get("/admin/puzzle/{puzzle_id}")
async def get_puzzle_admin_detail(
    db: AsyncDatabase,
    puzzle_id: uuid.UUID,
    user: User = Depends(require_admin),
):
    """get puzzle details with aggregate stats for admin view."""
    from sqlalchemy.orm import selectinload

    puzzle = await db.scalar(select(Puzzle).where(Puzzle.id == puzzle_id))
    if not puzzle:
        raise HTTPException(status_code=404, detail="puzzle not found")

    # aggregate attempt stats
    duration_expr = (FreeplayPuzzleAttempt.timestamp_finish - FreeplayPuzzleAttempt.timestamp_start) / 1000.0

    stats_query = (
        select(
            func.count(FreeplayPuzzleAttempt.id).label("total_attempts"),
            func.count(FreeplayPuzzleAttempt.id).filter(FreeplayPuzzleAttempt.is_solved == True).label("solved"),
            func.avg(case(
                (FreeplayPuzzleAttempt.is_solved == True, duration_expr),
                else_=None,
            )).label("avg_time"),
            func.min(case(
                (FreeplayPuzzleAttempt.is_solved == True, duration_expr),
                else_=None,
            )).label("best_time"),
        )
        .where(
            FreeplayPuzzleAttempt.puzzle_id == puzzle_id,
            FreeplayPuzzleAttempt.timestamp_finish.is_not(None),
        )
    )
    stats = (await db.execute(stats_query)).one()

    # recent attempts
    attempts_query = (
        select(FreeplayPuzzleAttempt)
        .options(selectinload(FreeplayPuzzleAttempt.user))
        .where(FreeplayPuzzleAttempt.puzzle_id == puzzle_id, FreeplayPuzzleAttempt.timestamp_finish.is_not(None))
        .order_by(FreeplayPuzzleAttempt.timestamp_finish.desc())
        .limit(20)
    )
    attempts = (await db.execute(attempts_query)).scalars().all()

    from app.modules.puzzle.formatting import format_puzzle_with_solution
    from app.modules.puzzle.schemas import PuzzleDefinitionResponse

    return {
        "puzzle": PuzzleDefinitionResponse.model_validate(format_puzzle_with_solution(puzzle)),
        "metrics": puzzle.metrics,
        "stats": {
            "total_attempts": stats.total_attempts or 0,
            "solved": stats.solved or 0,
            "solve_rate": round(100 * (stats.solved or 0) / stats.total_attempts, 1) if stats.total_attempts else 0,
            "avg_time": round(stats.avg_time, 2) if stats.avg_time else None,
            "best_time": round(stats.best_time, 2) if stats.best_time else None,
        },
        "attempts": [
            {
                "attempt_id": str(a.id),
                "username": a.user.username if a.user else None,
                "is_solved": a.is_solved,
                "time": round((a.timestamp_finish - a.timestamp_start) / 1000.0, 2) if a.timestamp_start else None,
                "metrics": a.metrics,
            }
            for a in attempts
        ],
    }

@router.get("/admin/freeplay/preview")
async def preview_freeplay_export(
    db: AsyncDatabase,
    user: User = Depends(require_admin),
    puzzle_type: Optional[List[str]] = Query(default=None),
    puzzle_size: Optional[List[str]] = Query(default=None),
    puzzle_difficulty: Optional[List[str]] = Query(default=None),
    filter_user_id: Optional[uuid.UUID] = Query(default=None),
    filter_device_id: Optional[uuid.UUID] = Query(default=None),
    solved_filter: Optional[str] = Query(default=None),
    date_start: Optional[str] = Query(default=None),
    date_end: Optional[str] = Query(default=None),
):
    """preview freeplay export counts without downloading."""
    conditions = []
    if puzzle_type:
        conditions.append(Puzzle.puzzle_type.in_(puzzle_type))
    if puzzle_size:
        conditions.append(Puzzle.puzzle_size.in_(puzzle_size))
    if puzzle_difficulty:
        conditions.append(Puzzle.puzzle_difficulty.in_(puzzle_difficulty))
    if filter_user_id:
        conditions.append(FreeplayPuzzleAttempt.user_id == filter_user_id)
    if filter_device_id:
        conditions.append(FreeplayPuzzleAttempt.device_id == filter_device_id)
    if solved_filter == "solved":
        conditions.append(FreeplayPuzzleAttempt.is_solved == True)
    elif solved_filter == "unsolved":
        conditions.append(FreeplayPuzzleAttempt.is_solved == False)
    if date_start:
        conditions.append(FreeplayPuzzleAttempt.created_at >= datetime.strptime(date_start, "%Y-%m-%d"))
    if date_end:
        conditions.append(FreeplayPuzzleAttempt.created_at < datetime.strptime(date_end, "%Y-%m-%d") + timedelta(days=1))

    query = (
        select(
            func.count(FreeplayPuzzleAttempt.id).label("total"),
            func.sum(case((FreeplayPuzzleAttempt.user_id.is_not(None), 1), else_=0)).label("authenticated"),
            func.sum(case((FreeplayPuzzleAttempt.user_id.is_(None), 1), else_=0)).label("anonymous"),
        )
        .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
    )
    for cond in conditions:
        query = query.where(cond)

    row = (await db.execute(query)).one()
    return {"total": row.total or 0, "authenticated": row.authenticated or 0, "anonymous": row.anonymous or 0}


@router.get("/admin/freeplay/export", responses={404: {"model": ErrorResponse}})
async def export_freeplay_data(
    db: AsyncDatabase,
    _user: User = Depends(require_admin),
    puzzle_type: Optional[List[str]] = Query(default=None),
    puzzle_size: Optional[List[str]] = Query(default=None),
    puzzle_difficulty: Optional[List[str]] = Query(default=None),
    user_type: Optional[str] = Query(None),
    filter_user_id: Optional[uuid.UUID] = Query(default=None),
    filter_device_id: Optional[uuid.UUID] = Query(default=None),
    solved_filter: Optional[str] = Query(default=None),
    date_start: Optional[str] = Query(default=None),
    date_end: Optional[str] = Query(default=None),
):
    """export freeplay game data as json download."""
    data = await PuzzleAdminService(db).export_freeplay_data(
        puzzle_types=puzzle_type, puzzle_sizes=puzzle_size, puzzle_difficulties=puzzle_difficulty,
        user_type=user_type, filter_user_id=filter_user_id, filter_device_id=filter_device_id,
        solved_filter=solved_filter, date_start=date_start, date_end=date_end,
    )

    parts = ["freeplay"]
    if puzzle_type and len(puzzle_type) == 1:
        parts.append(puzzle_type[0])
    if user_type:
        parts.append(user_type)
    parts.append("export.json")

    return JSONResponse(
        content=data,
        headers={"Content-Disposition": f"attachment; filename={'_'.join(parts)}", "Content-Type": "application/json"},
    )


@router.get("/admin/{puzzle_type}/export", responses={404: {"model": ErrorResponse}})
async def export_game_data(
    puzzle_type: str,
    db: AsyncDatabase,
    _user: User = Depends(require_admin),
    user_type: Optional[str] = Query(None),
):
    """export game data for a puzzle type as json download."""
    data = await PuzzleAdminService(db).export_game_data(puzzle_type, user_type)
    suffix = f"_{user_type}" if user_type else ""
    return JSONResponse(
        content=data,
        headers={"Content-Disposition": f"attachment; filename={puzzle_type}{suffix}_game_export.json", "Content-Type": "application/json"},
    )


