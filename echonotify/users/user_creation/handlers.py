from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from echonotify.auth.cookies import CookieManager
from echonotify.auth.schema import UserLoginResponseSchema
from echonotify.exception import UserAlreadyExistsError
from echonotify.infrastructure.database.database import get_db_session
from echonotify.users.user_creation.schema import UserCreateSchema
from echonotify.users.user_creation.service import CreateUser

router = APIRouter(prefix="/user", tags=["user"])


@router.post("", response_model=UserLoginResponseSchema)
async def create_user(
    user_data: UserCreateSchema,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
):
    try:
        cookies = CookieManager(response)
        creation_user = CreateUser(session=session)
        result = await creation_user.create_user_service(user_data)
        cookies.set_refresh_cookie(
            response=response,
            refresh_token=result.refresh_token,
            expires_in=3600,
        )
        return UserLoginResponseSchema(
            user_id=result.user_id, access_token=result.access_token
        )
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=e.detail
        ) from e
