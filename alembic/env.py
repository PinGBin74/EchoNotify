import asyncio
from logging.config import fileConfig
import os

from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from echonotify.infrastructure.database.models import Base
from echonotify.settings import Settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

DATABASE_URL = os.getenv("DATABASE_URL") or Settings().db_url


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        include_schemas=False,
        version_table_schema=target_metadata.schema,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    """Run migrations in 'online' mode with async engine"""
    connectable = create_async_engine(DATABASE_URL, future=True)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(run_migrations_online())
    else:
        import threading

        _state = {"exc": None}

        def _runner():
            try:
                asyncio.run(run_migrations_online())
            except BaseException as exc:
                _state["exc"] = exc

        thread = threading.Thread(target=_runner)
        thread.start()
        thread.join()
        if _state["exc"]:
            raise _state["exc"]
