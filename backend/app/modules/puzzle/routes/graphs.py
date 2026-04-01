import uuid
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy import select, func, and_, cast, Float

from app.dependencies import AsyncDatabase
from app.modules.authentication import User
from app.modules.puzzle.models import Puzzle, FreeplayPuzzleAttempt
from app.modules.puzzle.routes.dependencies import require_admin
from app.modules.puzzle.schemas import RecentGameEntry

router = APIRouter(prefix="/graphs")


@router.get("/puzzle-heatmap")
async def get_puzzle_heatmap(
    db: AsyncDatabase,
    user: User = Depends(require_admin),
    has_attempts: bool = Query(False),
    completed_only: bool = Query(False),
):
    """play counts for every active puzzle, for heatmap visualization."""
    join_condition = FreeplayPuzzleAttempt.puzzle_id == Puzzle.id
    if completed_only:
        join_condition = (join_condition) & (FreeplayPuzzleAttempt.timestamp_finish.is_not(None))

    query = (
        select(
            Puzzle.id,
            Puzzle.puzzle_type,
            Puzzle.puzzle_size,
            Puzzle.puzzle_difficulty,
            func.count(FreeplayPuzzleAttempt.id).label("play_count"),
        )
        .outerjoin(FreeplayPuzzleAttempt, join_condition)
        .where(Puzzle.is_active == True)
        .group_by(Puzzle.id, Puzzle.puzzle_type, Puzzle.puzzle_size, Puzzle.puzzle_difficulty)
    )
    if has_attempts:
        query = query.having(func.count(FreeplayPuzzleAttempt.id) > 0)
    query = query.order_by(Puzzle.puzzle_type, Puzzle.puzzle_size, Puzzle.puzzle_difficulty, func.count(FreeplayPuzzleAttempt.id).desc())

    result = await db.execute(query)
    return [
        {
            "id": str(r.id),
            "puzzle_type": r.puzzle_type,
            "puzzle_size": r.puzzle_size,
            "puzzle_difficulty": r.puzzle_difficulty,
            "play_count": r.play_count,
        }
        for r in result.all()
    ]


@router.get("/recent-games", response_model=List[RecentGameEntry])
async def get_recent_games(
    db: AsyncDatabase,
    user: User = Depends(require_admin),
    limit: int = Query(5, ge=1, le=50),
):
    """most recently played games with board state and player info."""
    from sqlalchemy.orm import selectinload
    from app.modules.puzzle.formatting import format_puzzle_for_frontend
    from app.modules.puzzle.schemas import PuzzleDefinitionResponse

    query = (
        select(FreeplayPuzzleAttempt)
        .options(selectinload(FreeplayPuzzleAttempt.puzzle), selectinload(FreeplayPuzzleAttempt.user))
        .where(FreeplayPuzzleAttempt.timestamp_finish.is_not(None))
        .order_by(FreeplayPuzzleAttempt.timestamp_finish.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    attempts = result.scalars().all()

    return [
        {
            "attempt_id": str(a.id),
            "puzzle_id": str(a.puzzle_id),
            "puzzle_type": a.puzzle.puzzle_type,
            "puzzle_size": a.puzzle.puzzle_size,
            "puzzle_difficulty": a.puzzle.puzzle_difficulty,
            "board_state": a.board_state,
            "is_solved": a.is_solved,
            "username": a.user.username if a.user else None,
            "time": round((a.timestamp_finish - a.timestamp_start) / 1000.0, 2) if a.timestamp_start else None,
            "metrics": a.metrics,
            "definition": PuzzleDefinitionResponse.model_validate(format_puzzle_for_frontend(a.puzzle)),
        }
        for a in attempts
    ]


@router.get("/puzzle/{puzzle_id}/click-order")
async def get_click_order_heatmap(
    db: AsyncDatabase,
    puzzle_id: uuid.UUID,
    user: User = Depends(require_admin),
):
    """average click order per cell across all solved attempts for a puzzle."""
    puzzle = await db.scalar(select(Puzzle).where(Puzzle.id == puzzle_id))
    if not puzzle:
        raise HTTPException(status_code=404, detail="puzzle not found")

    rows_count = puzzle.puzzle_data.get("rows", 0)
    cols_count = puzzle.puzzle_data.get("cols", 0)

    query = (
        select(FreeplayPuzzleAttempt.action_history)
        .where(
            FreeplayPuzzleAttempt.puzzle_id == puzzle_id,
            FreeplayPuzzleAttempt.is_solved == True,
            FreeplayPuzzleAttempt.timestamp_finish.is_not(None),
        )
    )
    result = await db.execute(query)
    all_histories = [row.action_history for row in result.all() if row.action_history]

    if not all_histories:
        return {"rows": rows_count, "cols": cols_count, "heatmap": [], "attempt_count": 0}

    CELL_ACTIONS = {"cell_click", "click", "cell_keypress", "keypress"}
    cell_ranks: dict[str, list[int]] = {}

    for history in all_histories:
        seen = set()
        rank = 0
        for action in history:
            action_type = action.get("action", "")
            if action_type not in CELL_ACTIONS:
                continue
            cell = action.get("cell")
            if not cell:
                continue
            r, c = cell.get("row"), cell.get("col")
            if r is None or c is None:
                continue
            key = f"{r},{c}"
            if key in seen:
                continue
            seen.add(key)
            rank += 1
            cell_ranks.setdefault(key, []).append(rank)

    heatmap = []
    for r in range(rows_count):
        row = []
        for c in range(cols_count):
            key = f"{r},{c}"
            ranks = cell_ranks.get(key, [])
            avg = round(sum(ranks) / len(ranks), 2) if ranks else None
            row.append(avg)
        heatmap.append(row)

    return {
        "rows": rows_count,
        "cols": cols_count,
        "heatmap": heatmap,
        "attempt_count": len(all_histories),
    }


@router.get("/class-metrics")
async def get_class_metrics(
    db: AsyncDatabase,
    puzzle_type: str = Query(...),
    puzzle_size: Optional[str] = Query(None),
    puzzle_difficulty: Optional[str] = Query(None),
):
    """aggregate metrics across all solved attempts for a puzzle class."""
    m = FreeplayPuzzleAttempt.metrics

    conditions = [
        Puzzle.puzzle_type == puzzle_type,
        FreeplayPuzzleAttempt.is_solved == True,
        m.is_not(None),
    ]
    if puzzle_size:
        conditions.append(Puzzle.puzzle_size == puzzle_size)
    if puzzle_difficulty:
        conditions.append(Puzzle.puzzle_difficulty == puzzle_difficulty)

    def jsonb_float(key: str):
        return cast(m[key].as_string(), Float)

    query = (
        select(
            func.count().label("total"),
            func.avg(jsonb_float("efficiency")).label("avg_efficiency"),
            func.avg(jsonb_float("solve_efficiency")).label("avg_solve_efficiency"),
            func.avg(jsonb_float("mistakes")).label("avg_mistakes"),
            func.avg(jsonb_float("corrections")).label("avg_corrections"),
            func.avg(jsonb_float("assist_actions")).label("avg_assists"),
            func.avg(jsonb_float("actual_actions")).label("avg_actual_actions"),
            func.avg(jsonb_float("min_actions")).label("avg_min_actions"),
            func.count().filter(jsonb_float("efficiency") >= 1.0).label("perfect_count"),
        )
        .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
        .where(and_(*conditions))
    )
    row = (await db.execute(query)).one()

    if not row.total:
        return {"puzzle_type": puzzle_type, "total": 0}

    return {
        "puzzle_type": puzzle_type,
        "puzzle_size": puzzle_size,
        "puzzle_difficulty": puzzle_difficulty,
        "total": row.total,
        "avg_efficiency": round(row.avg_efficiency, 4) if row.avg_efficiency else 0,
        "avg_solve_efficiency": round(row.avg_solve_efficiency, 4) if row.avg_solve_efficiency else 0,
        "avg_mistakes": round(row.avg_mistakes, 2) if row.avg_mistakes else 0,
        "avg_corrections": round(row.avg_corrections, 2) if row.avg_corrections else 0,
        "avg_assists": round(row.avg_assists, 2) if row.avg_assists else 0,
        "avg_actual_actions": round(row.avg_actual_actions, 2) if row.avg_actual_actions else 0,
        "avg_min_actions": round(row.avg_min_actions, 2) if row.avg_min_actions else 0,
        "perfect_count": row.perfect_count,
        "perfect_rate": round(100 * row.perfect_count / row.total, 1),
    }


@router.get("/min-actions-distribution")
async def get_min_actions_distribution(
    db: AsyncDatabase,
    puzzle_type: Optional[str] = Query(None),
    puzzle_size: Optional[str] = Query(None),
    puzzle_difficulty: Optional[str] = Query(None),
):
    """min_actions values for puzzles, optionally filtered by category."""
    conditions = [
        Puzzle.is_active == True,
        Puzzle.metrics.is_not(None),
    ]
    if puzzle_type:
        conditions.append(Puzzle.puzzle_type == puzzle_type)
    if puzzle_size:
        conditions.append(Puzzle.puzzle_size == puzzle_size)
    if puzzle_difficulty:
        conditions.append(Puzzle.puzzle_difficulty == puzzle_difficulty)

    query = (
        select(
            Puzzle.puzzle_type,
            cast(Puzzle.metrics["min_actions"].as_string(), Float).label("min_actions"),
        )
        .where(and_(*conditions))
    )
    result = await db.execute(query)
    rows = result.all()

    values = [{"puzzle_type": row.puzzle_type, "min_actions": int(row.min_actions)} for row in rows if row.min_actions is not None]

    return {
        "puzzle_type": puzzle_type,
        "puzzle_size": puzzle_size,
        "puzzle_difficulty": puzzle_difficulty,
        "values": values,
    }


@router.get("/difficulty-vs-min-actions")
async def get_difficulty_vs_min_actions(
    db: AsyncDatabase,
    puzzle_type: Optional[str] = Query(None),
    puzzle_size: Optional[str] = Query(None),
    puzzle_difficulty: Optional[str] = Query(None),
):
    """difficulty score vs min_actions for scatter plot."""
    conditions = [
        Puzzle.is_active == True,
        Puzzle.metrics.is_not(None),
        Puzzle.puzzle_data["difficulty_value"] != None,
    ]
    if puzzle_type:
        conditions.append(Puzzle.puzzle_type == puzzle_type)
    if puzzle_size:
        conditions.append(Puzzle.puzzle_size == puzzle_size)
    if puzzle_difficulty:
        conditions.append(Puzzle.puzzle_difficulty == puzzle_difficulty)

    query = (
        select(
            Puzzle.puzzle_type,
            Puzzle.metrics["min_actions"].label("min_actions"),
            Puzzle.puzzle_data["difficulty_value"].label("difficulty"),
        )
        .where(and_(*conditions))
    )
    result = await db.execute(query)

    points = [
        {"puzzle_type": row.puzzle_type, "min_actions": int(float(row.min_actions)), "difficulty": round(float(row.difficulty), 4)}
        for row in result.all()
        if row.min_actions is not None and row.difficulty is not None
    ]

    return {"points": points}


@router.get("/mistake-counts")
async def get_mistake_counts(
    db: AsyncDatabase,
    puzzle_type: str = Query(...),
    puzzle_size: Optional[str] = Query(None),
    puzzle_difficulty: Optional[str] = Query(None),
):
    """mistake counts for solved attempts in a puzzle category."""
    conditions = [
        Puzzle.puzzle_type == puzzle_type,
        FreeplayPuzzleAttempt.is_solved == True,
        FreeplayPuzzleAttempt.metrics.is_not(None),
    ]
    if puzzle_size:
        conditions.append(Puzzle.puzzle_size == puzzle_size)
    if puzzle_difficulty:
        conditions.append(Puzzle.puzzle_difficulty == puzzle_difficulty)

    query = (
        select(FreeplayPuzzleAttempt.metrics)
        .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
        .where(and_(*conditions))
    )
    result = await db.execute(query)

    mistakes = [m["mistakes"] for row in result.all() if (m := row.metrics) and "mistakes" in m]

    return {
        "puzzle_type": puzzle_type,
        "puzzle_size": puzzle_size,
        "puzzle_difficulty": puzzle_difficulty,
        "mistakes": mistakes,
    }


@router.get("/action-counts")
async def get_action_counts(
    db: AsyncDatabase,
    puzzle_type: str = Query(...),
    puzzle_size: Optional[str] = Query(None),
    puzzle_difficulty: Optional[str] = Query(None),
):
    """action counts for solved attempts in a puzzle category."""
    conditions = [
        Puzzle.puzzle_type == puzzle_type,
        FreeplayPuzzleAttempt.is_solved == True,
        FreeplayPuzzleAttempt.metrics.is_not(None),
    ]
    if puzzle_size:
        conditions.append(Puzzle.puzzle_size == puzzle_size)
    if puzzle_difficulty:
        conditions.append(Puzzle.puzzle_difficulty == puzzle_difficulty)

    query = (
        select(FreeplayPuzzleAttempt.metrics)
        .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
        .where(and_(*conditions))
    )
    result = await db.execute(query)

    actions = []
    min_actions_set = set()
    for row in result.all():
        m = row.metrics
        if m and m.get("actual_actions"):
            actions.append(m["actual_actions"])
            if m.get("min_actions"):
                min_actions_set.add(m["min_actions"])

    min_actions = max(min_actions_set, key=lambda x: list(min_actions_set).count(x)) if min_actions_set else None

    return {
        "puzzle_type": puzzle_type,
        "puzzle_size": puzzle_size,
        "puzzle_difficulty": puzzle_difficulty,
        "actions": actions,
        "min_actions": min_actions,
    }


@router.get("/solve-times")
async def get_solve_times(
    db: AsyncDatabase,
    puzzle_type: str = Query(...),
    puzzle_size: Optional[str] = Query(None),
    puzzle_difficulty: Optional[str] = Query(None),
):
    """all solve times for a puzzle category."""
    duration_expr = (FreeplayPuzzleAttempt.timestamp_finish - FreeplayPuzzleAttempt.timestamp_start) / 1000.0

    conditions = [
        Puzzle.puzzle_type == puzzle_type,
        FreeplayPuzzleAttempt.is_solved == True,
        FreeplayPuzzleAttempt.timestamp_finish.is_not(None),
        FreeplayPuzzleAttempt.timestamp_start.is_not(None),
    ]
    if puzzle_size:
        conditions.append(Puzzle.puzzle_size == puzzle_size)
    if puzzle_difficulty:
        conditions.append(Puzzle.puzzle_difficulty == puzzle_difficulty)

    query = (
        select(duration_expr.label("time"))
        .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
        .where(and_(*conditions))
    )
    result = await db.execute(query)
    times = [round(row.time, 2) for row in result.all() if row.time and 1 < row.time < 3600]

    return {"puzzle_type": puzzle_type, "puzzle_size": puzzle_size, "puzzle_difficulty": puzzle_difficulty, "times": times}
