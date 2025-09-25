"""
CLI command for importing puzzles from JSON file.
Usage: python -m app.commands.import_puzzles path/to/puzzles.json
"""

import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from sqlalchemy import select

# Import from your app - adjust these imports based on your actual structure
from app.dependencies import async_session_maker
from app.modules.puzzle import Puzzle

console = Console()
app = typer.Typer()


def parse_datetime(dt_string: str) -> datetime:
    """Parse datetime string from Django export."""
    # Remove timezone info and parse
    dt_string = dt_string.replace(" +00:00", "")
    return datetime.fromisoformat(dt_string)


async def import_puzzles_to_db(puzzles_data: List[Dict[str, Any]], skip_duplicates: bool = True):
    """Import puzzles into the database."""
    async with async_session_maker() as session:
        imported_count = 0
        skipped_count = 0
        error_count = 0

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task = progress.add_task(f"[cyan]Importing {len(puzzles_data)} puzzles...", total=len(puzzles_data))

            for puzzle_data in puzzles_data:
                try:
                    # Check if puzzle with this hash already exists
                    if skip_duplicates:
                        existing = await session.execute(select(Puzzle).where(Puzzle.puzzle_hash == puzzle_data["puzzle_hash"]))
                        if existing.scalar_one_or_none():
                            skipped_count += 1
                            progress.update(task, advance=1)
                            continue

                    # Move old ID into puzzle_data as old_id
                    puzzle_json = puzzle_data["puzzle_data"].copy()
                    puzzle_json["old_id"] = puzzle_data["id"]

                    # Create new Puzzle object (ID will be auto-generated)
                    puzzle = Puzzle(
                        created_at=parse_datetime(puzzle_data["created_at"]),
                        updated_at=parse_datetime(puzzle_data["updated_at"]),
                        puzzle_hash=puzzle_data["puzzle_hash"],
                        puzzle_type=puzzle_data["puzzle_type"],
                        puzzle_size=puzzle_data["puzzle_size"],
                        puzzle_difficulty=puzzle_data["puzzle_difficulty"],
                        puzzle_data=puzzle_json,
                    )

                    session.add(puzzle)
                    imported_count += 1

                    # Commit in batches of 100
                    if imported_count % 100 == 0:
                        await session.commit()

                except Exception as e:
                    console.print(f"[red]Error importing puzzle {puzzle_data.get('id', 'unknown')}: {e}")
                    error_count += 1
                    await session.rollback()

                progress.update(task, advance=1)

            # Final commit for remaining puzzles
            await session.commit()

        # Print summary
        console.print("\n[bold green]Import Complete![/bold green]")
        console.print(f"✅ Imported: {imported_count} puzzles")
        if skipped_count > 0:
            console.print(f"⏭️  Skipped (duplicates): {skipped_count} puzzles")
        if error_count > 0:
            console.print(f"❌ Errors: {error_count} puzzles")

        return imported_count, skipped_count, error_count


@app.command()
def main(
    file_path: Path = typer.Argument(..., help="Path to JSON file containing puzzle data", exists=True, file_okay=True, dir_okay=False, readable=True),
    skip_duplicates: bool = typer.Option(True, "--skip-duplicates/--overwrite", help="Skip puzzles that already exist (based on puzzle_hash)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview import without making changes to database"),
):
    """
    Import puzzles from a JSON file into the database.

    The JSON file should be a list of puzzle objects with the following structure:
    {
        "id": 1,
        "created_at": "2025-07-07 16:47:23.598498 +00:00",
        "updated_at": "2025-07-07 16:47:23.598517 +00:00",
        "puzzle_hash": "5c0bd017cd61ffba",
        "puzzle_type": "kakurasu",
        "puzzle_size": "5x5",
        "puzzle_difficulty": "easy",
        "puzzle_data": {...}
    }

    The old 'id' will be preserved in puzzle_data as 'old_id'.
    New UUID ids will be auto-generated.
    """
    console.print(f"[bold cyan]Loading puzzles from:[/bold cyan] {file_path}")

    try:
        # Load JSON file
        with open(file_path, "r") as f:
            puzzles_data = json.load(f)

        if not isinstance(puzzles_data, list):
            console.print("[red]Error: JSON file must contain a list of puzzles")
            raise typer.Exit(1)

        console.print(f"[green]Found {len(puzzles_data)} puzzles in file[/green]")

        # Show sample of puzzle types
        puzzle_types = {}
        for p in puzzles_data:
            ptype = p.get("puzzle_type", "unknown")
            puzzle_types[ptype] = puzzle_types.get(ptype, 0) + 1

        console.print("\n[bold]Puzzle types found:[/bold]")
        for ptype, count in sorted(puzzle_types.items()):
            console.print(f"  • {ptype}: {count} puzzles")

        if dry_run:
            console.print("\n[yellow]DRY RUN MODE - No changes will be made to the database[/yellow]")
            console.print("\nSample puzzle that would be imported:")
            sample = puzzles_data[0].copy()
            sample_json = sample["puzzle_data"].copy()
            sample_json["old_id"] = sample["id"]
            console.print(f"  Hash: {sample['puzzle_hash']}")
            console.print(f"  Type: {sample['puzzle_type']}")
            console.print(f"  Size: {sample['puzzle_size']}")
            console.print(f"  Difficulty: {sample['puzzle_difficulty']}")
            console.print(f"  Old ID preserved in puzzle_data: {sample['id']}")
            return

        # Confirm import
        if not typer.confirm("\nProceed with import?"):
            console.print("[yellow]Import cancelled[/yellow]")
            raise typer.Exit()

        # Run async import
        asyncio.run(import_puzzles_to_db(puzzles_data, skip_duplicates))

    except FileNotFoundError:
        console.print(f"[red]Error: File not found: {file_path}[/red]")
        raise typer.Exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error: Invalid JSON in file: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def verify(puzzle_type: str = typer.Option(None, help="Filter by puzzle type"), limit: int = typer.Option(10, help="Number of puzzles to show")):
    """Verify imported puzzles by showing a sample from the database."""

    async def verify_puzzles():
        async with async_session_maker() as session:
            query = select(Puzzle)
            if puzzle_type:
                query = query.where(Puzzle.puzzle_type == puzzle_type)
            query = query.limit(limit)

            result = await session.execute(query)
            puzzles = result.scalars().all()

            if not puzzles:
                console.print("[yellow]No puzzles found[/yellow]")
                return

            console.print(f"\n[bold]Showing {len(puzzles)} puzzles:[/bold]")
            for puzzle in puzzles:
                console.print(f"\n[cyan]ID:[/cyan] {puzzle.id}")
                console.print(f"  Type: {puzzle.puzzle_type}")
                console.print(f"  Size: {puzzle.puzzle_size}")
                console.print(f"  Difficulty: {puzzle.puzzle_difficulty}")
                console.print(f"  Hash: {puzzle.puzzle_hash}")
                if "old_id" in puzzle.puzzle_data:
                    console.print(f"  Old ID: {puzzle.puzzle_data['old_id']}")

    asyncio.run(verify_puzzles())


if __name__ == "__main__":
    app()
