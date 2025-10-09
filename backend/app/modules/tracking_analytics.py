from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Query
from sqlalchemy import func, select, and_, case
from sqlalchemy.orm import Session
from typing import Optional, List

from app.dependencies import AsyncDatabase
from app.modules.tracking import SessionActivity, SessionTrackingService, Device
from app.modules.authentication import User
from app.modules.puzzle import FreeplayPuzzleAttempt, Puzzle

# Router
router = APIRouter()


@router.get("/api/analytics/active-users", tags=["Analytics"])
async def get_active_users(db: AsyncDatabase):
    """
    Get count of currently active users (devices with heartbeat in last 2 minutes)
    """
    session_service = SessionTrackingService(db)
    count = await session_service.get_active_users_count()
    return {
        "active_users": count,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/api/analytics/daily-stats", tags=["Analytics"])
async def get_daily_stats(date: str, db: AsyncDatabase):
    """
    Get daily session statistics for a specific date (YYYY-MM-DD format)
    """
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}

    # Query sessions for the target date
    result = await db.execute(
        select(
            func.count().label("total_sessions"),
            func.count(func.distinct(SessionActivity.device_id)).label("unique_devices"),
            func.count(func.distinct(SessionActivity.user_id)).label("unique_users"),
            func.sum(SessionActivity.active_seconds).label("total_active_seconds"),
            func.avg(SessionActivity.active_seconds).label("avg_session_duration"),
            func.max(SessionActivity.active_seconds).label("max_session_duration"),
        )
        .where(func.date(SessionActivity.started_at) == target_date)
    )

    stats = result.first()

    return {
        "date": date,
        "total_sessions": stats.total_sessions or 0,
        "unique_devices": stats.unique_devices or 0,
        "unique_users": stats.unique_users or 0,
        "total_active_time_seconds": stats.total_active_seconds or 0,
        "total_active_time_hours": round((stats.total_active_seconds or 0) / 3600, 2),
        "avg_session_duration_seconds": round(stats.avg_session_duration or 0, 1),
        "max_session_duration_seconds": stats.max_session_duration or 0,
    }


@router.get("/api/analytics/session-summary", tags=["Analytics"])
async def get_session_summary(db: AsyncDatabase, limit: int = 100):
    """
    Get recent session summary with basic stats
    """
    sessions = await db.execute(
        select(
            SessionActivity.session_id,
            SessionActivity.started_at,
            SessionActivity.ended_at,
            SessionActivity.active_seconds,
            SessionActivity.device_id,
            SessionActivity.user_id,
        )
        .order_by(SessionActivity.started_at.desc())
        .limit(limit)
    )

    session_list = []
    for session in sessions:
        session_list.append({
            "session_id": session.session_id,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "active_seconds": session.active_seconds,
            "active_minutes": round(session.active_seconds / 60, 1),
            "is_active": session.ended_at is None,  # Derived from ended_at
            "device_id": str(session.device_id),
            "user_id": str(session.user_id) if session.user_id else None,
        })

    return {
        "sessions": session_list,
        "count": len(session_list),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/api/analytics/current-visitors", tags=["Analytics"])
async def get_current_visitors(db: AsyncDatabase):
    """
    Get current active visitors (devices with heartbeat in last 2 minutes)
    Perfect for real-time dashboards - ping every minute
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=2)

    current_visitors = await db.scalar(
        select(func.count(func.distinct(SessionActivity.device_id)))
        .where(
            SessionActivity.ended_at.is_(None),  # Active sessions
            SessionActivity.last_heartbeat_at > cutoff
        )
    )

    return {
        "current_visitors": current_visitors or 0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cutoff_minutes": 2
    }


@router.get("/api/analytics/registrations-over-time", tags=["Analytics"])
async def get_registrations_over_time(
    db: AsyncDatabase,
    start_date: str = None,  # YYYY-MM-DD
    end_date: str = None,    # YYYY-MM-DD
    groupby: str = "day",    # day, week, month
):
    """
    Get user registrations over time - perfect for bar charts
    Examples:
    - /api/analytics/registrations-over-time (last 30 days by day)
    - /api/analytics/registrations-over-time?groupby=week (last 12 weeks)
    - /api/analytics/registrations-over-time?start_date=2025-01-01&end_date=2025-01-31
    """
    try:
        # Default to last 30 days if no dates provided
        if not start_date and not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        # Parse dates
        start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1) if end_date else None

        # Build query with date_trunc for grouping
        period_col = func.date_trunc(groupby, User.date_created)
        query = select(
            period_col.label("period"),
            func.count().label("registrations")
        )

        # Add date filters
        if start_dt:
            query = query.where(User.date_created >= start_dt)
        if end_dt:
            query = query.where(User.date_created < end_dt)

        query = query.group_by(period_col).order_by(period_col)

        result = await db.execute(query)
        data = []
        total_registrations = 0

        for row in result:
            period_str = row.period.strftime("%Y-%m-%d") if groupby == "day" else row.period.isoformat()
            data.append({
                "period": period_str,
                "registrations": row.registrations
            })
            total_registrations += row.registrations

        return {
            "data": data,
            "total_registrations": total_registrations,
            "groupby": groupby,
            "start_date": start_date,
            "end_date": end_date,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}


@router.get("/api/analytics/average-session-time", tags=["Analytics"])
async def get_average_session_time(
    db: AsyncDatabase,
    start_date: str = None,  # YYYY-MM-DD
    end_date: str = None,    # YYYY-MM-DD
):
    """
    Get average session time by day
    Perfect for tracking engagement trends over time
    """
    try:
        # Default to last 30 days if no dates provided
        if not start_date and not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        # Parse dates
        start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1) if end_date else None

        # Query for daily average session times
        query = select(
            func.date(SessionActivity.started_at).label("date"),
            func.count().label("total_sessions"),
            func.avg(SessionActivity.active_seconds).label("avg_session_seconds"),
            func.sum(SessionActivity.active_seconds).label("total_active_seconds")
        )

        # Add date filters
        if start_dt:
            query = query.where(SessionActivity.started_at >= start_dt)
        if end_dt:
            query = query.where(SessionActivity.started_at < end_dt)

        query = query.group_by(func.date(SessionActivity.started_at)).order_by("date")

        result = await db.execute(query)
        data = []
        total_sessions = 0
        total_time = 0

        for row in result:
            avg_minutes = round(row.avg_session_seconds / 60, 1) if row.avg_session_seconds else 0
            total_minutes = round(row.total_active_seconds / 60, 1) if row.total_active_seconds else 0

            data.append({
                "date": row.date.strftime("%Y-%m-%d"),
                "total_sessions": row.total_sessions,
                "avg_session_seconds": round(row.avg_session_seconds or 0, 1),
                "avg_session_minutes": avg_minutes,
                "total_active_minutes": total_minutes
            })
            total_sessions += row.total_sessions
            total_time += (row.total_active_seconds or 0)

        overall_avg_minutes = round(total_time / 60 / total_sessions, 1) if total_sessions > 0 else 0

        return {
            "data": data,
            "overall_stats": {
                "total_sessions": total_sessions,
                "overall_avg_minutes": overall_avg_minutes,
                "total_hours": round(total_time / 3600, 1)
            },
            "start_date": start_date,
            "end_date": end_date,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}


@router.get("/api/analytics/stats-summary", tags=["Analytics"])
async def get_stats_summary(
    db: AsyncDatabase,
    include_superusers: bool = Query(False, description="Include superusers in statistics")
):
    """Get summary statistics for dashboard top cards"""
    # Total registered users
    if include_superusers:
        total_users = await db.scalar(select(func.count(User.id)))
    else:
        total_users = await db.scalar(
            select(func.count(User.id))
            .where(User.is_superuser == False)
        )

    # Active users today (unique devices with sessions in last 24 hours)
    cutoff_24h = datetime.now(timezone.utc) - timedelta(hours=24)
    if include_superusers:
        active_users_today = await db.scalar(
            select(func.count(func.distinct(SessionActivity.device_id)))
            .where(SessionActivity.started_at > cutoff_24h)
        )
    else:
        active_users_today = await db.scalar(
            select(func.count(func.distinct(SessionActivity.device_id)))
            .outerjoin(User, SessionActivity.user_id == User.id)
            .where(
                and_(
                    SessionActivity.started_at > cutoff_24h,
                    (SessionActivity.user_id.is_(None)) | (User.is_superuser == False)
                )
            )
        )

    # Total games played (puzzle attempts)
    if include_superusers:
        total_games = await db.scalar(select(func.count(FreeplayPuzzleAttempt.id)))
    else:
        total_games = await db.scalar(
            select(func.count(FreeplayPuzzleAttempt.id))
            .outerjoin(User, FreeplayPuzzleAttempt.user_id == User.id)
            .where((FreeplayPuzzleAttempt.user_id.is_(None)) | (User.is_superuser == False))
        )

    # Average session duration
    if include_superusers:
        avg_session_seconds = await db.scalar(
            select(func.avg(SessionActivity.active_seconds))
            .where(SessionActivity.active_seconds > 0)
        )
    else:
        avg_session_seconds = await db.scalar(
            select(func.avg(SessionActivity.active_seconds))
            .outerjoin(User, SessionActivity.user_id == User.id)
            .where(
                and_(
                    SessionActivity.active_seconds > 0,
                    (SessionActivity.user_id.is_(None)) | (User.is_superuser == False)
                )
            )
        )
    avg_session_minutes = round(avg_session_seconds / 60, 1) if avg_session_seconds else 0

    return {
        "total_users": total_users or 0,
        "active_users_today": active_users_today or 0,
        "total_games_played": total_games or 0,
        "avg_session_duration_minutes": avg_session_minutes,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/api/analytics/game-statistics", tags=["Analytics"])
async def get_game_statistics(
    db: AsyncDatabase,
    include_superusers: bool = Query(False, description="Include superusers in statistics"),
    user_filter: Optional[str] = Query(None, description="Filter by user type: 'logged_in', 'anonymous', or 'all'"),
    game_type: Optional[List[str]] = Query(None, description="Filter by game types"),
    game_size: Optional[List[str]] = Query(None, description="Filter by game sizes"),
    difficulty: Optional[List[str]] = Query(None, description="Filter by difficulty levels"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """
    Get game-related statistics with filtering options
    """
    try:
        # Build base query with joins, including User join for superuser exclusion
        query = (
            select(
                func.date(FreeplayPuzzleAttempt.created_at).label("date"),
                func.count(FreeplayPuzzleAttempt.id).label("total_games"),
                func.sum(case((FreeplayPuzzleAttempt.is_solved == True, 1), else_=0)).label("solved_games"),
                func.sum(case((FreeplayPuzzleAttempt.used_tutorial == True, 1), else_=0)).label("tutorial_games"),
                func.count(func.distinct(
                    case((FreeplayPuzzleAttempt.user_id.is_not(None), FreeplayPuzzleAttempt.user_id), else_=None)
                )).label("unique_logged_in_users"),
                func.count(func.distinct(
                    case((FreeplayPuzzleAttempt.user_id.is_(None), FreeplayPuzzleAttempt.device_id), else_=None)
                )).label("unique_anonymous_users")
            )
            .select_from(FreeplayPuzzleAttempt)
            .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
            .outerjoin(User, FreeplayPuzzleAttempt.user_id == User.id)
        )

        # Apply filters
        filters = []

        # Conditionally exclude superusers
        if not include_superusers:
            filters.append(
                (FreeplayPuzzleAttempt.user_id.is_(None)) |
                (User.is_superuser == False)
            )

        # User type filter
        if user_filter == "logged_in":
            filters.append(FreeplayPuzzleAttempt.user_id.is_not(None))
        elif user_filter == "anonymous":
            filters.append(FreeplayPuzzleAttempt.user_id.is_(None))

        # Game type filter
        if game_type:
            filters.append(Puzzle.puzzle_type.in_(game_type))

        # Game size filter
        if game_size:
            filters.append(Puzzle.puzzle_size.in_(game_size))

        # Difficulty filter
        if difficulty:
            filters.append(Puzzle.puzzle_difficulty.in_(difficulty))

        # Date filters
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            filters.append(FreeplayPuzzleAttempt.created_at >= start_dt)
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            filters.append(FreeplayPuzzleAttempt.created_at < end_dt)

        # Apply all filters
        if filters:
            query = query.where(and_(*filters))

        # Group by date and order
        query = query.group_by(func.date(FreeplayPuzzleAttempt.created_at)).order_by("date")

        result = await db.execute(query)
        data = []

        for row in result:
            solved_percentage = round((row.solved_games / row.total_games * 100), 1) if row.total_games > 0 else 0
            tutorial_percentage = round((row.tutorial_games / row.total_games * 100), 1) if row.total_games > 0 else 0

            data.append({
                "date": row.date.strftime("%Y-%m-%d"),
                "total_games": row.total_games,
                "solved_games": row.solved_games,
                "abandoned_games": row.total_games - row.solved_games,
                "tutorial_games": row.tutorial_games,
                "solved_percentage": solved_percentage,
                "tutorial_percentage": tutorial_percentage,
                "unique_logged_in_users": row.unique_logged_in_users,
                "unique_anonymous_users": row.unique_anonymous_users
            })

        return {
            "data": data,
            "filters": {
                "user_filter": user_filter,
                "game_type": game_type,
                "game_size": game_size,
                "difficulty": difficulty,
                "start_date": start_date,
                "end_date": end_date
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}


@router.get("/api/analytics/user-engagement", tags=["Analytics"])
async def get_user_engagement(
    db: AsyncDatabase,
    include_superusers: bool = Query(False, description="Include superusers in statistics"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """
    Get user engagement metrics
    """
    try:
        # Base filters for date range
        filters = []
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            filters.append(FreeplayPuzzleAttempt.created_at >= start_dt)
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            filters.append(FreeplayPuzzleAttempt.created_at < end_dt)

        # Games played distribution (for users with accounts)
        if include_superusers:
            games_per_user_query = (
                select(
                    FreeplayPuzzleAttempt.user_id,
                    func.count(FreeplayPuzzleAttempt.id).label("games_played")
                )
                .where(FreeplayPuzzleAttempt.user_id.is_not(None))
            )
        else:
            games_per_user_query = (
                select(
                    FreeplayPuzzleAttempt.user_id,
                    func.count(FreeplayPuzzleAttempt.id).label("games_played")
                )
                .join(User, FreeplayPuzzleAttempt.user_id == User.id)
                .where(
                    and_(
                        FreeplayPuzzleAttempt.user_id.is_not(None),
                        User.is_superuser == False
                    )
                )
            )

        if filters:
            games_per_user_query = games_per_user_query.where(and_(*filters))

        games_per_user_query = games_per_user_query.group_by(FreeplayPuzzleAttempt.user_id)

        games_per_user_result = await db.execute(games_per_user_query)
        games_counts = [row.games_played for row in games_per_user_result]

        # Calculate distribution
        users_1_game = sum(1 for count in games_counts if count == 1)
        users_5_games = sum(1 for count in games_counts if 2 <= count <= 5)
        users_10_plus_games = sum(1 for count in games_counts if count > 10)

        # Average games per person (logged in users)
        avg_games_per_person = sum(games_counts) / len(games_counts) if games_counts else 0

        # Average session time per person
        if include_superusers:
            session_time_query = (
                select(
                    SessionActivity.user_id,
                    func.avg(SessionActivity.active_seconds).label("avg_session_time")
                )
                .where(SessionActivity.user_id.is_not(None))
            )
        else:
            session_time_query = (
                select(
                    SessionActivity.user_id,
                    func.avg(SessionActivity.active_seconds).label("avg_session_time")
                )
                .join(User, SessionActivity.user_id == User.id)
                .where(
                    and_(
                        SessionActivity.user_id.is_not(None),
                        User.is_superuser == False
                    )
                )
            )

        if filters:
            # Apply date filters to session data too
            session_filters = []
            if start_date:
                session_filters.append(SessionActivity.started_at >= start_dt)
            if end_date:
                session_filters.append(SessionActivity.started_at < end_dt)
            if session_filters:
                session_time_query = session_time_query.where(and_(*session_filters))

        session_time_query = session_time_query.group_by(SessionActivity.user_id)
        session_time_result = await db.execute(session_time_query)

        session_times = [row.avg_session_time for row in session_time_result if row.avg_session_time]
        avg_session_minutes = sum(session_times) / len(session_times) / 60 if session_times else 0

        return {
            "games_played_distribution": {
                "users_played_1_game": users_1_game,
                "users_played_2_to_5_games": users_5_games,
                "users_played_10_plus_games": users_10_plus_games,
                "total_users_with_games": len(games_counts)
            },
            "averages": {
                "avg_games_per_person": round(avg_games_per_person, 1),
                "avg_session_duration_minutes": round(avg_session_minutes, 1)
            },
            "filters": {
                "start_date": start_date,
                "end_date": end_date
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}


@router.get("/api/analytics/game-types-breakdown", tags=["Analytics"])
async def get_game_types_breakdown(
    db: AsyncDatabase,
    include_superusers: bool = Query(False, description="Include superusers in statistics"),
    user_filter: Optional[str] = Query(None, description="Filter by user type: 'logged_in', 'anonymous', or 'all'"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """
    Get breakdown of games played by type, size, and difficulty
    """
    try:
        # Base query with User join for superuser exclusion
        query = (
            select(
                Puzzle.puzzle_type,
                Puzzle.puzzle_size,
                Puzzle.puzzle_difficulty,
                func.count(FreeplayPuzzleAttempt.id).label("games_played"),
                func.sum(case((FreeplayPuzzleAttempt.is_solved == True, 1), else_=0)).label("solved_games"),
                func.count(func.distinct(
                    case((FreeplayPuzzleAttempt.user_id.is_not(None), FreeplayPuzzleAttempt.user_id),
                         else_=FreeplayPuzzleAttempt.device_id)
                )).label("unique_players")
            )
            .select_from(FreeplayPuzzleAttempt)
            .join(Puzzle, FreeplayPuzzleAttempt.puzzle_id == Puzzle.id)
            .outerjoin(User, FreeplayPuzzleAttempt.user_id == User.id)
        )

        # Apply filters
        filters = []

        # Conditionally exclude superusers
        if not include_superusers:
            filters.append(
                (FreeplayPuzzleAttempt.user_id.is_(None)) |
                (User.is_superuser == False)
            )

        # User type filter
        if user_filter == "logged_in":
            filters.append(FreeplayPuzzleAttempt.user_id.is_not(None))
        elif user_filter == "anonymous":
            filters.append(FreeplayPuzzleAttempt.user_id.is_(None))

        # Date filters
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            filters.append(FreeplayPuzzleAttempt.created_at >= start_dt)
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            filters.append(FreeplayPuzzleAttempt.created_at < end_dt)

        if filters:
            query = query.where(and_(*filters))

        # Group by game properties
        query = query.group_by(
            Puzzle.puzzle_type,
            Puzzle.puzzle_size,
            Puzzle.puzzle_difficulty
        ).order_by(
            Puzzle.puzzle_type,
            Puzzle.puzzle_size,
            Puzzle.puzzle_difficulty
        )

        result = await db.execute(query)
        data = []

        for row in result:
            solve_rate = round((row.solved_games / row.games_played * 100), 1) if row.games_played > 0 else 0

            data.append({
                "puzzle_type": row.puzzle_type,
                "puzzle_size": row.puzzle_size,
                "puzzle_difficulty": row.puzzle_difficulty,
                "games_played": row.games_played,
                "solved_games": row.solved_games,
                "solve_rate_percentage": solve_rate,
                "unique_players": row.unique_players
            })

        return {
            "data": data,
            "filters": {
                "user_filter": user_filter,
                "start_date": start_date,
                "end_date": end_date
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}
