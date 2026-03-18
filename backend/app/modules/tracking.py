import uuid
from datetime import datetime
from typing import Dict
from typing import List

import uuid6
from fastapi import APIRouter, Response, Query
from fastapi.responses import JSONResponse
from fastapi import Request, HTTPException
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import String, DateTime, ForeignKey, Integer, Boolean, Index, func, cast, Date, text
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import Session
from sqlalchemy.types import JSON
from datetime import timezone
from typing import Optional

from app.dependencies import AsyncDatabase
from app.models import Base

# Consts
DEVICE_COOKIE_NAME = "device_id"
ONE_YEAR_IN_SECONDS = 60 * 60 * 24 * 365


# Models
class Device(Base):
    __tablename__ = "device"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid6.uuid7)
    user_agent: Mapped[str] = mapped_column(String, nullable=False)

    # Website Visit Tracking
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)
    thumbmarks: Mapped[List["DeviceThumbmark"]] = relationship(back_populates="device", order_by="DeviceThumbmark.date_created")
    session_activities: Mapped[List["SessionActivity"]] = relationship(back_populates="device")


class DeviceThumbmark(Base):
    __tablename__ = "device_thumbmark"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid6.uuid7)
    date_created: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("device.id"), nullable=False)
    ip_address: Mapped[str] = mapped_column(String, nullable=False)
    thumbmark_id: Mapped[str] = mapped_column(String, nullable=False)
    thumbmark_data: Mapped[Dict] = mapped_column(JSON, nullable=False)

    device: Mapped[Device] = relationship(back_populates="thumbmarks")


class SessionActivity(Base):
    """Track individual user sessions for detailed analytics"""
    __tablename__ = "session_activity"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid6.uuid7)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True) # (client-generated UUIDv7)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("device.id"), nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=True)

    # session timing (timezone-aware)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_heartbeat_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # activity metrics
    active_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # session context
    initial_referrer: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)  # IPv6 max length

    # relationships
    device: Mapped[Device] = relationship("Device", back_populates="session_activities")
    # Note: User relationship will be added via registry.configure_mappers()
    # to avoid circular import issues

    # indexes defined after columns
    __table_args__ = (
        Index("idx_session_device_started", device_id, started_at),
        Index("idx_session_user_started", user_id, started_at),
        Index("idx_session_ended_at", ended_at),  # Index for active session queries
    )


# Services
class DeviceService:
    def __init__(self, db: Session):
        self.db: Session = db

    async def put_device(self, http_request: Request, thumbmark_data: Dict):
        # data validation
        if not thumbmark_data or "thumbmark" not in thumbmark_data:
            raise HTTPException(detail="Invalid thumbmark data", status_code=422)

        thumbmark_id = thumbmark_data.get("thumbmark")
        if not thumbmark_id or not isinstance(thumbmark_id, str):
            raise HTTPException(
                detail="thumbmark_data must contain a valid 'thumbmark' string field",
                status_code=422,
            )

        if len(thumbmark_id) != 32:
            raise HTTPException(detail="thumbmark must be a 32 character hex string", status_code=422)

        # Strategy 1: Prefer device_id. If exists, make sure thumbmark_id is same.
        #             If it's not the same, add it to the database.
        device_id = http_request.cookies.get(DEVICE_COOKIE_NAME)

        if device_id:
            try:
                device_uuid = uuid.UUID(device_id)
                device = await self.db.scalar(select(Device).where(Device.id == device_uuid))
            except ValueError:
                # allow to fall through to creating a new device
                device_id = None
                device = None

            if device:
                # device found, check if thumbmark is same as latest
                latest_thumbmark = (
                    (await self.db.execute(select(DeviceThumbmark).where(DeviceThumbmark.device_id == device.id).order_by(DeviceThumbmark.date_created.desc())))
                    .scalars()
                    .first()
                )

                # if the thumbmark is the same, we're done.
                if latest_thumbmark and latest_thumbmark.thumbmark_id == thumbmark_data["thumbmark"]:
                    return device

                # if we got here, the thumbmark is different, so add it.
                thumbmark = DeviceThumbmark(
                    device_id=device.id,
                    ip_address=http_request.client.host,
                    thumbmark_id=thumbmark_data["thumbmark"],
                    thumbmark_data=thumbmark_data,
                )
                self.db.add(thumbmark)
                await self.db.commit()
                return device

            elif device_id:
                # we have a device_id cookie, but it's not in the database.
                # just fall through to creating a new device with a new ID.
                pass

        # Strategy 2: There is no device_id, so we've never seen this user before.
        #             Give them a new device_id (1 year long cookie that refreshes every visit)
        device = Device(user_agent=http_request.headers.get("user-agent"))
        self.db.add(device)
        await self.db.flush()

        thumbmark = DeviceThumbmark(
            device_id=device.id,
            ip_address=http_request.client.host,
            thumbmark_id=thumbmark_data["thumbmark"],
            thumbmark_data=thumbmark_data,
        )
        self.db.add(thumbmark)
        await self.db.commit()
        await self.db.refresh(device)
        return device


class SessionTrackingService:
    def __init__(self, db: Session):
        self.db: Session = db

    async def handle_heartbeat(self, session_id: str, device_id: uuid.UUID, user_id: Optional[uuid.UUID],
                              active_duration_delta: int, ip_address: str, initial_referrer: Optional[str] = None):
        """Handle a heartbeat from the client - create or update session"""
        now = datetime.now(timezone.utc)

        # Try to find existing session
        session = await self.db.scalar(
            select(SessionActivity).where(SessionActivity.session_id == session_id)
        )

        if session:
            # Update existing session
            session.last_heartbeat_at = now
            session.active_seconds += active_duration_delta
            # Update user_id if user logged in during session
            if user_id and not session.user_id:
                session.user_id = user_id
        else:
            # Create new session
            session = SessionActivity(
                session_id=session_id,
                device_id=device_id,
                user_id=user_id,
                started_at=now,
                last_heartbeat_at=now,
                active_seconds=active_duration_delta,
                ip_address=ip_address,
                initial_referrer=initial_referrer
            )
            self.db.add(session)

        await self.db.commit()
        return session


    async def get_active_users_count(self) -> int:
        """Get count of active users (devices with heartbeat in last 2 minutes)"""
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=2)

        count = await self.db.scalar(
            select(func.count(func.distinct(SessionActivity.device_id)))
            .where(
                SessionActivity.ended_at.is_(None),  # Session is still active
                SessionActivity.last_heartbeat_at > cutoff
            )
        )

        return count or 0


# Routers
router = APIRouter()


class DevicePut(BaseModel):
    thumbmark: Dict = Field(None, description="Thumbmark Data")


class DeviceResponse(BaseModel):
    device_id: str


class HeartbeatRequest(BaseModel):
    session_id: str = Field(..., description="Client-generated UUIDv7 session identifier")
    device_id: uuid.UUID = Field(..., description="Device ID from cookie")
    user_id: Optional[uuid.UUID] = Field(None, description="User ID if logged in")
    active_duration_delta: int = Field(..., description="Seconds of activity since last heartbeat")
    initial_referrer: Optional[str] = Field(None, description="Initial referrer for new sessions")




@router.put("/api/device", tags=["Device Tracking"], response_model=DeviceResponse)
async def create_device(http_request: Request, device: DevicePut, db: AsyncDatabase):
    """
    Create a new device and thumbmark record
    - Thumbmark record only created if the given thumbmark id is different
    - New device only created if the request does not have a device_id cookie
    """
    ds = DeviceService(db)
    device = await ds.put_device(http_request, device.thumbmark)
    response = JSONResponse(
        status_code=200,
        content={"device_id": str(device.id)}
    )
    from app.config import settings, DeploymentEnvironment
    response.set_cookie(
        DEVICE_COOKIE_NAME,
        value=str(device.id),
        httponly=True,
        secure=settings.ENVIRONMENT != DeploymentEnvironment.LOCAL,
        max_age=ONE_YEAR_IN_SECONDS,
    )
    return response


@router.post("/api/tracking/heartbeat", tags=["Session Tracking"])
async def session_heartbeat(http_request: Request, heartbeat: HeartbeatRequest, db: AsyncDatabase):
    """
    Receive session heartbeat from client
    - Creates new session if session_id doesn't exist
    - Updates existing session with new activity duration
    - Tracks user login state changes during session
    """
    session_service = SessionTrackingService(db)

    session = await session_service.handle_heartbeat(
        session_id=heartbeat.session_id,
        device_id=heartbeat.device_id,
        user_id=heartbeat.user_id,
        active_duration_delta=heartbeat.active_duration_delta,
        ip_address=http_request.client.host,
        initial_referrer=heartbeat.initial_referrer
    )

    return {
        "session_id": session.session_id,
        "active_seconds": session.active_seconds,
        "status": "updated" if session.started_at != session.last_heartbeat_at else "created"
    }


@router.get("/api/admin/devices", tags=["Admin"])
async def list_devices(
    db: AsyncDatabase,
    search: Optional[str] = Query(None, description="Search by device ID or user agent"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    List all devices with metadata for admin use.
    Returns device ID, user agent, first/last seen, and session count.
    """
    from sqlalchemy import select, func, desc

    # Build query
    query = (
        select(
            Device.id,
            Device.user_agent,
            Device.first_seen,
            Device.last_seen,
            func.count(SessionActivity.id).label('session_count')
        )
        .outerjoin(SessionActivity, Device.id == SessionActivity.device_id)
        .group_by(Device.id)
        .order_by(desc(Device.last_seen))
    )

    # Apply search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            Device.user_agent.ilike(search_pattern) |
            Device.id.cast(String).ilike(search_pattern)
        )

    # Get total count
    count_query = select(func.count(Device.id))
    if search:
        search_pattern = f"%{search}%"
        count_query = count_query.where(
            Device.user_agent.ilike(search_pattern) |
            Device.id.cast(String).ilike(search_pattern)
        )
    total_count = await db.scalar(count_query)

    # Apply pagination
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    devices = result.all()

    return {
        "devices": [
            {
                "id": str(d.id),
                "user_agent": d.user_agent,
                "first_seen": d.first_seen.isoformat() if d.first_seen else None,
                "last_seen": d.last_seen.isoformat() if d.last_seen else None,
                "session_count": d.session_count,
                "label": f"{d.user_agent[:50]}..." if d.user_agent and len(d.user_agent) > 50 else d.user_agent
            }
            for d in devices
        ],
        "total_count": total_count,
        "limit": limit,
        "offset": offset
    }


@router.get("/api/admin/users", tags=["Admin"])
async def list_users(
    db: AsyncDatabase,
    search: Optional[str] = Query(None, description="Search by username or email"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    List all users with metadata for admin use.
    Returns user ID, username, email, and attempt count.
    """
    from sqlalchemy import select, func, desc
    from app.modules.authentication import User
    from app.modules.puzzle import FreeplayPuzzleAttempt

    # Build query
    query = (
        select(
            User.id,
            User.username,
            User.email,
            User.date_created,
            func.count(FreeplayPuzzleAttempt.id).label('attempt_count')
        )
        .outerjoin(FreeplayPuzzleAttempt, User.id == FreeplayPuzzleAttempt.user_id)
        .group_by(User.id)
        .order_by(User.date_created.asc())
    )

    # Apply search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            User.username.ilike(search_pattern) |
            User.email.ilike(search_pattern)
        )

    # Get total count
    count_query = select(func.count(User.id))
    if search:
        search_pattern = f"%{search}%"
        count_query = count_query.where(
            User.username.ilike(search_pattern) |
            User.email.ilike(search_pattern)
        )
    total_count = await db.scalar(count_query)

    # Apply pagination
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    users = result.all()

    return {
        "users": [
            {
                "id": str(u.id),
                "username": u.username,
                "email": u.email,
                "date_created": u.date_created.isoformat() if u.date_created else None,
                "attempt_count": u.attempt_count,
                "label": u.username or u.email or str(u.id)[:8]
            }
            for u in users
        ],
        "total_count": total_count,
        "limit": limit,
        "offset": offset
    }
