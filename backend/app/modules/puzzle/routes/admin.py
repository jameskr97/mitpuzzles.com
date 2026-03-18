import uuid
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select, func, case

from app.dependencies import AsyncDatabase
from app.modules.authentication import User
from app.modules.puzzle.schemas import ErrorResponse
from app.modules.puzzle.services import PuzzleAdminService
from app.modules.puzzle.models import Puzzle, FreeplayPuzzleAttempt
from app.modules.puzzle.routes.dependencies import require_admin

router = APIRouter()


@router.get("/admin/summary")
async def get_game_data_summary(db: AsyncDatabase, user: User = Depends(require_admin)):
    """get summary of all game data for admin users."""
    return await PuzzleAdminService(db).get_game_data_summary()


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


