"""Celery tasks for background processing."""

import logging
from datetime import datetime, timedelta

from celery import shared_task

from echonotify.auth.utils import utc_now_naive
from echonotify.infrastructure.database.database import get_db_session
from echonotify.infrastructure.redis.client import (
    get_redis_cache,
    get_redis_session,
)
from echonotify.settings import Settings

logger = logging.getLogger(__name__)


@shared_task(
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3},
    retry_backoff=True,
)
async def cleanup_expired_sessions_task():
    """Clean up expired sessions"""
    settings = Settings()
    redis_session = get_redis_session(settings)

    async with redis_session:
        expired_count = 0

        keys = await redis_session.scan_keys("session:*", count=1000)

        for key in keys:
            ttl = await redis_session.ttl(key)
            if ttl < 0:
                await redis_session.delete(key)
                expired_count += 1

    logger.info(f"Cleaned up {expired_count} expired sessions")
    return expired_count


@shared_task(
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2},
    retry_backoff=True,
)
async def cleanup_old_orders_task():
    """Clean up old orders older than 30 days."""
    try:
        async for session in get_db_session():
            from sqlalchemy import delete

            from echonotify.orders.models import Order

            cutoff_date = datetime.utcnow() - timedelta(days=30)

            stmt = delete(Order).where(
                Order.created_at < cutoff_date,
                Order.status.in_(["delivered", "cancelled"]),
            )

            result = await session.execute(stmt)
            await session.commit()

            deleted_count = result.rowcount
            logger.info(f"Deleted {deleted_count} old orders")
            return deleted_count

    except Exception as e:
        logger.error(f"Failed to cleanup old orders: {e}")
        raise


@shared_task(
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2},
    retry_backoff=True,
)
async def cleanup_old_messages_task():
    """Clean up old chat messages older than 7 days."""
    try:
        async for session in get_db_session():
            from sqlalchemy import delete

            from echonotify.chat.models import Message

            cutoff_date = utc_now_naive() - timedelta(days=7)

            stmt = delete(Message).where(Message.created_at < cutoff_date)

            result = await session.execute(stmt)
            await session.commit()

            deleted_count = result.rowcount
            logger.info(f"Deleted {deleted_count} old messages")
            return deleted_count

    except Exception as e:
        logger.error(f"Failed to cleanup old messages: {e}")
        raise


@shared_task(
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 1},
    retry_backoff=False,
)
async def health_check():
    """Perform system health check."""
    try:
        settings = Settings()

        redis_cache = get_redis_cache(settings)
        redis_session = get_redis_session(settings)

        async with redis_cache:
            await redis_cache.set("health_check", "ok", ttl=60)
            redis_value = await redis_cache.get("health_check")

        async with redis_session:
            session_health = await redis_session.health_check()

        db_health = False
        async for session in get_db_session():
            await session.execute("SELECT 1")
            db_health = True
            break

        if redis_value == "ok" and session_health and db_health:
            logger.info("Health check completed successfully")
            return True
        else:
            raise Exception("Health check failed")

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise
