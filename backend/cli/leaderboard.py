import asyncio

import typer
from rich.console import Console

from app.dependencies import async_session_maker

app = typer.Typer(name="leaderboard", help="Leaderboard management commands", no_args_is_help=True)
console = Console()


async def _backfill_ao_scores(score_type: str, dry_run: bool):
    """backfill best average-of-n scores for all users."""
    from app.modules.puzzle.services.leaderboard import LeaderboardService

    async with async_session_maker() as db:
        service = LeaderboardService(db)

        current_user = [None]
        user_count = [0]

        def flush_user():
            if current_user[0] and user_count[0]:
                console.print(f"user {current_user[0]}: saved {user_count[0]} {score_type.upper()} scores")

        def on_progress(user_id, puzzle_type, size, difficulty, score):
            if user_id != current_user[0]:
                flush_user()
                current_user[0] = user_id
                user_count[0] = 0
            if score is not None:
                user_count[0] += 1

        result = await service.backfill_ao_scores(score_type=score_type, on_progress=on_progress)
        flush_user()

        if dry_run:
            await db.rollback()
            console.print(f"[yellow]dry run — rolled back[/yellow]")
        else:
            await db.commit()

        console.print(f"[green]done: {result['processed']} combos processed, {result['updated']} scores written[/green]")


@app.command()
def backfill(
    score_type: str = typer.Argument("ao3", help="score type to backfill (ao3, ao5, ao12)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="show what would be written without committing"),
):
    """backfill best average-of-n scores from puzzle history."""
    valid = {"ao3", "ao5", "ao12"}
    if score_type not in valid:
        console.print(f"[red]invalid score type '{score_type}'. must be one of: {', '.join(sorted(valid))}[/red]")
        raise typer.Exit(1)

    console.print(f"[cyan]backfilling {score_type} scores...[/cyan]")
    asyncio.run(_backfill_ao_scores(score_type, dry_run))
