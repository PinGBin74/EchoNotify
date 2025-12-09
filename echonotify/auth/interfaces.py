from typing import Optional, Protocol

from pydantic import EmailStr

from echonotify.users.user_profile.models import RefreshToken, UserProfile


class IRefreshTokenRepository(Protocol):
    """
    Interface for work with refresh_tokens
    """

    async def find_all_valid(self) -> list[RefreshToken]:
        """
        Return list of all working refresh_tokens.
        """
        ...

    async def save(self, token: RefreshToken) -> None:
        """
        Save new refresh_token.
        """
        ...

    async def delete(self, token: RefreshToken) -> None:
        """
        Delete certain refresh_token.
        """
        ...

    async def delete_all_for_user(self, user_id: int) -> None:
        """
        Delete all refresh_tokens.
        """
        ...


class IUserRepository(Protocol):
    """
    Interface for work with users
    Using Orm.
    """

    async def get_user_data_by_email(
        self, email: EmailStr
    ) -> Optional[UserProfile]:
        """
        Return users by email or None.
        """
        ...

    async def get_user_by_id(self, user_id: int) -> Optional[UserProfile]:
        """
        Search users by id.
        """
        ...
