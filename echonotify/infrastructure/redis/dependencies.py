"""Redis dependencies for FastAPI dependency injection."""

from typing import AsyncGenerator

from echonotify.infrastructure.redis.client import RedisCache, RedisSession
from echonotify.settings import Settings


async def get_redis_cache() -> AsyncGenerator[RedisCache, None]:
    """Dependency to get Redis cache client."""
    settings = Settings()
    cache = RedisCache(settings)
    try:
        yield cache
    finally:
        await cache.disconnect()


async def get_redis_session() -> AsyncGenerator[RedisSession, None]:
    """Dependency to get Redis session client."""
    settings = Settings()
    session = RedisSession(settings)
    try:
        yield session
    finally:
        await session.disconnect()
