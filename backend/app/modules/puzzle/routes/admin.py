import uuid
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select, func, case, and_

from app.dependencies import AsyncDatabase
from app.modules.authentication import User
from app.modules.puzzle.schemas import (
    PriorityPuzzleListResponse,
    PriorityGroupedListResponse,
    AddPriorityRequest,
)
from app.modules.puzzle.services import PuzzleAdminService
from app.modules.puzzle.models import Puzzle, FreeplayPuzzleAttempt, PuzzlePriority
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


@router.get("/admin/freeplay/export")
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


@router.get("/admin/{puzzle_type}/export")
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


################################################################################
# priority puzzles

@router.get("/admin/priority", response_model=PriorityPuzzleListResponse)
async def get_priority_puzzles(
    db: AsyncDatabase,
    _user: User = Depends(require_admin),
    include_inactive: bool = Query(False),
    puzzle_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """get list of priority puzzles with statistics."""
    return await PuzzleAdminService(db).get_priority_puzzles(
        include_inactive=include_inactive, puzzle_type=puzzle_type, limit=limit, offset=offset,
    )


@router.get("/admin/priority/grouped", response_model=PriorityGroupedListResponse)
async def get_priority_puzzles_grouped(
    db: AsyncDatabase,
    _user: User = Depends(require_admin),
    include_inactive: bool = Query(False),
):
    """get priority puzzles grouped by type/size/difficulty."""
    return await PuzzleAdminService(db).get_priority_puzzles_grouped(include_inactive=include_inactive)


@router.post("/admin/priority", status_code=201)
async def add_priority_puzzle(
    request: AddPriorityRequest,
    db: AsyncDatabase,
    _user: User = Depends(require_admin),
):
    """add a puzzle to the priority queue."""
    priority = await PuzzleAdminService(db).add_priority_puzzle(request.puzzle_id)
    return {"status": "success", "message": "Puzzle added to priority queue", "priority_id": str(priority.id), "puzzle_id": str(priority.puzzle_id)}


@router.delete("/admin/priority/{priority_id}")
async def remove_priority_puzzle(
    priority_id: uuid.UUID,
    db: AsyncDatabase,
    _user: User = Depends(require_admin),
):
    """remove a puzzle from the priority queue."""
    priority = await PuzzleAdminService(db).remove_priority_puzzle(priority_id)
    return {"status": "success", "message": "Puzzle removed from priority queue", "priority_id": str(priority.id)}


@router.get("/admin/priority/group/export")
async def export_priority_group_attempts(
    db: AsyncDatabase,
    _user: User = Depends(require_admin),
    puzzle_type: str = Query(...),
    puzzle_size: str = Query(...),
    puzzle_difficulty: Optional[str] = Query(None),
    solved_only: bool = Query(True),
):
    """export all attempts for priority puzzles in a group."""
    query = (
        select(PuzzlePriority.puzzle_id)
        .join(Puzzle, PuzzlePriority.puzzle_id == Puzzle.id)
        .where(
            and_(
                PuzzlePriority.removed_at == None,
                Puzzle.puzzle_type == puzzle_type,
                Puzzle.puzzle_size == puzzle_size,
            )
        )
    )
    if puzzle_difficulty:
        query = query.where(Puzzle.puzzle_difficulty == puzzle_difficulty)
    else:
        query = query.where(Puzzle.puzzle_difficulty == None)

    result = await db.execute(query)
    priority_puzzle_ids = [str(row[0]) for row in result.all()]

    if not priority_puzzle_ids:
        raise HTTPException(status_code=404, detail="No priority puzzles found for this group")

    admin_service = PuzzleAdminService(db)
    difficulties = [puzzle_difficulty] if puzzle_difficulty else None
    data = await admin_service.export_freeplay_data(
        puzzle_types=[puzzle_type], puzzle_sizes=[puzzle_size], puzzle_difficulties=difficulties,
        solved_filter="solved" if solved_only else None,
    )

    data = [a for a in data if a["puzzle"]["id"] in priority_puzzle_ids]
    if not data:
        raise HTTPException(status_code=404, detail="No attempts found for this priority group")

    diff_part = f"_{puzzle_difficulty}" if puzzle_difficulty else ""
    filename = f"priority_{puzzle_type}_{puzzle_size}{diff_part}_group_attempts.json"
    return JSONResponse(content=data, headers={"Content-Disposition": f"attachment; filename={filename}", "Content-Type": "application/json"})


@router.get("/admin/priority/{priority_id}/export")
async def export_priority_puzzle_attempts(
    priority_id: uuid.UUID,
    db: AsyncDatabase,
    _user: User = Depends(require_admin),
    solved_only: bool = Query(True),
):
    """export all attempts for a specific priority puzzle."""
    admin_service = PuzzleAdminService(db)
    puzzle = await admin_service.get_priority_puzzle_definition(priority_id)
    if not puzzle:
        raise HTTPException(status_code=404, detail=f"Priority record with id {priority_id} not found")

    data = await admin_service.export_freeplay_data(
        puzzle_types=[puzzle.puzzle_type], puzzle_sizes=[puzzle.puzzle_size],
        puzzle_difficulties=[puzzle.puzzle_difficulty] if puzzle.puzzle_difficulty else None,
        solved_filter="solved" if solved_only else None,
    )

    data = [a for a in data if a["puzzle"]["id"] == str(puzzle.id)]
    if not data:
        raise HTTPException(status_code=404, detail="No attempts found for this puzzle")

    filename = f"priority_{puzzle.puzzle_type}_{puzzle.puzzle_size}_{puzzle.id}_attempts.json"
    return JSONResponse(content=data, headers={"Content-Disposition": f"attachment; filename={filename}", "Content-Type": "application/json"})
