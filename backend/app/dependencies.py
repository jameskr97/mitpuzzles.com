from typing import Annotated
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from fastapi import Depends, Request, HTTPException

from app.config import settings
from app.models import Base

import uuid


engine = create_async_engine(str(settings.DATABASE_URL))
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_device_id(request: Request) -> uuid.UUID:
    """
    Extract and validate device ID from cookie.
    Raises HTTPException if device ID is missing or invalid.
    """
    from app.modules.device_tracking import DEVICE_COOKIE_NAME

    device_id_str = request.cookies.get(DEVICE_COOKIE_NAME)
    if not device_id_str:
        raise HTTPException(status_code=400, detail="Device tracking cookie not found. Please enable cookies.")

    try:
        return uuid.UUID(device_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid device ID format")


AsyncDatabase = Annotated[AsyncSession, Depends(get_async_session)]
