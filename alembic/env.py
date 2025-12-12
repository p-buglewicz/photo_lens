"""Alembic environment configuration (synchronous)."""

from logging.config import fileConfig
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from alembic import context  # type: ignore[attr-defined]
import os
import sys

# Add the project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.app.core.config import settings
from backend.app.models.base import Base

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _normalize_sync_url(url: str) -> str:
    """Ensure we use a synchronous driver for Alembic migrations."""
    if "+asyncpg" in url:
        return url.replace("+asyncpg", "+psycopg")
    if url.startswith("postgresql.asyncpg://"):
        return url.replace("postgresql.asyncpg://", "postgresql+psycopg://", 1)
    return url


# Set sqlalchemy.url from environment (force sync driver)
config.set_main_option("sqlalchemy.url", _normalize_sync_url(settings.database_url))

# add your model's MetaData object here
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: object) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (sync engine)."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = _normalize_sync_url(settings.database_url)

    connectable = create_engine(
        _normalize_sync_url(settings.database_url),
        echo=False,
        poolclass=NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
