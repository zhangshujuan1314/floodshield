"""Async Alembic environment for FloodShield.

Uses asyncpg for async migrations against PostgreSQL + PostGIS.
Reads DATABASE_URL from the environment; falls back to the project default.
"""
from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ---------------------------------------------------------------------------
# Alembic Config object
# ---------------------------------------------------------------------------
config = context.config

# Configure Python logging from the alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Inject DATABASE_URL from the environment so we never hardcode credentials
# ---------------------------------------------------------------------------
database_url = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://floodshield:floodshield@localhost:5432/floodshield",
)
config.set_main_option("sqlalchemy.url", database_url)

# ---------------------------------------------------------------------------
# Import ALL models so Alembic's autogenerate can detect them
# ---------------------------------------------------------------------------
from app.core.database import Base  # noqa: E402
from app.models.base import (  # noqa: E402
    AuditLog,
    HazardReport,
    NotificationDelivery,
    Observation,
    OfficialAlert,
    Organization,
    RiskSnapshot,
    RoadEvent,
    RouteRequest,
    RouteResult,
    Shelter,
    Task,
    User,
)

# Tell Alembic which metadata to compare against
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline mode – generates SQL scripts without a live DB connection
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with just a URL and not an Engine, though an
    Engine is acceptable here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online mode – connects to the DB and runs migrations
# ---------------------------------------------------------------------------
def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the given synchronous connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine and associate a
    connection with the context for online migrations."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode via the async engine."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
