from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from echonotify.auth.cookies import CookieManager
from echonotify.auth.schema import (
    UserLoginRequestSchema,
    UserLoginResponseSchema,
)
from echonotify.auth.service import (  # Added import for AuthServicesBundle
    AuthServicesBundle,
)
from echonotify.config import logging
from echonotify.exception import (
    TokenExpiredError,
    TokenNotCorrectError,
    UserNotCorrectPasswordError,
)
from echonotify.infrastructure.database.database import get_db_session
from echonotify.settings import Settings
from echonotify.users.dependencies import (
    get_auth_service,
    get_current_user_id,
)

router = APIRouter(prefix="/auth", tags=["auth"])

settings = Settings()
logger = logging.getLogger(__name__)


# ------------------------------
# LOGIN
# ------------------------------
@router.post("/login", response_model=UserLoginResponseSchema)
async def login(
    body: UserLoginRequestSchema,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
    auth_bundle: AuthServicesBundle = Depends(
        get_auth_service
    ),  # Fixed: Added type hint AuthServicesBundle
):
    """
    Login user, return access token and set refresh_token cookie.
    """

    auth_service = auth_bundle.auth_service  # <--- главное отличие

    try:
        # login(email, password, session)
        result = await auth_service.login(body.email, body.password, session)

        # set refresh token cookie
        CookieManager(response).set_refresh_token(
            result.refresh_token,
            settings.REFRESH_TOKEN_EXPIRE_SECONDS,
        )

        return UserLoginResponseSchema(
            user_id=result.user_id,
            access_token=result.access_token,
        )

    except UserNotCorrectPasswordError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


# ------------------------------
# REFRESH ACCESS TOKEN
# ------------------------------
@router.post("/refresh", response_model=dict)
async def refresh(
    response: Response,
    raw_refresh: str = Cookie(alias="refresh_token"),
    session: AsyncSession = Depends(get_db_session),
    auth_bundle: AuthServicesBundle = Depends(
        get_auth_service
    ),  # Fixed: Added type hint AuthServicesBundle
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
            settings.REFRESH_TOKEN_EXPIRE_SECONDS,
        )

        return {
            "access_token": tokens.access_token,
            "token_type": "bearer",
        }

    except (TokenNotCorrectError, TokenExpiredError) as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


# ------------------------------
# LOGOUT
# ------------------------------
@router.post("/logout")
async def logout(
    response: Response,
    raw_refresh: str = Cookie(alias="refresh_token"),
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
    auth_bundle: AuthServicesBundle = Depends(
        get_auth_service
    ),  # Fixed: Added type hint AuthServicesBundle
):
    """
    Logout user – invalidate refresh token and remove cookie.
    """

    auth_service = auth_bundle.auth_service

    await auth_service.logout(raw_refresh)

    CookieManager(response).delete_refresh_token()

    return {"message": "Successfully logged out"}
