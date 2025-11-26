from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from echonotify.user.user_creation.schema import UserCreateSchema
from echonotify.user.user_profile.models import UserProfile


@dataclass
class UserRepository:
    session: AsyncSession

    async def create_user(self, user_data: UserCreateSchema) -> UserProfile:
        user = UserProfile(
            name=user_data.name,
            email=user_data.email,
            password=user_data.password,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_user_by_email(self, email: str) -> UserProfile | None:
        stmt = select(UserProfile).where(UserProfile.email == email)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> UserProfile | None:
        stmt = select(UserProfile).where(UserProfile.id == user_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()
