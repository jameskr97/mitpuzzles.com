import logging
from datetime import datetime, timezone, timedelta
from celery import Celery
from sqlalchemy import update, and_, create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.modules.tracking import SessionActivity

logger = logging.getLogger(__name__)

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

