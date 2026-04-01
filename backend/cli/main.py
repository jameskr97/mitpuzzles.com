import asyncio
import json
import os
from typing import List

import typer
from rich.console import Console
from sqlalchemy import select, text

from app.dependencies import async_session_maker
from app.modules.experiments import ExperimentRun
from app.modules.puzzle import Puzzle
from cli.puzzle_importer import app as puzzle_app
from cli.activity import app as activity_app
from cli.metrics import app as metrics_app

app = typer.Typer(name="app-cli", help="MIT Puzzles CLI", no_args_is_help=True)
console = Console()

# Add subcommands
app.add_typer(puzzle_app, name="puzzle", help="Puzzle import and management commands")
app.add_typer(metrics_app, name="metrics", help="Game metrics analysis commands")
app.add_typer(activity_app, name="activity", help="User activity management commands")


def _ensure_path_exists(path: str):
    """ensure the given path exists"""
    if not os.path.exists(path):
        console.print(f"[red]Error: Path {path} does not exist[/red]")
        raise typer.Exit(1)


def _confirm_action(message: str):
    """confirm an action with the user"""
    if not typer.confirm(message):
        console.print("[yellow]Action cancelled[/yellow]")
        raise typer.Exit()


async def _import_file(file_path: str) -> bool:
    """import puzzles from a single json file: TODO(fixme): this doesn't acknowledge the new definition_id and solution_id"""
    filename_ext = os.path.basename(file_path)
    filename, ext = os.path.splitext(filename_ext)

    try:
        puzzle_type = filename.split("_")[0]
        puzzle_size = filename.split("_")[1]
        puzzle_difficulty = filename.split("_")[2]
    except IndexError:
        console.print(
            f"[red]{filename}: Invalid filename format: {filename_ext}. Expected format: <puzzle_type>_<puzzle_size>_<puzzle_difficulty>.json. Skipping file...[/red]"
        )
        return False

    # load file
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        console.print(f"[red]{filename}: Error reading file: {e}[/red]")
        return False

    if not isinstance(data, list):
        console.print(f"[red]{filename}: The file {file_path} does not contain a list at the top level[/red]")
        return False

    # get existing hashes from database
    async with async_session_maker() as session:
        result = await session.execute(select(Puzzle.puzzle_hash))
        all_current_hashes = {row[0] for row in result.fetchall()}

        # also track hashes we're importing in this session to avoid duplicates within the file
        session_hashes = set()

        # import the puzzles
        imported_count = 0
        skipped_count = 0
        for puzzle in data:
            if "id" not in puzzle:
                # generate an id based on game_board hash
                if "game_board" not in puzzle:
                    console.print("[yellow]Skipping puzzle without id or game_board[/yellow]")
                    continue

                import hashlib

                board = puzzle["game_board"]
                # flatten the 2d board list
                flat_board = [cell for row in board for cell in row]
                # create board string with dimensions and flattened values
                rows = len(board)
                cols = len(board[0]) if board else 0
                board_str = f"{rows}x{cols}:" + ",".join(map(str, flat_board))
                hash_obj = hashlib.sha256(board_str.encode("utf-8"))
                puzzle["id"] = hash_obj.hexdigest()[:16]
                console.print(f"[yellow]Generated puzzle id: {puzzle['id']}[/yellow]")

            puzzle_hash = puzzle["id"]  # the "id" field in json is actually the puzzle hash

            # skip puzzles that already exist in database
            if puzzle_hash in all_current_hashes:
                skipped_count += 1
                continue

            # skip puzzles that are duplicates within this file
            if puzzle_hash in session_hashes:
                console.print(f"[yellow]Skipping duplicate puzzle hash within file: {puzzle_hash}[/yellow]")
                skipped_count += 1
                continue

            session_hashes.add(puzzle_hash)

            try:
                new_puzzle = Puzzle(
                    puzzle_hash=puzzle_hash,
                    puzzle_type=puzzle_type,
                    puzzle_size=puzzle_size,
                    puzzle_difficulty=puzzle_difficulty,
                    puzzle_data=puzzle,
                )
                session.add(new_puzzle)
                imported_count += 1

                # commit in batches of 100
                if imported_count % 100 == 0:
                    await session.commit()

            except Exception as e:
                console.print(f"[red]Failed to import puzzle with id {puzzle_hash}: {e}[/red]")
                await session.rollback()
                continue

        # final commit
        await session.commit()

        # reset the auto-increment sequence to avoid conflicts
        if imported_count > 0:
            result = await session.execute(text("SELECT MAX(id) FROM puzzle"))
            max_id = result.scalar()
            if max_id:
                await session.execute(text(f"ALTER SEQUENCE puzzle_id_seq RESTART WITH {max_id + 1}"))
                await session.commit()

    if imported_count > 0:
        console.print(f"[green]Imported {imported_count} puzzles from {filename_ext}[/green]")
    if skipped_count > 0:
        console.print(f"[yellow]Skipped {skipped_count} existing puzzles[/yellow]")
    if imported_count == 0:
        console.print(f"[yellow]No new puzzles to import from {filename_ext}[/yellow]")
    return True


@app.command()
def import_puzzles(path: str = typer.Argument(..., help="The path to a directory or JSON file containing puzzle data")):
    """validate and import puzzles from json files"""
    _ensure_path_exists(path)

    # if not a directory, assume it's a json file
    if not os.path.isdir(path):
        asyncio.run(_import_file(path))
        return

    # get all json files in the directory
    json_files = sorted([f for f in os.listdir(path) if f.endswith(".json")])
    if not json_files:
        console.print(f"[yellow]No JSON files found in {path}[/yellow]")
        return

    console.print(f"[green]Found the following JSON files in {path}:[/green]")
    for json_file in json_files:
        console.print(f" - {json_file}")

    _confirm_action("Do you want to proceed with importing these files?")

    # import each file
    async def import_all_files():
        for file in json_files:
            file_path = os.path.join(path, file)
            await _import_file(file_path)

    asyncio.run(import_all_files())


async def _do_experiment_download(eid: str):
    async with async_session_maker() as session:
        results: List[ExperimentRun] = (
            (await session.execute(select(ExperimentRun).where(ExperimentRun.recruitment_platform == "prolific").where(ExperimentRun.experiment_id == eid)))
            .scalars()
            .all()
        )

        data = [r.experiment_data for r in results]
        with open(f"{eid}.json", "w+") as f:
            f.write(json.dumps(data))
        print(f"Data written to {eid}.json")


@app.command(no_args_is_help=True)
def download_experiment_data(eid: str = typer.Argument(..., help="The id of the experiment")):
    asyncio.run(_do_experiment_download(eid))


async def _do_send_notification(title: str, body: str, admin_only: bool):
    """send push notification to subscribed users"""
    from app.modules.push_notifications import send_push_to_all

    async with async_session_maker() as session:
        result = await send_push_to_all(session, title, body, admin_only=admin_only)

        if admin_only:
            console.print(f"[cyan]Sending to superusers only[/cyan]")
        else:
            console.print(f"[cyan]Sending to all subscribed users[/cyan]")

        console.print(f"[green]Successfully sent: {result['sent']}[/green]")
        if result['failed'] > 0:
            console.print(f"[yellow]Failed to send: {result['failed']}[/yellow]")
        console.print(f"[blue]Total subscriptions: {result['total']}[/blue]")


@app.command()
def notify(
    title: str = typer.Argument(..., help="The notification title"),
    body: str = typer.Argument(..., help="The notification body"),
    admin_only: bool = typer.Option(False, "--admin-only", help="Send only to superusers (for testing)"),
):
    """Send push notification to subscribed users"""
    asyncio.run(_do_send_notification(title, body, admin_only))


@app.command()
def start_analysis(
    job_id: str = typer.Argument(..., help="Job ID to start"),
):
    """Start a pending analysis job."""
    from app.tasks import analyze_puzzle_batch

    analyze_puzzle_batch.delay(job_id)
    console.print(f"[green]Started analysis for job {job_id}[/green]")


@app.command(no_args_is_help=True)
def analyze_puzzles(
    paths: List[str] = typer.Argument(..., help="Paths to JSON files or directories"),
    puzzle_type: str = typer.Option(None, "--type", "-t", help="Puzzle type (overrides filename)"),
    start_job: bool = typer.Option(True, "--start/--no-start", help="Start Celery job immediately"),
):
    """
    Upload puzzles for analysis. Creates a job that runs in the background.

    The job checks for duplicates and verifies puzzle uniqueness using SAT solver.
    Monitor progress with Celery Flower or query the database.

    Examples:
        - cli analyze-puzzles lightup_10x10_easy.json
        - cli analyze-puzzles ./puzzles/ --type lightup
        - cli analyze-puzzles puzzles.json --type lightup --no-start
    """
    asyncio.run(_analyze_puzzles(paths, puzzle_type, start_job))


async def _analyze_puzzles(paths: List[str], puzzle_type: str | None, start_job: bool):
    from cli.normalizer import PuzzleNormalizer
    from app.modules.puzzle_analysis import BackgroundJob, AnalysisJobPuzzle
    from app.tasks import analyze_puzzle_batch

    normalizer = PuzzleNormalizer()

    # Collect all JSON files from paths
    json_files = []
    for path in paths:
        _ensure_path_exists(path)
        if os.path.isdir(path):
            json_files.extend(sorted([os.path.join(path, f) for f in os.listdir(path) if f.endswith(".json")]))
        else:
            json_files.append(path)

    if not json_files:
        console.print("[yellow]No JSON files found[/yellow]")
        return

    console.print(f"[cyan]Found {len(json_files)} file(s) to process[/cyan]")

    async with async_session_maker() as session:
        for file_path in json_files:
            filename = os.path.basename(file_path)
            console.print(f"\n[bold]Processing {filename}...[/bold]")

            # Load JSON
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                console.print(f"[red]Error reading file: {e}[/red]")
                continue

            puzzles = data if isinstance(data, list) else [data]
            console.print(f"[dim]Loaded {len(puzzles)} puzzle(s)[/dim]")

            # Determine puzzle type
            if puzzle_type:
                ptype = puzzle_type
            else:
                try:
                    ptype, _, _ = normalizer.extract_puzzle_metadata(os.path.splitext(filename)[0])
                except ValueError:
                    console.print(f"[red]Could not determine puzzle type from filename. Use --type flag.[/red]")
                    continue

            console.print(f"[dim]Puzzle type: {ptype}[/dim]")

            # Normalize puzzles
            normalized, duplicates = normalizer.process_all_puzzles({filename: puzzles})

            if duplicates:
                console.print(f"[yellow]Found {len(duplicates)} duplicates within file (skipped)[/yellow]")

            if not normalized:
                console.print("[yellow]No puzzles to analyze after normalization[/yellow]")
                continue

            console.print(f"[dim]Normalized {len(normalized)} puzzle(s)[/dim]")

            # Create job
            job = BackgroundJob(
                status="pending",
                puzzle_type=ptype,
                source_filename=filename,
                source_data=puzzles,  # Store original for potential rerun
                total_puzzles=len(normalized),
            )
            session.add(job)
            await session.flush()

            # Create puzzle records
            for idx, puzzle in enumerate(normalized):
                puzzle_record = AnalysisJobPuzzle(
                    job_id=job.id,
                    puzzle_index=idx,
                    puzzle_data=puzzle,
                    definition_id=puzzle["definition_id"],
                    solution_id=puzzle["solution_id"],
                    complete_id=puzzle["complete_id"],
                    status="pending",
                )
                session.add(puzzle_record)

            await session.commit()

            console.print(f"[green]Created job {job.id} with {len(normalized)} puzzles[/green]")

            # Start Celery task
            if start_job:
                analyze_puzzle_batch.delay(str(job.id))
                console.print(f"[cyan]Started background analysis task[/cyan]")
            else:
                console.print(f"[yellow]Job created but not started. Use Celery to start manually.[/yellow]")

            console.print(f"[blue]Job ID: {job.id}[/blue]")


@app.command()
def analyze_db_puzzles(
    puzzle_type: str = typer.Argument(..., help="Puzzle type to analyze (e.g., lightup)"),
    puzzle_size: str = typer.Option(None, "--size", "-s", help="Filter by size (e.g., 5x5)"),
    puzzle_difficulty: str = typer.Option(None, "--difficulty", "-d", help="Filter by difficulty (e.g., easy)"),
    limit: int = typer.Option(None, "--limit", "-l", help="Limit number of puzzles"),
    start_job: bool = typer.Option(True, "--start/--no-start", help="Start Celery job immediately"),
):
    """
    Analyze existing puzzles from the database.

    Creates an analysis job for puzzles already in the puzzle table.
    Useful for re-verifying puzzles or checking for issues.

    Examples:
        - cli analyze-db-puzzles lightup
        - cli analyze-db-puzzles lightup --size 5x5
        - cli analyze-db-puzzles lightup --difficulty easy --limit 100
    """
    asyncio.run(_analyze_db_puzzles(puzzle_type, puzzle_size, puzzle_difficulty, limit, start_job))


async def _analyze_db_puzzles(
    puzzle_type: str,
    puzzle_size: str | None,
    puzzle_difficulty: str | None,
    limit: int | None,
    start_job: bool,
):
    from sqlalchemy import select
    from app.modules.puzzle import Puzzle
    from app.modules.puzzle_analysis import BackgroundJob, AnalysisJobPuzzle
    from app.tasks import analyze_puzzle_batch

    async with async_session_maker() as session:
        # Build query
        query = select(Puzzle).where(Puzzle.puzzle_type == puzzle_type)

        if puzzle_size:
            query = query.where(Puzzle.puzzle_size == puzzle_size)
        if puzzle_difficulty:
            query = query.where(Puzzle.puzzle_difficulty == puzzle_difficulty)

        query = query.order_by(Puzzle.created_at)

        if limit:
            query = query.limit(limit)

        # Execute query
        result = await session.execute(query)
        puzzles = result.scalars().all()

        if not puzzles:
            console.print(f"[yellow]No puzzles found matching criteria[/yellow]")
            return

        console.print(f"[cyan]Found {len(puzzles)} {puzzle_type} puzzles to analyze[/cyan]")

        # Build source filename description
        parts = [puzzle_type]
        if puzzle_size:
            parts.append(puzzle_size)
        if puzzle_difficulty:
            parts.append(puzzle_difficulty)
        source_name = f"db:{':'.join(parts)}"

        # Create job
        job = BackgroundJob(
            status="pending",
            puzzle_type=puzzle_type,
            source_filename=source_name,
            source_data=None,  # Don't store - puzzles are already in DB
            total_puzzles=len(puzzles),
        )
        session.add(job)
        await session.flush()

        # Create puzzle records from existing puzzles
        for idx, puzzle in enumerate(puzzles):
            puzzle_record = AnalysisJobPuzzle(
                job_id=job.id,
                puzzle_index=idx,
                puzzle_data=puzzle.puzzle_data,
                definition_id=puzzle.definition_id,
                solution_id=puzzle.solution_id,
                complete_id=puzzle.complete_id,
                status="pending",
                imported=True,  # Already in database
                imported_puzzle_id=puzzle.id,
            )
            session.add(puzzle_record)

        await session.commit()

        console.print(f"[green]Created job {job.id} with {len(puzzles)} puzzles[/green]")

        # Start Celery task
        if start_job:
            analyze_puzzle_batch.delay(str(job.id), skip_duplicate_check=True)
            console.print(f"[cyan]Started background analysis task[/cyan]")
        else:
            console.print(f"[yellow]Job created but not started. Use 'cli start-analysis {job.id}' to start.[/yellow]")

        console.print(f"[blue]Job ID: {job.id}[/blue]")


if __name__ == "__main__":
    app()
