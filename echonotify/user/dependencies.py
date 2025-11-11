from fastapi import Depends
from fastapi.security import HTTPBearer

from echonotify.auth.service import (
    get_user_id_from_access_token,
)
from echonotify.config import logging

reusable_oauth2 = HTTPBearer()
logging = logging.getLogger(__name__)


def get_current_user_id(
    token: str = Depends(HTTPBearer()),
) -> int:
    return get_user_id_from_access_token(token.credentials)
