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

app = typer.Typer(name="app-cli", help="MIT Puzzles CLI", no_args_is_help=True)
console = Console()

# Add puzzle subcommands
app.add_typer(puzzle_app, name="puzzle", help="Puzzle import and management commands")


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


if __name__ == "__main__":
    app()
