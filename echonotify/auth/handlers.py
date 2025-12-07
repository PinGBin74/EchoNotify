from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from echonotify.auth.cookies import CookieManager
from echonotify.auth.schema import (
    UserLoginRequestSchema,
    UserLoginResponseSchema,
)
from echonotify.auth.service import AuthService
from echonotify.config import logging
from echonotify.exception import UserNotCorrectPasswordError
from echonotify.infrastructure.database.database import get_db_session
from echonotify.settings import Settings
from echonotify.users.dependencies import get_current_user_id

router = APIRouter(prefix="/auth", tags=["auth"])

settings = Settings()
logger = logging.getLogger(__name__)
auth_service = AuthService()


@router.post("/login", response_model=UserLoginResponseSchema)
async def login(
    body: UserLoginRequestSchema,
    response: Response,
    session: AsyncSession = Depends(get_db_session),  # noqa
):
    try:
        result = await auth_service.login_service(
            body.email, body.password, session
        )
        cookie_manager = CookieManager(response)
        cookie_manager.set_refresh_token(
            result.refresh_token, settings.REFRESH_TOKEN_EXPIRE_SECONDS
        )
        return UserLoginResponseSchema(
            user_id=result.user_id, access_token=result.access_token
        )
    except UserNotCorrectPasswordError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.post("/refresh", response_model=dict)
async def refresh(
    response: Response,
    raw_refresh: str = Cookie(alias="refresh_token"),
    session: AsyncSession = Depends(get_db_session),
):
    tokens = await auth_service.refresh_access_token_by_raw(
        raw_refresh, session
    )
    cookie_manager = CookieManager(response)
    cookie_manager.set_refresh_token(
        tokens.refresh_token, settings.REFRESH_TOKEN_EXPIRE_SECONDS
    )
    return {"access_token": tokens.access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(
    response: Response,
    raw_refresh: str = Cookie(alias="refresh_token"),
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
):
    await auth_service.logout_service_by_raw(raw_refresh, session)
    cookie_manager = CookieManager(response)
    cookie_manager.delete_refresh_token()
    return {"message": "Successfully logged out"}
