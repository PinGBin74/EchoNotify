from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from echonotify.users.user_profile.models import UserProfile


class UserRepository:
    """Repository class for handling user-related database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user_with_defaults(
        self,
        email: str,
        name: str,
        password: str,
    ) -> UserProfile:
        """Create a new user with default settings."""

        user = UserProfile(
            name=name,
            email=email,
            password=password,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.commit()
        return user

    async def get_user_by_id(self, user_id: int) -> Optional[UserProfile]:
        """Retrieve a user by their ID."""

        user_query = select(UserProfile).where(UserProfile.id == user_id)
        result = await self.session.execute(user_query)
        return result.scalar_one_or_none()

    async def user_exists(self, email: str) -> bool:
        """Check if a user with the given email exists."""
        user = await self.get_user_data_by_email(
            email, self.session, UserProfile
        )
        return user is not None

    async def get_user_data_by_email(self, email: str):
        user_query = select(UserProfile).where(UserProfile.email == email)
        result = await self.session.execute(user_query)
        return result.scalar_one_or_none()
