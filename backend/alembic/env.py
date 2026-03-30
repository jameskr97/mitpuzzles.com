import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

# model imports TODO(james): replace noqa lines with a * import (move models to one module?)
from app.models import Base
from app.modules.authentication import User, OAuthAccount, AccessToken # noqa: F401
from app.modules.tracking import Device, DeviceThumbmark  # noqa: F401
from app.modules.experiments import ExperimentRun, ExperimentProlificData  # noqa: F401
from app.modules.feedback import Feedback  # noqa: F401
from app.modules.puzzle import Puzzle, FreeplayPuzzleAttempt, UserActivityDaily  # noqa: F401
from app.modules.puzzle_analysis import BackgroundJob, AnalysisJobPuzzle  # noqa: F401
from app.modules.user_profile import UserProfile  # noqa: F401
from app.modules.push_notifications import PushSubscription  # noqa: F401
from app.modules.data_export import GeneratedExport  # noqa: F401
from app.modules.news import NewsPost  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata


target_metadata = Base.metadata


async def run_async_migrations():
    """Run migrations in async mode."""
    if database_url := os.getenv("DATABASE_URL"):
        config.set_main_option("sqlalchemy.url", database_url)

    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def do_run_migrations(connection):
    """Helper function to run migrations with sync interface."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    if database_url := os.getenv("DATABASE_URL"):
        config.set_main_option("sqlalchemy.url", database_url)
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    asyncio.run(run_async_migrations())
    # if database_url := os.getenv("DATABASE_URL"):
    #     config.set_main_option("sqlalchemy.url", database_url)
    #
    # connectable = engine_from_config(
    #     config.get_section(config.config_ini_section, {}),
    #     prefix="sqlalchemy.",
    #     poolclass=pool.NullPool,
    # )
    #
    # with connectable.connect() as connection:
    #     context.configure(connection=connection, target_metadata=target_metadata)
    #
    #     with context.begin_transaction():
    #         context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
