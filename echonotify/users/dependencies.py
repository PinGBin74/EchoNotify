from fastapi import Depends
from fastapi.security import HTTPBearer

from echonotify.auth.service import (
    get_email_from_access_token,
    get_user_id_from_access_token,
)
from echonotify.config import logging

from ..decorators import handle_token_errors

reusable_oauth2 = HTTPBearer()
logging = logging.getLogger(__name__)


@handle_token_errors
def get_current_user_id(
    token: str = Depends(HTTPBearer()),
) -> int:
    return get_user_id_from_access_token(token.credentials)


@handle_token_errors
async def get_current_email_id(
    token: str = Depends(HTTPBearer()),
) -> str:
    return get_email_from_access_token(token.credentials)
