from collections.abc import Generator, AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import delete

from app.main import app
from app.dependencies import get_async_session
from app.models.base import Base
from app.models.device import Device, DeviceThumbmark
from app.modules.auth.models import User

# Use in-memory SQLite with async support
test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
async_session_maker = async_sessionmaker(test_engine, expire_on_commit=False)


async def get_test_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Clean up after each test
    async with async_session_maker() as session:
        await session.execute(delete(User))
        await session.execute(delete(DeviceThumbmark))
        await session.execute(delete(Device))
        await session.commit()


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_async_session] = get_test_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def mock_send_verification_email():
    with patch("app.modules.auth.routes.send_verification_email", new_callable=AsyncMock) as mock:
        yield mock
