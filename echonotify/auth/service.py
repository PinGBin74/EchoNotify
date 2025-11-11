from datetime import datetime, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from echonotify.config import logging
from echonotify.exceptions import TokenExpiredError, TokenNotCorrectError
from echonotify.settings import Settings

logger = logging.getLogger(__name__)

_pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
settings = Settings()


def get_user_id_from_access_token(access_token: str) -> int:
    """Extract user ID from JWT access token."""
    payload = get_payload_from_access_token(access_token)
    user_id = payload["user_id"]
    return user_id


def get_payload_from_access_token(access_token: str) -> dict:

    try:
        payload = jwt.decode(
            access_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ENCODE_ALGORITHM],
        )
        if payload["exp"] < datetime.now(timezone.utc).timestamp():
            raise TokenExpiredError("Token has expired")
        return payload
    except JWTError as e:
        raise TokenNotCorrectError("Invalid token") from e
