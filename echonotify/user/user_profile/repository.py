from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from echonotify.user.user_creation.schema import UserCreateSchema
from echonotify.user.user_profile.models import UserProfile


@dataclass
class UserRepository:
    db_session: AsyncSession

    async def create_user(
        self, session: AsyncSession, user_data: UserCreateSchema
    ) -> UserProfile:
        user = UserProfile(
            name=user_data.name,
            email=user_data.email,
            password=user_data.password,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def get_user_by_email(
        self, session: AsyncSession, email: str
    ) -> UserProfile:
        user_query = select(UserProfile).where(UserProfile.email == email)
        result = await session.execute(user_query)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, session: AsyncSession, user_id: int):
        user_query = select(UserProfile).where(UserProfile.id == user_id)
        result = await session.execute(user_query)
        user = result.scalar_one_or_none()
        return user
