"""CLI commands for user activity data."""

import asyncio
from collections import defaultdict
from datetime import datetime

import typer
from rich.console import Console
from sqlalchemy import select, func, case, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.dependencies import async_session_maker
from app.modules.puzzle.models import (
    Puzzle,
    FreeplayPuzzleAttempt,
    DailyPuzzle,
    DailyPuzzleAttempt,
    UserActivityDaily,
)

app = typer.Typer(name="activity", help="User activity management commands", no_args_is_help=True)
console = Console()

BATCH_SIZE = 500


async def _regenerate():
    async with async_session_maker() as db:
        # -- truncate --
        console.print("[yellow]Truncating user_activity_daily...[/yellow]")
        await db.execute(text("TRUNCATE TABLE user_activity_daily"))
        await db.commit()

        # -- aggregate freeplay attempts by (user_id, date, puzzle_type) --
        console.print("Querying freeplay attempts...")

        duration_expr = (
            FreeplayPuzzleAttempt.timestamp_finish - FreeplayPuzzleAttempt.timestamp_start
        ) / 1000.0

        query = (
            select(
                FreeplayPuzzleAttempt.user_id,
                func.date(func.to_timestamp(FreeplayPuzzleAttempt.timestamp_finish / 1000.0)).label("activity_date"),
                Puzzle.puzzle_type,
                func.count().label("attempted"),
                func.count().filter(FreeplayPuzzleAttempt.is_solved == True).label("solved"),
                func.min(
                    case(
                        (FreeplayPuzzleAttempt.is_solved == True, duration_expr),
                        else_=None,
                    )
                ).label("best_time"),
            )
            .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
            .where(
                FreeplayPuzzleAttempt.user_id.is_not(None),
                FreeplayPuzzleAttempt.timestamp_finish.is_not(None),
            )
            .group_by(
                FreeplayPuzzleAttempt.user_id,
                text("activity_date"),
                Puzzle.puzzle_type,
            )
        )

        result = await db.execute(query)
        freeplay_rows = result.all()
        console.print(f"  Found {len(freeplay_rows)} (user, date, type) groups")

        # -- aggregate daily attempts --
        console.print("Querying daily attempts...")

        daily_query = (
            select(
                DailyPuzzleAttempt.user_id,
                func.date(DailyPuzzle.puzzle_date).label("activity_date"),
                FreeplayPuzzleAttempt.is_solved,
                case(
                    (FreeplayPuzzleAttempt.is_solved == True, duration_expr),
                    else_=None,
                ).label("time"),
            )
            .join(DailyPuzzle, DailyPuzzleAttempt.daily_puzzle_id == DailyPuzzle.id)
            .join(FreeplayPuzzleAttempt, DailyPuzzleAttempt.attempt_id == FreeplayPuzzleAttempt.id)
            .where(
                DailyPuzzleAttempt.user_id.is_not(None),
                DailyPuzzleAttempt.attempt_id.is_not(None),
            )
        )

        daily_result = await db.execute(daily_query)
        daily_rows = daily_result.all()
        console.print(f"  Found {len(daily_rows)} daily attempts")

        # -- merge into (user_id, date) -> data dict --
        console.print("Building activity rows...")

        activity_map: dict[tuple, dict] = defaultdict(lambda: {"puzzles": {}})

        for row in freeplay_rows:
            key = (row.user_id, row.activity_date)
            entry = {
                "solved": row.solved,
                "attempted": row.attempted,
            }
            if row.best_time is not None:
                entry["best_time"] = round(row.best_time, 2)
            activity_map[key]["puzzles"][row.puzzle_type] = entry

        for row in daily_rows:
            key = (row.user_id, row.activity_date)
            daily_data = {"solved": bool(row.is_solved)}
            if row.time is not None:
                daily_data["time"] = round(row.time, 2)
            activity_map[key]["daily"] = daily_data

        console.print(f"  Built {len(activity_map)} activity rows")

        # -- insert in batches --
        rows_to_insert = [
            {
                "user_id": user_id,
                "activity_date": activity_date,
                "data": data,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            for (user_id, activity_date), data in activity_map.items()
        ]

        inserted = 0
        for i in range(0, len(rows_to_insert), BATCH_SIZE):
            batch = rows_to_insert[i : i + BATCH_SIZE]
            stmt = pg_insert(UserActivityDaily).values(batch)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_user_activity_daily",
                set_={"data": stmt.excluded.data, "updated_at": stmt.excluded.updated_at},
            )
            await db.execute(stmt)
            await db.commit()
            inserted += len(batch)
            console.print(f"  {inserted}/{len(rows_to_insert)}")

        console.print(f"[green]Done. Inserted {inserted} activity rows.[/green]")


@app.command()
def regenerate():
    """Truncate and rebuild user_activity_daily from attempt data."""
    typer.confirm("This will truncate user_activity_daily and rebuild from scratch. Continue?", abort=True)
    asyncio.run(_regenerate())
