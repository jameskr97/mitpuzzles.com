"""CLI commands for game metrics analysis."""

import asyncio
from collections import defaultdict
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.dependencies import async_session_maker
from app.modules.puzzle.models import Puzzle, FreeplayPuzzleAttempt
from app.modules.puzzle.services.game_metrics import compute_game_metrics
from app.modules.puzzle.services.puzzle_metrics import compute_puzzle_metrics

app = typer.Typer(name="metrics", help="Game metrics analysis commands", no_args_is_help=True)
console = Console()


@app.command()
def analyze(
    puzzle_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by puzzle type"),
    solved_only: bool = typer.Option(False, "--solved", help="Only analyze solved attempts"),
    limit: int = typer.Option(0, "--limit", "-n", help="Max attempts to analyze (0 = all)"),
    attempt_id: Optional[str] = typer.Option(None, "--attempt", "-a", help="Analyze a single attempt by ID"),
):
    """Compute efficiency metrics across game attempts."""
    asyncio.run(_analyze_async(puzzle_type=puzzle_type, solved_only=solved_only, limit=limit, attempt_id=attempt_id))


async def _analyze_async(
    puzzle_type: Optional[str] = None,
    solved_only: bool = False,
    limit: int = 0,
    attempt_id: Optional[str] = None,
):
    async with async_session_maker() as db:
        query = (
            select(FreeplayPuzzleAttempt)
            .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
            .options(selectinload(FreeplayPuzzleAttempt.puzzle))
        )

        if attempt_id:
            import uuid
            query = query.where(FreeplayPuzzleAttempt.id == uuid.UUID(attempt_id))
        else:
            if puzzle_type:
                query = query.where(Puzzle.puzzle_type == puzzle_type)
            if solved_only:
                query = query.where(FreeplayPuzzleAttempt.is_solved == True)
            query = query.where(FreeplayPuzzleAttempt.action_history != None)
            query = query.order_by(FreeplayPuzzleAttempt.created_at.desc())
            if limit > 0:
                query = query.limit(limit)

        result = await db.execute(query)
        attempts = result.scalars().all()

        if not attempts:
            console.print("[yellow]No attempts found matching criteria.[/yellow]")
            return

        console.print(f"Analyzing {len(attempts)} attempts...\n")

        # single attempt: show detailed output
        if attempt_id and len(attempts) == 1:
            attempt = attempts[0]
            puzzle = attempt.puzzle
            puzzle_data = puzzle.puzzle_data

            initial_state = puzzle_data.get("initial_state", [])
            solution = puzzle_data.get("solution", [])

            if not solution:
                console.print("[red]Puzzle has no solution stored.[/red]")
                return

            metrics = compute_game_metrics(
                puzzle_type=puzzle.puzzle_type,
                initial_state=initial_state,
                solution=solution,
                action_history=attempt.action_history or [],
                is_solved=attempt.is_solved,
            )

            if "error" in metrics:
                console.print(f"[red]{metrics['error']}[/red]")
                return

            console.print(f"[bold]Attempt:[/bold] {attempt.id}")
            console.print(f"[bold]Puzzle:[/bold]  {puzzle.puzzle_type} {puzzle.puzzle_size} {puzzle.puzzle_difficulty or ''}")
            console.print(f"[bold]Solved:[/bold]  {attempt.is_solved}")
            console.print()

            detail_table = Table(show_header=True, header_style="bold magenta")
            detail_table.add_column("Metric", style="cyan")
            detail_table.add_column("Value", justify="right")

            detail_table.add_row("Min actions", str(metrics["min_actions"]))
            detail_table.add_row("Actual actions", str(metrics["actual_actions"]))
            detail_table.add_row("  Positive actions", str(metrics["positive_actions"]))
            detail_table.add_row("  Assist actions", str(metrics["assist_actions"]))
            detail_table.add_row("Efficiency (total)", f"{metrics['efficiency']:.1%}")
            detail_table.add_row("Efficiency (solve)", f"{metrics['solve_efficiency']:.1%}")
            detail_table.add_row("Mistakes", str(metrics["mistakes"]))
            detail_table.add_row("Corrections", str(metrics["corrections"]))
            detail_table.add_row("Cells changed >1x", str(metrics["cells_changed_multiple_times"]))
            detail_table.add_row("Wasted actions", str(metrics["wasted_actions"]))
            console.print(detail_table)

            if metrics["action_breakdown"]:
                console.print("\n[bold]Action breakdown:[/bold]")
                for action_type, count in sorted(metrics["action_breakdown"].items(), key=lambda x: -x[1]):
                    console.print(f"  {action_type}: {count}")
            return

        # bulk analysis: aggregate by puzzle type
        type_stats: dict[str, dict] = defaultdict(lambda: {
            "count": 0,
            "solved": 0,
            "skipped": 0,
            "total_min": 0,
            "total_actual": 0,
            "total_positive": 0,
            "total_assists": 0,
            "total_mistakes": 0,
            "total_corrections": 0,
            "total_multi_change": 0,
            "perfect_games": 0,
            "efficiencies": [],
            "solve_efficiencies": [],
        })

        analyzed = 0
        for attempt in attempts:
            puzzle = attempt.puzzle
            puzzle_data = puzzle.puzzle_data

            initial_state = puzzle_data.get("initial_state", [])
            solution = puzzle_data.get("solution", [])

            if not solution or not initial_state:
                type_stats[puzzle.puzzle_type]["skipped"] += 1
                continue

            metrics = compute_game_metrics(
                puzzle_type=puzzle.puzzle_type,
                initial_state=initial_state,
                solution=solution,
                action_history=attempt.action_history or [],
                is_solved=attempt.is_solved,
            )

            if "error" in metrics:
                type_stats[puzzle.puzzle_type]["skipped"] += 1
                continue

            stats = type_stats[puzzle.puzzle_type]
            stats["count"] += 1
            if attempt.is_solved:
                stats["solved"] += 1
            stats["total_min"] += metrics["min_actions"]
            stats["total_actual"] += metrics["actual_actions"]
            stats["total_positive"] += metrics["positive_actions"]
            stats["total_assists"] += metrics["assist_actions"]
            stats["total_mistakes"] += metrics["mistakes"]
            stats["total_corrections"] += metrics["corrections"]
            stats["total_multi_change"] += metrics["cells_changed_multiple_times"]
            if metrics["actual_actions"] > 0:
                stats["efficiencies"].append(metrics["efficiency"])
                stats["solve_efficiencies"].append(metrics["solve_efficiency"])
            if metrics["efficiency"] == 1.0 and metrics["actual_actions"] > 0:
                stats["perfect_games"] += 1

            analyzed += 1

        console.print(f"Analyzed {analyzed} attempts\n")

        # summary table
        summary = Table(show_header=True, header_style="bold magenta", title="Efficiency by Puzzle Type")
        summary.add_column("Type", style="cyan")
        summary.add_column("Games", justify="right")
        summary.add_column("Solved", justify="right")
        summary.add_column("Total Eff", justify="right")
        summary.add_column("Solve Eff", justify="right")
        summary.add_column("Perfect", justify="right")
        summary.add_column("Avg Assists", justify="right")
        summary.add_column("Avg Mistakes", justify="right")
        summary.add_column("Skipped", justify="right", style="yellow")

        for pt in sorted(type_stats.keys()):
            s = type_stats[pt]
            n = s["count"]
            if n == 0:
                summary.add_row(pt, "0", "0", "-", "-", "-", "-", "-", str(s["skipped"]))
                continue

            avg_eff = sum(s["efficiencies"]) / len(s["efficiencies"]) if s["efficiencies"] else 0
            avg_solve_eff = sum(s["solve_efficiencies"]) / len(s["solve_efficiencies"]) if s["solve_efficiencies"] else 0
            avg_assists = s["total_assists"] / n
            avg_mistakes = s["total_mistakes"] / n

            summary.add_row(
                pt,
                str(n),
                str(s["solved"]),
                f"{avg_eff:.1%}",
                f"{avg_solve_eff:.1%}",
                str(s["perfect_games"]),
                f"{avg_assists:.1f}",
                f"{avg_mistakes:.1f}",
                str(s["skipped"]),
            )

        console.print(summary)


@app.command()
def compute_puzzles(
    puzzle_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by puzzle type"),
    apply: bool = typer.Option(False, "--apply", help="Write metrics to database (default is dry-run)"),
):
    """Compute and store structural metrics on puzzle definitions."""
    asyncio.run(_compute_puzzles_async(puzzle_type=puzzle_type, apply=apply))


async def _compute_puzzles_async(puzzle_type: Optional[str] = None, apply: bool = False):
    BATCH_SIZE = 500

    async with async_session_maker() as db:
        query = select(Puzzle)
        if puzzle_type:
            query = query.where(Puzzle.puzzle_type == puzzle_type)

        result = await db.execute(query)
        puzzles = result.scalars().all()

        console.print(f"Processing {len(puzzles)} puzzles...\n")

        by_type: dict[str, dict] = defaultdict(lambda: {
            "total": 0, "computed": 0, "skipped": 0,
            "min_actions_sum": 0, "board_size_sum": 0,
            "solution_density_sum": 0.0,
        })

        to_update: list[tuple] = []  # (puzzle, metrics_dict)

        for puzzle in puzzles:
            stats = by_type[puzzle.puzzle_type]
            stats["total"] += 1

            metrics = compute_puzzle_metrics(puzzle.puzzle_type, puzzle.puzzle_data)
            if metrics is None:
                stats["skipped"] += 1
                continue

            stats["computed"] += 1
            stats["min_actions_sum"] += metrics["min_actions"]
            stats["board_size_sum"] += metrics["board_size"]
            stats["solution_density_sum"] += metrics["solution_density"]
            to_update.append((puzzle, metrics))

        # summary table
        summary = Table(show_header=True, header_style="bold magenta", title="Puzzle Metrics Summary")
        summary.add_column("Type", style="cyan")
        summary.add_column("Total", justify="right")
        summary.add_column("Computed", justify="right")
        summary.add_column("Avg Min Actions", justify="right")
        summary.add_column("Avg Board Size", justify="right")
        summary.add_column("Avg Sol Density", justify="right")
        summary.add_column("Skipped", justify="right", style="yellow")

        for pt in sorted(by_type.keys()):
            s = by_type[pt]
            n = s["computed"]
            if n == 0:
                summary.add_row(pt, str(s["total"]), "0", "-", "-", "-", str(s["skipped"]))
                continue

            summary.add_row(
                pt,
                str(s["total"]),
                str(n),
                f"{s['min_actions_sum'] / n:.1f}",
                f"{s['board_size_sum'] / n:.0f}",
                f"{s['solution_density_sum'] / n:.3f}",
                str(s["skipped"]),
            )

        console.print(summary)

        if not apply:
            console.print(f"\n[yellow]DRY RUN — {len(to_update)} puzzles would be updated. Use --apply to write.[/yellow]")
            return

        console.print(f"\n[cyan]Writing metrics to {len(to_update)} puzzles...[/cyan]")
        written = 0
        for i in range(0, len(to_update), BATCH_SIZE):
            batch = to_update[i : i + BATCH_SIZE]
            for puzzle, metrics in batch:
                puzzle.metrics = metrics
            await db.commit()
            written += len(batch)
            console.print(f"  {written}/{len(to_update)}")

        console.print(f"\n[green]Done. Wrote metrics to {written} puzzles.[/green]")


@app.command()
def backfill_attempts(
    puzzle_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by puzzle type"),
    apply: bool = typer.Option(False, "--apply", help="Write metrics to database (default is dry-run)"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Recompute even if metrics already exist"),
):
    """Backfill game metrics on existing freeplay attempts."""
    asyncio.run(_backfill_attempts_async(puzzle_type=puzzle_type, apply=apply, overwrite=overwrite))


async def _backfill_attempts_async(puzzle_type: Optional[str] = None, apply: bool = False, overwrite: bool = False):
    BATCH_SIZE = 500

    async with async_session_maker() as db:
        query = (
            select(FreeplayPuzzleAttempt)
            .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
            .options(selectinload(FreeplayPuzzleAttempt.puzzle))
        )
        if puzzle_type:
            query = query.where(Puzzle.puzzle_type == puzzle_type)
        if not overwrite:
            query = query.where(FreeplayPuzzleAttempt.metrics.is_(None))

        result = await db.execute(query)
        attempts = result.scalars().all()

        console.print(f"Processing {len(attempts)} attempts...\n")

        computed = 0
        skipped = 0
        by_type: dict[str, dict] = defaultdict(lambda: {"count": 0, "skipped": 0})

        for i, attempt in enumerate(attempts):
            puzzle = attempt.puzzle
            initial_state = puzzle.puzzle_data.get("initial_state") or puzzle.puzzle_data.get("game_state")
            solution = puzzle.puzzle_data.get("solution") or puzzle.puzzle_data.get("game_board")

            if not initial_state or not solution:
                skipped += 1
                by_type[puzzle.puzzle_type]["skipped"] += 1
                continue

            metrics = compute_game_metrics(
                puzzle_type=puzzle.puzzle_type,
                initial_state=initial_state,
                solution=solution,
                action_history=attempt.action_history or [],
                is_solved=attempt.is_solved,
            )

            if "error" in metrics:
                skipped += 1
                by_type[puzzle.puzzle_type]["skipped"] += 1
                continue

            if apply:
                attempt.metrics = metrics
            computed += 1
            by_type[puzzle.puzzle_type]["count"] += 1

            if apply and (i + 1) % BATCH_SIZE == 0:
                await db.commit()
                console.print(f"  {i + 1}/{len(attempts)}")

        if apply:
            await db.commit()

        # summary
        summary = Table(show_header=True, header_style="bold magenta", title="Attempt Metrics Backfill")
        summary.add_column("Type", style="cyan")
        summary.add_column("Computed", justify="right")
        summary.add_column("Skipped", justify="right", style="yellow")

        for pt in sorted(by_type.keys()):
            s = by_type[pt]
            summary.add_row(pt, str(s["count"]), str(s["skipped"]))

        console.print(summary)
        console.print(f"\nTotal: {computed} computed, {skipped} skipped")

        if not apply:
            console.print(f"\n[yellow]DRY RUN — {computed} attempts would be updated. Use --apply to write.[/yellow]")
        else:
            console.print(f"\n[green]Done. Wrote metrics to {computed} attempts.[/green]")
