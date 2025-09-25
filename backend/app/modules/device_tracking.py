import uuid
from datetime import datetime
from typing import Dict
from typing import List

import uuid6
from fastapi import APIRouter, Response
from fastapi import Request, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import Session
from sqlalchemy.types import JSON

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


class DeviceThumbmark(Base):
    __tablename__ = "device_thumbmark"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid6.uuid7)
    date_created: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("device.id"), nullable=False)
    ip_address: Mapped[str] = mapped_column(String, nullable=False)
    thumbmark_id: Mapped[str] = mapped_column(String, nullable=False)
    thumbmark_data: Mapped[Dict] = mapped_column(JSON, nullable=False)

    device: Mapped[Device] = relationship(back_populates="thumbmarks")


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


# Routers
router = APIRouter()


class DevicePut(BaseModel):
    thumbmark: Dict = Field(None, description="Thumbmark Data")


@router.put("/api/device", tags=["Device Tracking"])
async def create_device(http_request: Request, device: DevicePut, db: AsyncDatabase):
    """
    Create a new device and thumbmark record
    - Thumbmark record only created if the given thumbmark id is different
    - New device only created if the request does not have a device_id cookie
    """
    ds = DeviceService(db)
    device = await ds.put_device(http_request, device.thumbmark)
    response = Response(status_code=202)
    response.set_cookie(
        DEVICE_COOKIE_NAME,
        value=str(device.id),
        httponly=True,
        secure=True,
        max_age=ONE_YEAR_IN_SECONDS,
    )
    return response
