"""test configuration — spins up a disposable PostgreSQL container per session."""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

from testcontainers.postgres import PostgresContainer

from app.main import app
from app.dependencies import get_async_session
from app.models import Base


# --- database ---

@pytest.fixture(scope="session")
def postgres_url():
    """start a PostgreSQL container for the test session."""
    with PostgresContainer("postgres:18") as pg:
        url = pg.get_connection_url()
        async_url = url.replace("psycopg2", "asyncpg")
        yield async_url


@pytest_asyncio.fixture
async def db(postgres_url) -> AsyncGenerator[AsyncSession, None]:
    """fresh database for each test — creates tables, yields session, drops tables."""
    engine = create_async_engine(postgres_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# --- test client ---

@pytest_asyncio.fixture
async def client(postgres_url) -> AsyncGenerator[AsyncClient, None]:
    """async test client with its own fresh database."""
    engine = create_async_engine(postgres_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async def override_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()
