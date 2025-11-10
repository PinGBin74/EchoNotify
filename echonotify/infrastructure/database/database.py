import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from echonotify.settings import Settings

connect_args = {}
if os.getenv("ENVIRONMENT") == "production":
    connect_args["ssl"] = "require"

async_engine = create_async_engine(
    Settings().db_url,
    future=True,
    echo=True,
    pool_pre_ping=True,
    connect_args=connect_args,
)

AsyncSessionFactory = async_sessionmaker(
    async_engine,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        yield session
