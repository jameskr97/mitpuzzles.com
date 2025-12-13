import logging
from datetime import datetime, timezone, timedelta
from celery import Celery
from sqlalchemy import update, and_, create_engine, select
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.modules.tracking import SessionActivity

logger = logging.getLogger(__name__)


def get_sync_session():
    """Get a synchronous database session for Celery tasks."""
    database_url = settings.DATABASE_URL
    if 'asyncpg' in database_url:
        database_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    return Session()

# Initialize Celery with Valkey as broker (Redis-compatible)
celery_app = Celery(
    'mitpuzzles',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max
    worker_prefetch_multiplier=1,
)

# Scheduled tasks
celery_app.conf.beat_schedule = {
    'cleanup-stale-sessions': {
        'task': 'app.tasks.cleanup_stale_sessions',
        'schedule': 60.0,  # every 60 seconds
    },
}


@celery_app.task(name='app.tasks.cleanup_stale_sessions')
def cleanup_stale_sessions():
    """
    Close sessions that haven't received a heartbeat in 30 minutes.
    Sets ended_at to last_heartbeat_at + 15 seconds.
    Runs every 60 seconds.
    """
    try:
        # We need to use a synchronous session for Celery tasks
        # Convert asyncpg URL to psycopg2 for sync usage
        database_url = settings.DATABASE_URL
        if 'asyncpg' in database_url:
            database_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')

        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)

        with Session() as db:
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=30)

            # Update stale sessions
            result = db.execute(
                update(SessionActivity)
                .where(
                    and_(
                        SessionActivity.ended_at.is_(None),  # Session is still "active"
                        SessionActivity.last_heartbeat_at < cutoff_time
                    )
                )
                .values(
                    ended_at=SessionActivity.last_heartbeat_at + timedelta(seconds=15)
                )
            )

            db.commit()

            closed_count = result.rowcount
            if closed_count > 0:
                logger.info(f"Closed {closed_count} stale sessions")

            return {
                'closed_sessions': closed_count,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    except Exception as e:
        logger.error(f"Error cleaning up sessions: {e}")
        raise


@celery_app.task(name='app.tasks.analyze_puzzle_batch', bind=True)
def analyze_puzzle_batch(self, job_id: str, skip_duplicate_check: bool = False):
    """
    Analyze all puzzles in an analysis job.
    Checks for duplicates and runs SAT solver to verify uniqueness.
    """
    from app.modules.puzzle_analysis import BackgroundJob, AnalysisJobPuzzle
    from app.modules.puzzle import Puzzle
    from app.solvers import solve, supports_solver

    db = get_sync_session()

    try:
        # Load job
        job = db.query(BackgroundJob).filter(BackgroundJob.id == job_id).first()
        if not job:
            logger.error(f"Analysis job not found: {job_id}")
            return {"error": "Job not found"}

        job.status = "running"
        db.commit()
        print(f"[analyze_puzzle_batch] Starting job {job_id} with {job.total_puzzles} puzzles")

        # Load puzzles for this job
        puzzles = (
            db.query(AnalysisJobPuzzle)
            .filter(AnalysisJobPuzzle.job_id == job_id)
            .order_by(AnalysisJobPuzzle.puzzle_index)
            .all()
        )

        # Get all complete_ids from this job for duplicate checking
        # Skip if job is analyzing puzzles already in database
        existing_ids = set()
        if not skip_duplicate_check:
            job_complete_ids = [p.complete_id for p in puzzles]

            # Check which complete_ids already exist in the puzzle table
            existing_ids = set(
                db.query(Puzzle.complete_id)
                .filter(Puzzle.complete_id.in_(job_complete_ids))
                .all()
            )
            existing_ids = {row[0] for row in existing_ids}
            print(f"[analyze_puzzle_batch] Found {len(existing_ids)} existing puzzles in database")
        else:
            print(f"[analyze_puzzle_batch] Skipping duplicate check (puzzles from database)")

        # Check if solver is available for this puzzle type
        has_solver = supports_solver(job.puzzle_type)
        if has_solver:
            print(f"[analyze_puzzle_batch] Using SAT solver for puzzle type: {job.puzzle_type}")
        else:
            print(f"[analyze_puzzle_batch] WARNING: No solver for {job.puzzle_type} - marking as unverified")

        # Process each puzzle
        for puzzle in puzzles:
            puzzle.status = "analyzing"
            db.commit()

            try:
                # First check if this puzzle already exists in the database
                if puzzle.complete_id in existing_ids:
                    puzzle.status = "done"
                    puzzle.result = "duplicate"
                    job.duplicate_count += 1
                    logger.debug(f"Puzzle {puzzle.puzzle_index}: duplicate (exists in database)")

                elif has_solver:
                    # Run SAT solver
                    result = solve(job.puzzle_type, puzzle.puzzle_data, max_solutions=10)

                    puzzle.status = "done"
                    puzzle.solution_count = result.solution_count

                    if result.error:
                        puzzle.result = "error"
                        puzzle.error_message = result.error
                        job.error_count += 1
                        logger.warning(f"Puzzle {puzzle.puzzle_index}: error - {result.error}")

                    elif not result.is_valid:
                        puzzle.result = "invalid"
                        job.invalid_count += 1
                        logger.debug(f"Puzzle {puzzle.puzzle_index}: invalid (no solution)")

                    elif result.is_unique:
                        puzzle.result = "unique"
                        job.unique_count += 1
                        logger.debug(f"Puzzle {puzzle.puzzle_index}: unique")

                    else:
                        puzzle.result = "multi_solution"
                        puzzle.solutions = result.solutions
                        job.multi_solution_count += 1
                        logger.debug(f"Puzzle {puzzle.puzzle_index}: multi_solution ({result.solution_count})")

                else:
                    # No solver available - mark as unverified unique
                    puzzle.status = "done"
                    puzzle.result = "unique"
                    job.unique_count += 1
                    logger.debug(f"Puzzle {puzzle.puzzle_index}: unique (unverified)")

            except Exception as e:
                puzzle.status = "error"
                puzzle.result = "error"
                puzzle.error_message = str(e)
                job.error_count += 1
                logger.error(f"Puzzle {puzzle.puzzle_index}: exception - {e}")

            job.processed_count += 1
            db.commit()

            # Log progress every 50 puzzles or on last puzzle
            if job.processed_count % 50 == 0 or job.processed_count == job.total_puzzles:
                print(f"[analyze_puzzle_batch] Job {job_id}: {job.processed_count}/{job.total_puzzles} processed")

            # Update task progress for Flower
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': job.processed_count,
                    'total': job.total_puzzles,
                    'status': f'Processing puzzle {job.processed_count}/{job.total_puzzles}'
                }
            )

        # Mark job complete
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

        summary = {
            'job_id': str(job_id),
            'status': 'completed',
            'total': job.total_puzzles,
            'unique': job.unique_count,
            'multi_solution': job.multi_solution_count,
            'duplicate': job.duplicate_count,
            'invalid': job.invalid_count,
            'error': job.error_count,
        }

        print(f"[analyze_puzzle_batch] Completed: {summary}")
        return summary

    except Exception as e:
        logger.error(f"Analysis job {job_id} failed: {e}")
        if job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
        raise

    finally:
        db.close()

