from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from echonotify.auth.constants import EXPIRES_AT_REFRESH_TOKEN
from echonotify.auth.cookies import CookieManager
from echonotify.auth.schema import (
    UserLoginRequestSchema,
    UserLoginResponseSchema,
)
from echonotify.auth.service import (
    AuthServicesBundle,
)
from echonotify.exception import (
    TokenExpiredError,
    TokenNotCorrectError,
    UserNotCorrectPasswordError,
    UserNotFoundError,
)
from echonotify.infrastructure.database.database import get_db_session
from echonotify.settings import Settings
from echonotify.users.dependencies import (
    get_auth_service,
)

router = APIRouter(prefix="/auth", tags=["auth"])

settings = Settings()


@router.post("/login", response_model=UserLoginResponseSchema)
async def login(
    body: UserLoginRequestSchema,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
    auth_bundle: AuthServicesBundle = Depends(get_auth_service),
):
    """
    Login user, return access token and set refresh_token cookie.
    """

    auth_service = auth_bundle.auth_service

    try:
        result = await auth_service.login(body.email, body.password, session)

        # set refresh token cookie
        CookieManager(response).set_refresh_token(
            result.refresh_token,
            EXPIRES_AT_REFRESH_TOKEN,
        )

        return UserLoginResponseSchema(
            user_id=result.user_id,
            access_token=result.access_token,
        )

    except UserNotCorrectPasswordError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e)
        ) from e
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e


@router.post("/refresh", response_model=dict)
async def refresh(
    response: Response,
    raw_refresh: str = Cookie(alias="refresh_token"),
    session: AsyncSession = Depends(get_db_session),
    auth_bundle: AuthServicesBundle = Depends(get_auth_service),
):
    """
    Refresh access token by refresh cookie.
    """

    auth_service = auth_bundle.auth_service

    try:
        tokens = await auth_service.refresh(
            raw_refresh,
            session,
        )

        CookieManager(response).set_refresh_token(
            tokens.refresh_token,
            EXPIRES_AT_REFRESH_TOKEN,
        )

        return {
            "access_token": tokens.access_token,
            "token_type": "bearer",
        }

    except (TokenNotCorrectError, TokenExpiredError) as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e)
        ) from e
