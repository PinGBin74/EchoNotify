from fastapi import Depends
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from echonotify.auth.service import (
    AuthService,
    AuthServicesBundle,
    AuthValidator,
    JWTService,
    PasswordService,
    RefreshTokenService,
    UserService,
)
from echonotify.config import logging
from echonotify.settings import Settings

from ..auth.constants import EXPIRES_AT_ACCESS_TOKEN, EXPIRES_AT_REFRESH_TOKEN
from ..auth.repository import RefreshTokenRepositorySQLAlchemy
from ..decorators import handle_token_errors
from ..infrastructure.database.database import get_db_session
from .user_creation.repository import UserRepository

reusable_oauth2 = HTTPBearer()
logging = logging.getLogger(__name__)
settings = Settings()


@handle_token_errors
async def get_auth_service(
    session: AsyncSession = Depends(get_db_session),
) -> AuthServicesBundle:
    user_repo = UserRepository(session)
    refresh_repo = RefreshTokenRepositorySQLAlchemy(session)

    password_service = PasswordService()
    jwt_service = JWTService(
        access_exp_minutes=EXPIRES_AT_ACCESS_TOKEN,
    )
    refresh_service = RefreshTokenService(
        repo=refresh_repo,
        password_service=password_service,
        refresh_expires_seconds=EXPIRES_AT_REFRESH_TOKEN,
    )
    user_service = UserService(user_repo)
    validator = AuthValidator(password_service)

    auth_service = AuthService(
        user_service=user_service,
        jwt_service=jwt_service,
        refresh_service=refresh_service,
        validator=validator,
    )

    return AuthServicesBundle(
        password_service=password_service,
        jwt_service=jwt_service,
        refresh_service=refresh_service,
        user_service=user_service,
        validator=validator,
        auth_service=auth_service,
    )


@handle_token_errors
def get_current_user_id(
    token: str = Depends(HTTPBearer()),
    auth: AuthServicesBundle = Depends(get_auth_service),
) -> int:
    return auth.get_user_id_from_access_token(token.credentials)


@handle_token_errors
async def get_current_email_id(
    token: str = Depends(HTTPBearer()),
    auth: AuthServicesBundle = Depends(get_auth_service),
) -> str:
    return auth.get_email_from_access_token(token.credentials)
