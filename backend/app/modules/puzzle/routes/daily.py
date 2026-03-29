import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends

from app.dependencies import AsyncDatabase, get_device_id
from app.modules.authentication import User, fastapi_users
from app.modules.puzzle.schemas import (
    ErrorResponse,
    PuzzleDefinitionResponse,
    DailyTodayResponse,
    PuzzleSubmitResponse,
    FreeplayAttemptCreate,
    LeaderboardResponse,
)
from app.modules.puzzle.services import DailyPuzzleService, LeaderboardService
from app.modules.puzzle.formatting import format_puzzle_for_frontend

router = APIRouter()


@router.get("/daily/today", response_model=DailyTodayResponse, responses={400: {"model": ErrorResponse}})
async def get_daily_today(
    db: AsyncDatabase,
    device_id: uuid.UUID = Depends(get_device_id),
    user: Optional[User] = Depends(fastapi_users.current_user(optional=True)),
):
    """get today's daily puzzle status for this user/device."""
    service = DailyPuzzleService(db)
    today = datetime.now(timezone.utc).replace(tzinfo=None)
    status = await service.get_daily_puzzle_status(today, user.id if user else None, device_id)
    return {"date": today.strftime("%Y-%m-%d"), "puzzle": status}


@router.get("/daily/{date}/definition", responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
async def get_daily_definition(date: str, db: AsyncDatabase):
    """get the puzzle definition for a date's daily puzzle."""
    try:
        puzzle_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid date format. use YYYY-MM-DD.")

    service = DailyPuzzleService(db)
    daily_puzzle = await service.get_or_create_daily_puzzle(puzzle_date)
    return PuzzleDefinitionResponse.model_validate(format_puzzle_for_frontend(daily_puzzle.puzzle))


@router.get("/daily/{date}/leaderboard", response_model=LeaderboardResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
async def get_daily_leaderboard(
    date: str,
    db: AsyncDatabase,
    limit: int = Query(10, ge=1, le=100),
    user: Optional[User] = Depends(fastapi_users.current_user(optional=True)),
):
    """get leaderboard for a date's daily puzzle."""
    try:
        puzzle_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid date format. use YYYY-MM-DD.")

    service = DailyPuzzleService(db)
    daily_puzzle = await service.get_or_create_daily_puzzle(puzzle_date)

    data = await LeaderboardService(db).get_daily_leaderboard(daily_puzzle.id, limit, user)
    return LeaderboardResponse.model_validate(data)


@router.post("/daily/{date}/submit", status_code=201, response_model=PuzzleSubmitResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
async def submit_daily_attempt(
    date: str,
    attempt_data: FreeplayAttemptCreate,
    db: AsyncDatabase,
    device_id: uuid.UUID = Depends(get_device_id),
    user: Optional[User] = Depends(fastapi_users.current_user(optional=True)),
):
    """submit an attempt for a date's daily puzzle."""
    try:
        puzzle_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid date format. use YYYY-MM-DD.")

    return await DailyPuzzleService(db).submit_daily_attempt(puzzle_date, device_id, user, attempt_data)
