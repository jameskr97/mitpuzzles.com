"""
Puzzle import and update commands with semantic ID support.
Handles normalized puzzle data with deduplication.
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

app = typer.Typer(name="puzzle-import", help="Puzzle import and update commands")
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
    Merge new puzzle data with existing data.

    Strategies:
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
    Import normalized puzzles with semantic IDs.

    This command:
    - Loads puzzles from JSON files
    - Normalizes them (generates semantic IDs)
    - Detects duplicates using complete_id
    - Updates existing puzzles or inserts new ones
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

            # Check if puzzle exists
            existing = await session.scalar(select(Puzzle).where(Puzzle.complete_id == complete_id))

            if existing:
                # Update existing puzzle
                existing_data = existing.puzzle_data
                merged_data = await _merge_puzzle_data(existing_data, puzzle_data, merge_strategy)

                if merged_data != existing_data:
                    if verbose:
                        console.print(f"  Updating puzzle {complete_id[:8]}...")

                    if not dry_run:
                        existing.puzzle_data = merged_data
                        existing.updated_at = datetime.utcnow()

                        # Update semantic IDs if they changed (shouldn't happen but safety check)
                        existing.definition_id = puzzle_data["definition_id"]
                        existing.solution_id = puzzle_data["solution_id"]

                        # Update metadata
                        existing.puzzle_type = puzzle_data["puzzle_type"]
                        existing.puzzle_size = puzzle_data["puzzle_size"]
                        existing.puzzle_difficulty = puzzle_data.get("difficulty_label", None)

                    stats["updated"] += 1
                else:
                    stats["unchanged"] += 1
                    if verbose:
                        console.print(f"  Puzzle {complete_id[:8]}... unchanged")
            else:
                # Insert new puzzle
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
    console.print("IMPORT SUMMARY")
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
    Check for various types of duplicates in the database.

    Finds:
    - Puzzles with same definition_id (should have same solution)
    - Puzzles with same solution_id (variants)
    - Any data inconsistencies
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


if __name__ == "__main__":
    app()
