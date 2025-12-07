import inspect
from functools import wraps
from typing import Any, Callable, Coroutine

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
