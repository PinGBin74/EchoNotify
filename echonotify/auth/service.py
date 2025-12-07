import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt
from passlib.context import CryptContext
from pydantic import EmailStr

from echonotify.auth.constants import (
    EXPIRES_AT_ACCESS_TOKEN,
    EXPIRES_AT_REFRESH_TOKEN,
)
from echonotify.auth.repository import IRefreshTokenRepository
from echonotify.auth.schema import UserLoginSchema
from echonotify.auth.utils import utc_now_naive
from echonotify.exception import (
    TokenExpiredError,
    TokenNotCorrectError,
    UserNotCorrectPasswordError,
    UserNotFoundError,
)
from echonotify.settings import Settings
from echonotify.users.user_profile.models import RefreshToken, UserProfile

settings = Settings()
_pwd = CryptContext(schemes=["argon2"], deprecated="auto")


class AuthService:
    def __init__(self, repo: IRefreshTokenRepository):
        self.repo = repo

    # 🔹 Utility: hashing
    def verify_password(self, plain: str, hashed: str) -> bool:
        return _pwd.verify(plain, hashed)

    def hash_password(self, password: str) -> str:
        return _pwd.hash(password)

    # 🔹 Generate access JWT
    def _generate_access(self, user: UserProfile) -> str:
        payload = {
            "user_id": user.id,
            "email": user.email,
            "exp": (
                datetime.now(timezone.utc)
                + timedelta(minutes=EXPIRES_AT_ACCESS_TOKEN)
            ).timestamp(),
        }
        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ENCODE_ALGORITHM,
        )

    async def _validate_refresh(self, refresh_token: str) -> RefreshToken:
        tokens = await self.repo.find_all_valid()

        for record in tokens:
            if _pwd.verify(refresh_token, record.token):
                return record

        raise TokenNotCorrectError("Invalid refresh token")

    async def login(
        self, email: EmailStr, password: str, session
    ) -> UserLoginSchema:
        user: Optional[UserProfile] = await self.get_user_data_by_email(
            email, session, UserProfile
        )

        if not user:
            raise UserNotFoundError("User not found")
        if user.is_google_account:
            raise UserNotCorrectPasswordError("Google auth required")
        if not self._verify_password(password, user.password):
            raise UserNotCorrectPasswordError("Wrong password")

        access_token = self._generate_access(user)
        refresh_token = await self._issue_refresh(user.id)

        return UserLoginSchema(
            user_id=user.id,
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def _issue_refresh(self, user_id: int) -> str:
        await self.repo.delete_all_for_user(user_id)
        token_str = secrets.token_urlsafe(64)

        entry = RefreshToken(
            user_id=user_id,
            token=self._hash_password(token_str),
            created_at=utc_now_naive(),
            expires_at=utc_now_naive()
            + timedelta(seconds=EXPIRES_AT_REFRESH_TOKEN),
        )
        await self.repo.save(entry)
        return token_str

    async def refresh(self, refresh_token: str, session) -> UserLoginSchema:
        record = await self._validate_refresh(refresh_token)

        if record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(
            timezone.utc
        ):
            await self.repo.delete_all_for_user(record.user_id)
            raise TokenExpiredError("Refresh token expired")

        user = await self.get_user_by_id(record.user_id, session)
        access_token = self._generate_access(user)
        new_refresh = await self._issue_refresh(record.user_id)

        return UserLoginSchema(
            user_id=user.id,
            access_token=access_token,
            refresh_token=new_refresh,
        )

    async def logout(self, refresh_token: str) -> None:
        record = await self._validate_refresh(refresh_token)
        await self.repo.delete(record)

    @staticmethod
    def generate_access_token(user_id: int, email: EmailStr) -> str:
        """Generate JWT access token."""
        payload = {
            "user_id": user_id,
            "email": str(email),
            "exp": (
                datetime.now(timezone.utc)
                + timedelta(minutes=EXPIRES_AT_ACCESS_TOKEN)
            ).timestamp(),
        }
        encoded_jwt = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ENCODE_ALGORITHM,
        )
        return encoded_jwt

    async def login_service(
        self,
        email: EmailStr,
        password: str,
    ) -> UserLoginSchema:
        """Authenticate user and generate access and refresh tokens."""
        try:
            user = await self.get_user_data_by_email(email, UserProfile)
            if user.is_google_account:
                raise UserNotCorrectPasswordError(
                    "Google users must use OAuth login"
                )
            self._validate_auth_user(user, password)

            access_token = self.generate_access_token(user.id, user.email)
            refresh_token = await self.generate_or_update_refresh_token(
                user.id,
            )

            return UserLoginSchema(
                user_id=user.id,
                access_token=access_token,
                refresh_token=refresh_token,
            )
        except UserNotFoundError as e:
            raise UserNotCorrectPasswordError("User not found") from e

    async def refresh_access_token_by_raw(
        self,
        raw_refresh: str,
    ) -> UserLoginSchema:
        if not raw_refresh:
            raise TokenNotCorrectError("Refresh token is required")
        return await self.refresh_access_token(
            raw_refresh,
        )

    async def logout_service_by_raw(
        self,
        raw_refresh: str,
    ) -> None:
        if not raw_refresh:
            raise TokenNotCorrectError("Refresh token is required")
        await self.logout_service(
            raw_refresh,
        )

    async def refresh_access_token(
        self,
        refresh_token: str,
    ) -> UserLoginSchema:
        try:
            if not refresh_token:
                raise TokenNotCorrectError("Refresh token is required")

            token_record = await self.get_refresh_token(
                refresh_token,
            )

            if token_record.expires_at.replace(
                tzinfo=timezone.utc
            ) < datetime.now(timezone.utc):
                await self.delete_refresh_token(
                    token_record.user_id,
                )
                raise TokenExpiredError("Refresh token has expired")

            user = await self.get_user_by_id(token_record.user_id)
            access_token = self.generate_access_token(
                token_record.user_id, user.email
            )

            new_refresh_token = await self.generate_or_update_refresh_token(
                token_record.user_id
            )

            return UserLoginSchema(
                user_id=token_record.user_id,
                access_token=access_token,
                refresh_token=new_refresh_token,
            )

        except TokenExpiredError as e:
            raise TokenExpiredError() from e
        except TokenNotCorrectError as e:
            raise HTTPException(status_code=401, detail=str(e))  # noqa
