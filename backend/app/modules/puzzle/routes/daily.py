import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy import select

from app.dependencies import AsyncDatabase, get_device_id
from app.modules.authentication import User, fastapi_users
from app.modules.puzzle.schemas import (
    PuzzleDefinitionResponse,
    FreeplayAttemptCreate,
    LeaderboardResponse,
)
from app.modules.puzzle.services import DailyPuzzleService, LeaderboardService
from app.modules.puzzle.formatting import format_puzzle_for_frontend
from app.modules.puzzle.models import Puzzle, DailyPuzzle

router = APIRouter()


@router.get("/daily/today")
async def get_daily_today(
    db: AsyncDatabase,
    device_id: uuid.UUID = Depends(get_device_id),
    user: Optional[User] = Depends(fastapi_users.current_user(optional=True)),
):
    """get today's daily puzzle status for this user/device."""
    service = DailyPuzzleService(db)
    today = datetime.now(timezone.utc)
    statuses = await service.get_daily_puzzle_status(today, user.id if user else None, device_id)
    return {"date": today.strftime("%Y-%m-%d"), "puzzles": statuses}


@router.get("/daily/{date}/definition/{puzzle_type}")
async def get_daily_definition(date: str, puzzle_type: str, db: AsyncDatabase):
    """get the puzzle definition for a specific daily puzzle."""
    try:
        puzzle_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    service = DailyPuzzleService(db)
    daily_puzzles = await service.get_or_create_daily_puzzles(puzzle_date)

    for dp in daily_puzzles:
        if dp.puzzle.puzzle_type == puzzle_type:
            return PuzzleDefinitionResponse.model_validate(format_puzzle_for_frontend(dp.puzzle))

    raise HTTPException(status_code=404, detail=f"No daily puzzle found for {puzzle_type} on {date}")


@router.get("/daily/{date}/leaderboard/{puzzle_type}", response_model=LeaderboardResponse)
async def get_daily_leaderboard(
    date: str,
    puzzle_type: str,
    db: AsyncDatabase,
    limit: int = Query(10, ge=1, le=100),
    user: Optional[User] = Depends(fastapi_users.current_user(optional=True)),
):
    """get leaderboard for a specific daily puzzle."""
    try:
        puzzle_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    puzzle_date = puzzle_date.replace(hour=0, minute=0, second=0, microsecond=0)

    daily_puzzle = await db.scalar(
        select(DailyPuzzle)
        .join(Puzzle, DailyPuzzle.puzzle_id == Puzzle.id)
        .where(DailyPuzzle.puzzle_date == puzzle_date, Puzzle.puzzle_type == puzzle_type)
    )
    if not daily_puzzle:
        raise HTTPException(status_code=404, detail=f"No daily puzzle found for {puzzle_type} on {date}")

    data = await LeaderboardService(db).get_daily_leaderboard(daily_puzzle.id, limit, user)
    return LeaderboardResponse.model_validate(data)


@router.post("/daily/{date}/submit/{puzzle_type}", status_code=201)
async def submit_daily_attempt(
    date: str,
    puzzle_type: str,
    attempt_data: FreeplayAttemptCreate,
    db: AsyncDatabase,
    device_id: uuid.UUID = Depends(get_device_id),
    user: Optional[User] = Depends(fastapi_users.current_user(optional=True)),
):
    """submit an attempt for a daily puzzle."""
    try:
        puzzle_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    return await DailyPuzzleService(db).submit_daily_attempt(puzzle_date, puzzle_type, device_id, user, attempt_data)
