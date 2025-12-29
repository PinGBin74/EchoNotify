import inspect
from functools import wraps
from typing import Any, Callable, Coroutine, Dict, Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from echonotify.exception import (
    TokenExpiredError,
    TokenNotCorrectError,
    UserNotFoundError,
)
from echonotify.users.user_profile.models import UserProfile


def check_user_exists(func: Callable[..., Coroutine[Any, Any, Any]]):
    """
    Decorator to check if a user exists before calling the decorated function.

    The decorated function must have `session` and `user_id` as parameters.
    If the user does not exist, it will raise a 404 error.
    """

    @wraps(func)
    async def wrapper(
        *args,
        session: AsyncSession,
        user_id: int,
        **kwargs,
    ):
        user = await session.get(UserProfile, user_id)
        if not user:
            raise UserNotFoundError("User not found")

        return await func(*args, session=session, user_id=user_id, **kwargs)

    return wrapper


def handle_token_errors(func):
    """
    Decorator to handle token-related errors.

    If the token is expired or incorrect, it raises a 401 error.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            if inspect.isawaitable(result):
                return await result
            return result
        except (
            TokenExpiredError,
            TokenNotCorrectError,
            UserNotFoundError,
        ) as e:
            raise HTTPException(status_code=401, detail=e.detail) from e

    return wrapper


def celery_task(
    name: Optional[str] = None,
    bind: bool = False,
    autoretry_for: Optional[tuple] = None,
    retry_kwargs: Optional[Dict[str, Any]] = None,
    retry_backoff: bool = True,
    retry_backoff_max: int = 700,
    retry_jitter: bool = True,
    **kwargs,
):
    """Декоратор для регистрации Celery задачи"""

    def decorator(func: Callable):
        from echonotify.celery_app import app

        task_name = name or f"echonotify.{func.__module__}.{func.__name__}"

        return app.task(
            name=task_name,
            bind=bind,
            autoretry_for=autoretry_for,
            retry_kwargs=retry_kwargs or {},
            retry_backoff=retry_backoff,
            retry_backoff_max=retry_backoff_max,
            retry_jitter=retry_jitter,
            **kwargs,
        )(func)

    return decorator


def celery_periodic_task(
    schedule: Any,
    name: Optional[str] = None,
    args: Optional[tuple] = None,
    kwargs: Optional[Dict[str, Any]] = None,
    **task_kwargs,
):
    """Декоратор для регистрации периодической Celery задачи"""

    def decorator(func: Callable):
        from echonotify.celery_app import app

        task_name = name or f"echonotify.{func.__module__}.{func.__name__}"

        app.conf.beat_schedule[task_name] = {
            "task": task_name,
            "schedule": schedule,
            "args": args or (),
            "kwargs": kwargs or {},
        }

        return celery_task(name=task_name, **task_kwargs)(func)

    return decorator
