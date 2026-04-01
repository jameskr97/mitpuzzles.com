"""
puzzle import and update commands with semantic ID support.
handles normalized puzzle data with deduplication.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from app.dependencies import async_session_maker
from app.modules.puzzle import Puzzle, PuzzlePriority
from cli.normalizer import PuzzleNormalizer

app = typer.Typer(name="puzzle-import", help="Puzzle import and update commands", no_args_is_help=True)
console = Console()


async def _load_and_normalize_puzzles(path: Path) -> List[Dict[str, Any]]:
    """Load and normalize puzzles from a file or directory."""
    normalizer = PuzzleNormalizer()
    all_puzzles = {}

    if path.is_file():
        # Single file
        with open(path, "r") as f:
            data = json.load(f)
            if isinstance(data, dict):
                all_puzzles = data
            else:
                # If it's a list, use filename as key
                all_puzzles[path.stem] = data
    else:
        # Directory of files
        for json_file in path.glob("*.json"):
            with open(json_file, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_puzzles[json_file.stem] = data
                elif isinstance(data, dict):
                    # If dict, assume it's already in the right format
                    all_puzzles.update(data)

    # Normalize all puzzles
    unique_puzzles, duplicates = normalizer.process_all_puzzles(all_puzzles)

    if duplicates:
        console.print(f"[yellow]Found {len(duplicates)} duplicates within the import data[/yellow]")

    return unique_puzzles


async def _merge_puzzle_data(existing_data: Dict, new_data: Dict, strategy: str = "update") -> Dict:
    """
    merge new puzzle data with existing data.

    strategies:
    - 'update': New data overwrites existing (default)
    - 'preserve': Existing data takes precedence
    - 'merge': Deep merge, keeping all fields
    """
    if strategy == "update":
        return {**existing_data, **new_data}
    elif strategy == "preserve":
        return {**new_data, **existing_data}
    elif strategy == "merge":
        result = existing_data.copy()
        for key, value in new_data.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = await _merge_puzzle_data(result[key], value, "merge")
            elif key not in result:
                result[key] = value
        return result
    else:
        raise ValueError(f"Unknown merge strategy: {strategy}")


@app.command()
def import_normalized(
    path: Path = typer.Argument(..., help="Path to JSON file or directory"),
    merge_strategy: str = typer.Option("update", "--merge", help="Merge strategy: update/preserve/merge"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without saving"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Show detailed output"),
):
    """
    import normalized puzzles with semantic ids.

    this command:
    - loads puzzles from JSON files
    - normalizes them (generates semantic IDs)
    - detects duplicates using complete_id
    - updates existing puzzles or inserts new ones
    """
    asyncio.run(_import_normalized_async(path, merge_strategy, dry_run, verbose))


async def _import_normalized_async(path: Path, merge_strategy: str, dry_run: bool, verbose: bool):
    """Async implementation of import_normalized."""

    if not path.exists():
        console.print(f"[red]Error: Path {path} does not exist[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Loading puzzles from {path}...[/green]")

    # Load and normalize puzzles
    try:
        normalized_puzzles = await _load_and_normalize_puzzles(path)
    except Exception as e:
        console.print(f"[red]Error normalizing puzzles: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Normalized {len(normalized_puzzles)} unique puzzles[/green]")

    stats = {"updated": 0, "inserted": 0, "unchanged": 0, "errors": 0}

    async with async_session_maker() as session:
        for puzzle_data in normalized_puzzles:
            complete_id = puzzle_data["complete_id"]
            existing = await session.scalar(select(Puzzle).where(Puzzle.complete_id == complete_id)) # check if exists

            if existing:
                # do puzzle data merge
                existing_data = existing.puzzle_data
                merged_data = await _merge_puzzle_data(existing_data, puzzle_data, merge_strategy)

                # check if data is different
                if merged_data != existing_data:
                    if verbose:
                        console.print(f"  Updating puzzle {complete_id[:8]}...")

                    # do data merge
                    if not dry_run:
                        existing.puzzle_data = merged_data
                        existing.updated_at = datetime.utcnow()

                        # update semantic IDs if they changed (shouldn't happen but safety check)
                        existing.definition_id = puzzle_data["definition_id"]
                        existing.solution_id = puzzle_data["solution_id"]

                        # update metadata
                        existing.puzzle_type = puzzle_data["puzzle_type"]
                        existing.puzzle_size = puzzle_data["puzzle_size"]
                        existing.puzzle_difficulty = puzzle_data.get("difficulty_label", None)

                    stats["updated"] += 1
                else:
                    stats["unchanged"] += 1
                    if verbose:
                        console.print(f"  Puzzle {complete_id[:8]}... unchanged")
                continue
            
            # invariant - this is a new puzzle
            if verbose:
                console.print(f"  Inserting new puzzle {complete_id[:8]}...")

            if not dry_run:
                new_puzzle = Puzzle(
                    complete_id=complete_id,
                    definition_id=puzzle_data["definition_id"],
                    solution_id=puzzle_data["solution_id"],
                    puzzle_type=puzzle_data["puzzle_type"],
                    puzzle_size=puzzle_data["puzzle_size"],
                    puzzle_difficulty=puzzle_data.get("difficulty_label", None),
                    puzzle_data=puzzle_data,
                )
                session.add(new_puzzle)

            stats["inserted"] += 1

        if not dry_run:
            try:
                await session.commit()
                console.print("[green]Changes committed to database[/green]")
            except IntegrityError as e:
                await session.rollback()
                console.print(f"[red]Database error: {e}[/red]")
                stats["errors"] += 1
        else:
            console.print("[yellow]DRY RUN - No changes made[/yellow]")

    # Print summary
    console.print("\n" + "=" * 60)
    console.print("Import Summary")
    console.print("=" * 60)

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Action", style="cyan")
    table.add_column("Count", justify="right")

    table.add_row("Updated", str(stats["updated"]))
    table.add_row("Inserted", str(stats["inserted"]))
    table.add_row("Unchanged", str(stats["unchanged"]))
    table.add_row("Errors", str(stats["errors"]))

    console.print(table)


@app.command()
def check_duplicates():
    """
    check for various types of duplicates in the database.

    Finds:
    - puzzles with same definition_id (should have same solution)
    - puzzles with same solution_id (variants)
    - any data inconsistencies
    """
    asyncio.run(_check_duplicates_async())


async def _check_duplicates_async():
    """Async implementation of check_duplicates."""

    async with async_session_maker() as session:
        # Check for puzzles with same definition but different solutions (shouldn't happen)
        result = await session.execute(
            select(Puzzle.puzzle_type, Puzzle.definition_id, func.count(func.distinct(Puzzle.solution_id)).label("solution_count"))
            .group_by(Puzzle.puzzle_type, Puzzle.definition_id)
            .having(func.count(func.distinct(Puzzle.solution_id)) > 1)
        )

        ambiguous = result.all()
        if ambiguous:
            console.print("[red]⚠️  CRITICAL: Found ambiguous puzzles![/red]")
            for puzzle_type, def_id, count in ambiguous:
                console.print(f"  {puzzle_type}: definition {def_id[:8]}... has {count} different solutions!")
        else:
            console.print("[green]✓ No ambiguous puzzles found[/green]")

        # Count variants (same solution)
        result = await session.execute(
            select(
                Puzzle.puzzle_type, func.count(func.distinct(Puzzle.solution_id)).label("unique_solutions"), func.count(Puzzle.id).label("total_puzzles")
            ).group_by(Puzzle.puzzle_type)
        )

        console.print("\n[bold]Puzzle Statistics:[/bold]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Type", style="cyan")
        table.add_column("Total", justify="right")
        table.add_column("Unique Solutions", justify="right")
        table.add_column("Avg Variants", justify="right")

        for row in result.all():
            puzzle_type, unique_sols, total = row
            avg_variants = total / unique_sols if unique_sols > 0 else 0
            table.add_row(puzzle_type, str(total), str(unique_sols), f"{avg_variants:.1f}")

        console.print(table)


@app.command()
def export(
    output: Path = typer.Option("puzzles_export.json", "-o", "--output", help="Output file"),
    puzzle_type: Optional[str] = typer.Option(None, "--type", help="Filter by puzzle type"),
    include_ids: bool = typer.Option(False, "--include-ids", help="Include semantic IDs"),
):
    """Export puzzles for review or backup."""
    asyncio.run(_export_async(output, puzzle_type, include_ids))


async def _export_async(output: Path, puzzle_type: Optional[str], include_ids: bool):
    """Async implementation of export."""

    async with async_session_maker() as session:
        query = select(Puzzle)
        if puzzle_type:
            query = query.where(Puzzle.puzzle_type == puzzle_type)

        result = await session.execute(query)
        puzzles = result.scalars().all()

        export_data = {}
        for puzzle in puzzles:
            key = f"{puzzle.puzzle_type}_{puzzle.puzzle_size}_{puzzle.puzzle_difficulty}"

            if key not in export_data:
                export_data[key] = []

            puzzle_export = puzzle.puzzle_data.copy()

            if include_ids:
                puzzle_export["_complete_id"] = puzzle.complete_id
                puzzle_export["_definition_id"] = puzzle.definition_id
                puzzle_export["_solution_id"] = puzzle.solution_id

            export_data[key].append(puzzle_export)

        with open(output, "w") as f:
            json.dump(export_data, f, indent=2, default=str)

        total = sum(len(v) for v in export_data.values())
        console.print(f"[green]Exported {total} puzzles to {output}[/green]")


@app.command()
def check_priority_coverage(
    fix: bool = typer.Option(False, "--fix", help="Add a random puzzle as priority for each missing combination"),
    count: int = typer.Option(50, "--count", "-n", help="Number of priority puzzles to add per missing combination (with --fix)"),
):
    """
    Check if every puzzle type+size+difficulty combination has priority puzzles.

    Reports:
    - Combinations with no priority puzzles (missing)
    - Combinations with priority puzzles (covered)
    - Summary statistics

    Use --fix to automatically add priority puzzles for missing combinations.
    """
    asyncio.run(_check_priority_coverage_async(fix=fix, count=count))


async def _check_priority_coverage_async(fix: bool = False, count: int = 1):
    """Async implementation of check_priority_coverage."""
    from sqlalchemy import and_
    from datetime import datetime

    async with async_session_maker() as session:
        # Get all unique puzzle combinations
        combinations_query = (
            select(
                Puzzle.puzzle_type,
                Puzzle.puzzle_size,
                Puzzle.puzzle_difficulty,
                func.count(Puzzle.id).label("total_puzzles")
            )
            .group_by(Puzzle.puzzle_type, Puzzle.puzzle_size, Puzzle.puzzle_difficulty)
            .order_by(Puzzle.puzzle_type, Puzzle.puzzle_size, Puzzle.puzzle_difficulty)
        )
        result = await session.execute(combinations_query)
        all_combinations = result.all()

        # Get combinations that have active priority puzzles
        priority_combinations_query = (
            select(
                Puzzle.puzzle_type,
                Puzzle.puzzle_size,
                Puzzle.puzzle_difficulty,
                func.count(PuzzlePriority.id).label("priority_count")
            )
            .join(PuzzlePriority, PuzzlePriority.puzzle_id == Puzzle.id)
            .where(PuzzlePriority.removed_at == None)
            .group_by(Puzzle.puzzle_type, Puzzle.puzzle_size, Puzzle.puzzle_difficulty)
        )
        priority_result = await session.execute(priority_combinations_query)
        priority_combinations = {
            (row.puzzle_type, row.puzzle_size, row.puzzle_difficulty): row.priority_count
            for row in priority_result.all()
        }

        # Build results
        missing = []
        covered = []

        for row in all_combinations:
            key = (row.puzzle_type, row.puzzle_size, row.puzzle_difficulty)
            priority_count = priority_combinations.get(key, 0)

            entry = {
                "puzzle_type": row.puzzle_type,
                "puzzle_size": row.puzzle_size,
                "puzzle_difficulty": row.puzzle_difficulty,
                "puzzle_difficulty_display": row.puzzle_difficulty or "(none)",
                "total_puzzles": row.total_puzzles,
                "priority_count": priority_count,
            }

            if priority_count == 0:
                missing.append(entry)
            else:
                covered.append(entry)

        # Print missing combinations
        if missing:
            console.print("\n[red bold]Missing Priority Puzzles:[/red bold]")
            missing_table = Table(show_header=True, header_style="bold red")
            missing_table.add_column("Type", style="cyan")
            missing_table.add_column("Size", justify="center")
            missing_table.add_column("Difficulty", justify="center")
            missing_table.add_column("Total Puzzles", justify="right")

            for entry in missing:
                missing_table.add_row(
                    entry["puzzle_type"],
                    entry["puzzle_size"],
                    entry["puzzle_difficulty_display"],
                    str(entry["total_puzzles"]),
                )
            console.print(missing_table)
        else:
            console.print("\n[green]All combinations have priority puzzles.[/green]")

        # Print covered combinations
        if covered:
            console.print("\n[green bold]Covered Combinations:[/green bold]")
            covered_table = Table(show_header=True, header_style="bold green")
            covered_table.add_column("Type", style="cyan")
            covered_table.add_column("Size", justify="center")
            covered_table.add_column("Difficulty", justify="center")
            covered_table.add_column("Total Puzzles", justify="right")
            covered_table.add_column("Priority Count", justify="right", style="green")

            for entry in covered:
                covered_table.add_row(
                    entry["puzzle_type"],
                    entry["puzzle_size"],
                    entry["puzzle_difficulty_display"],
                    str(entry["total_puzzles"]),
                    str(entry["priority_count"]),
                )
            console.print(covered_table)

        # Print summary
        console.print("\n" + "=" * 60)
        console.print("[bold]SUMMARY[/bold]")
        console.print("=" * 60)
        console.print(f"Total combinations: {len(all_combinations)}")
        console.print(f"[green]Covered: {len(covered)}[/green]")
        console.print(f"[red]Missing: {len(missing)}[/red]")

        # Handle --fix option
        if missing and not fix:
            console.print(f"\n[yellow]Run with --fix to add priority puzzles for missing combinations[/yellow]")
        elif missing and fix:
            console.print(f"\n[cyan]Adding {count} priority puzzle(s) per missing combination...[/cyan]")

            added_count = 0
            for entry in missing:
                # Get random puzzles for this combination
                puzzle_query = (
                    select(Puzzle)
                    .where(Puzzle.puzzle_type == entry["puzzle_type"])
                    .where(Puzzle.puzzle_size == entry["puzzle_size"])
                )
                if entry["puzzle_difficulty"] is not None:
                    puzzle_query = puzzle_query.where(Puzzle.puzzle_difficulty == entry["puzzle_difficulty"])
                else:
                    puzzle_query = puzzle_query.where(Puzzle.puzzle_difficulty == None)

                puzzle_query = puzzle_query.order_by(func.random()).limit(count)
                puzzles_result = await session.execute(puzzle_query)
                puzzles = puzzles_result.scalars().all()

                for puzzle in puzzles:
                    # Check if already has active priority (shouldn't happen but safety check)
                    existing_query = select(PuzzlePriority).where(
                        and_(
                            PuzzlePriority.puzzle_id == puzzle.id,
                            PuzzlePriority.removed_at == None
                        )
                    )
                    existing = await session.scalar(existing_query)
                    if existing:
                        continue

                    # Add to priority
                    priority = PuzzlePriority(
                        puzzle_id=puzzle.id,
                        added_at=datetime.utcnow()
                    )
                    session.add(priority)
                    added_count += 1

                    console.print(f"  [green]Added priority:[/green] {entry['puzzle_type']} {entry['puzzle_size']} {entry['puzzle_difficulty_display']} - puzzle {puzzle.id}")

            await session.commit()
            console.print(f"\n[green]Successfully added {added_count} priority puzzle(s)[/green]")


@app.command()
def normalize_format(
    apply: bool = typer.Option(False, "--apply", help="Actually update the database (default is dry-run)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show sample values from each category for verification"),
):
    """
    check which freeplay attempts use the old developer-format and report stats.

    by default runs as dry-run showing what would change. Use --apply to update.
    Use --verbose to see sample data from each category for manual verification.
    """
    asyncio.run(_normalize_format_async(apply=apply, verbose=verbose))


async def _normalize_format_async(apply: bool = False, verbose: bool = False):
    """scan all freeplay attempts and report/fix format inconsistencies."""
    from app.modules.puzzle.models import FreeplayPuzzleAttempt
    from app.modules.puzzle.utils import is_research_format
    from app.service.encoder import ResearchFormatTranslator
    from collections import defaultdict

    BATCH_SIZE = 500

    async with async_session_maker() as session:
        # count total attempts
        total_count = await session.scalar(select(func.count(FreeplayPuzzleAttempt.id)))
        console.print(f"Total attempts: {total_count}")

        # fetch all attempts with their puzzle type (need the join)
        query = (
            select(
                FreeplayPuzzleAttempt.id,
                FreeplayPuzzleAttempt.board_state,
                FreeplayPuzzleAttempt.action_history,
                Puzzle.puzzle_type,
            )
            .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
        )
        result = await session.execute(query)
        rows = result.all()

        # categorize
        already_research = 0
        needs_conversion = 0
        no_data = 0
        unknown_type = 0
        by_type: dict[str, dict[str, int]] = defaultdict(lambda: {"research": 0, "developer": 0, "no_data": 0})

        conversion_ids: list[tuple] = []  # (id, puzzle_type)

        # samples for verbose output
        samples: dict[str, dict[str, list]] = defaultdict(lambda: {"research": [], "developer": []})
        SAMPLE_COUNT = 2

        def _collect_unique_values(board_state, action_history):
            """Collect all unique cell values from board_state and action_history."""
            values = set()
            if board_state:
                for row in board_state:
                    if isinstance(row, list):
                        values.update(row)
            if action_history:
                for action in action_history:
                    if action.get("old_value") is not None:
                        values.add(action["old_value"])
                    if action.get("new_value") is not None:
                        values.add(action["new_value"])
            return sorted(values)

        for row in rows:
            attempt_id, board_state, action_history, puzzle_type = row

            if not board_state and not action_history:
                no_data += 1
                by_type[puzzle_type]["no_data"] += 1
                continue

            if puzzle_type not in ResearchFormatTranslator.ENUM_TO_RESEARCH:
                unknown_type += 1
                continue

            if is_research_format(board_state, action_history):
                already_research += 1
                by_type[puzzle_type]["research"] += 1
                if verbose and len(samples[puzzle_type]["research"]) < SAMPLE_COUNT:
                    samples[puzzle_type]["research"].append({
                        "id": str(attempt_id),
                        "values": _collect_unique_values(board_state, action_history),
                    })
            else:
                needs_conversion += 1
                by_type[puzzle_type]["developer"] += 1
                conversion_ids.append((attempt_id, puzzle_type))
                if verbose and len(samples[puzzle_type]["developer"]) < SAMPLE_COUNT:
                    samples[puzzle_type]["developer"].append({
                        "id": str(attempt_id),
                        "values": _collect_unique_values(board_state, action_history),
                    })

        # print summary
        console.print()
        summary_table = Table(show_header=True, header_style="bold magenta", title="Format Summary")
        summary_table.add_column("Category", style="cyan")
        summary_table.add_column("Count", justify="right")
        summary_table.add_column("%", justify="right")

        for label, count in [
            ("Already research format", already_research),
            ("Needs conversion (developer format)", needs_conversion),
            ("No data (empty)", no_data),
            ("Unknown puzzle type", unknown_type),
        ]:
            pct = f"{count / total_count * 100:.1f}" if total_count > 0 else "0"
            summary_table.add_row(label, str(count), pct)

        console.print(summary_table)

        # per-type breakdown
        if by_type:
            console.print()
            type_table = Table(show_header=True, header_style="bold magenta", title="Per-Type Breakdown")
            type_table.add_column("Puzzle Type", style="cyan")
            type_table.add_column("Research", justify="right", style="green")
            type_table.add_column("Developer", justify="right", style="red")
            type_table.add_column("No Data", justify="right", style="yellow")

            for pt in sorted(by_type.keys()):
                counts = by_type[pt]
                type_table.add_row(pt, str(counts["research"]), str(counts["developer"]), str(counts["no_data"]))

            console.print(type_table)

        # verbose: show samples from each category
        if verbose:
            for pt in sorted(samples.keys()):
                pt_samples = samples[pt]
                has_any = any(len(v) > 0 for v in pt_samples.values())
                if not has_any:
                    continue

                console.print(f"\n[bold]── {pt} ──[/bold]")

                if pt_samples["research"]:
                    console.print(f"  [green]Research format samples:[/green]")
                    for s in pt_samples["research"]:
                        console.print(f"    {s['id'][:8]}…  values: {s['values']}")

                if pt_samples["developer"]:
                    console.print(f"  [red]Developer format samples:[/red]")
                    for s in pt_samples["developer"]:
                        console.print(f"    {s['id'][:8]}…  values: {s['values']}")

        if needs_conversion == 0:
            console.print("\n[green]All attempts are already in research format.[/green]")
            return

        if not apply:
            console.print(f"\n[yellow]DRY RUN — {needs_conversion} attempts would be converted. Use --apply to update.[/yellow]")
            return

        # apply conversions in batches
        console.print(f"\n[cyan]Converting {needs_conversion} attempts...[/cyan]")
        converted = 0

        for i in range(0, len(conversion_ids), BATCH_SIZE):
            batch = conversion_ids[i : i + BATCH_SIZE]
            batch_ids = [aid for aid, _ in batch]

            # fetch full rows for this batch
            batch_query = (
                select(FreeplayPuzzleAttempt)
                .where(FreeplayPuzzleAttempt.id.in_(batch_ids))
            )
            batch_result = await session.execute(batch_query)
            attempts = batch_result.scalars().all()

            # map id -> puzzle_type
            id_to_type = {aid: pt for aid, pt in batch}

            for attempt in attempts:
                pt = id_to_type[attempt.id]
                try:
                    translator = ResearchFormatTranslator(pt)

                    if attempt.board_state and isinstance(attempt.board_state, list):
                        if attempt.board_state and isinstance(attempt.board_state[0], list):
                            attempt.board_state = translator.translate_grid(attempt.board_state)

                    if attempt.action_history and isinstance(attempt.action_history, list):
                        attempt.action_history = translator.translate_action_history(attempt.action_history)

                    converted += 1
                except Exception as e:
                    console.print(f"[red]Error converting {attempt.id}: {e}[/red]")

            await session.commit()
            console.print(f"  {min(i + BATCH_SIZE, len(conversion_ids))}/{len(conversion_ids)}")

        console.print(f"\n[green]Done. Converted {converted} attempts to research format.[/green]")


if __name__ == "__main__":
    app()
