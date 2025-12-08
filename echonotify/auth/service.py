from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import EmailStr

from echonotify.auth.constants import (
    EXPIRES_AT_ACCESS_TOKEN,
    EXPIRES_AT_REFRESH_TOKEN,
)
from echonotify.auth.interfaces import IRefreshTokenRepository, IUserRepository
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


class PasswordService:
    """Hash and verify users."""

    def __init__(self, schemes: Optional[list[str]] = None):
        schemes = schemes or ["argon2"]
        self._ctx = CryptContext(schemes=schemes, deprecated="auto")

    def hash(self, password: str) -> str:
        return self._ctx.hash(password)

    def verify(self, plain: str, hashed: str) -> bool:
        return self._ctx.verify(plain, hashed)


class JWTService:
    """Generate access-jwt"""

    def __init__(self, secret: str, algorithm: str, access_exp_minutes: int):
        self.secret = secret
        self.algorithm = algorithm
        self.access_exp_minutes = access_exp_minutes

    def generate_access(self, user_id: int, email: EmailStr) -> str:
        payload = {
            "user_id": user_id,
            "email": str(email),
            "exp": (
                datetime.now(timezone.utc)
                + timedelta(minutes=self.access_exp_minutes)
            ).timestamp(),
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)


class RefreshTokenService:
    def __init__(
        self,
        repo: IRefreshTokenRepository,
        password_service: PasswordService,
        refresh_expires_seconds: int,
    ):
        self.repo = repo
        self.password_service = password_service
        self.refresh_expires_seconds = refresh_expires_seconds

    async def issue(self, user_id: int) -> str:
        """Generate new refresh_token.
        Returns raw token str."""
        await self.repo.delete_all_for_user(user_id)
        raw = secrets.token_urlsafe(64)

        entry = RefreshToken(
            user_id=user_id,
            token=self.password_service.hash(raw),
            created_at=utc_now_naive(),
            expires_at=utc_now_naive()
            + timedelta(seconds=self.refresh_expires_seconds),
        )
        await self.repo.save(entry)
        return raw

    async def validate(self, raw_refresh: str) -> RefreshToken:
        tokens = await self.repo.find_all_valid()
        for record in tokens:
            if self.password_service.verify(raw_refresh, record.token):
                return record
        raise TokenNotCorrectError("Invalid refresh token")

    async def assert_not_expired(self, record: RefreshToken) -> None:
        if record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(
            timezone.utc
        ):
            await self.repo.delete_all_for_user(record.user_id)
            raise TokenExpiredError("Refresh token expired")

    async def revoke(self, record: RefreshToken) -> None:
        await self.repo.delete(record)


class UserService:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def get_by_email(self, email: EmailStr, session) -> UserProfile:
        user = await self.user_repo.get_by_email(email, session)
        if not user:
            raise UserNotFoundError("User not found")
        return user

    async def get_by_id(self, user_id: int, session) -> UserProfile:
        user = await self.user_repo.get_by_id(user_id, session)
        if not user:
            raise UserNotFoundError("User not found")
        return user


class AuthValidator:
    def __init__(self, password_service: PasswordService):
        self.password_service = password_service

    def validate_login(self, user: UserProfile, password: str) -> None:
        if user.is_google_account:
            raise UserNotCorrectPasswordError("Google auth required")
        if not self.password_service.verify(password, user.password):
            raise UserNotCorrectPasswordError("Wrong password")


class AuthService:
    def __init__(
        self,
        user_service: UserService,
        jwt_service: JWTService,
        refresh_service: RefreshTokenService,
        validator: AuthValidator,
    ):
        self.user_service = user_service
        self.jwt_service = jwt_service
        self.refresh_service = refresh_service
        self.validator = validator

    async def login(
        self, email: EmailStr, password: str, session
    ) -> UserLoginSchema:
        user = await self.user_service.get_by_email(email, session)
        self.validator.validate_login(user, password)

        access_token = self.jwt_service.generate_access(user.id, user.email)
        refresh_token = await self.refresh_service.issue(user.id)

        return UserLoginSchema(
            user_id=user.id,
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh(self, raw_refresh: str, session) -> UserLoginSchema:
        record = await self.refresh_service.validate(raw_refresh)
        await self.refresh_service.assert_not_expired(record)

        user = await self.user_service.get_by_id(record.user_id, session)
        access_token = self.jwt_service.generate_access(user.id, user.email)
        new_refresh = await self.refresh_service.issue(user.id)

        return UserLoginSchema(
            user_id=user.id,
            access_token=access_token,
            refresh_token=new_refresh,
        )

    async def logout(self, raw_refresh: str) -> None:
        record = await self.refresh_service.validate(raw_refresh)
        await self.refresh_service.revoke(record)


@dataclass
class AuthServicesBundle:
    password_service: PasswordService
    jwt_service: JWTService
    refresh_service: RefreshTokenService
    user_service: UserService
    validator: AuthValidator
    auth_service: AuthService

    def build_auth_services(
        self,
        user_repo: IUserRepository,
        refresh_repo: IRefreshTokenRepository,
        *,
        settings_obj: Settings = settings,
    ) -> AuthServicesBundle:
        pwd = PasswordService()
        jwt_svc = JWTService(
            secret=settings_obj.JWT_SECRET_KEY,
            algorithm=settings_obj.JWT_ENCODE_ALGORITHM,
            access_exp_minutes=EXPIRES_AT_ACCESS_TOKEN,
        )
        refresh_svc = RefreshTokenService(
            repo=refresh_repo,
            password_service=pwd,
            refresh_expires_seconds=EXPIRES_AT_REFRESH_TOKEN,
        )
        user_svc = UserService(user_repo)
        validator = AuthValidator(pwd)
        auth = AuthService(
            user_service=user_svc,
            jwt_service=jwt_svc,
            refresh_service=refresh_svc,
            validator=validator,
        )

        return AuthServicesBundle(
            password_service=pwd,
            jwt_service=jwt_svc,
            refresh_service=refresh_svc,
            user_service=user_svc,
            validator=validator,
            auth_service=auth,
        )

    def get_email_from_access_token(self, access_token: str) -> str:
        """Extract user ID from JWT access token."""
        payload = self.get_payload_from_access_token(access_token)
        email = payload["email"]
        return email

    def get_user_id_from_access_token(self, access_token: str) -> int:
        """Extract user ID from JWT access token."""
        payload = self.get_payload_from_access_token(access_token)
        user_id = payload["user_id"]
        return user_id

    def get_payload_from_access_token(self, access_token: str) -> dict:
        """Extract payload fron access token."""
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
