# repository.py
from typing import List

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from echonotify.auth.interfaces import IRefreshTokenRepository
from echonotify.auth.utils import utc_now_naive
from echonotify.users.user_profile.models import RefreshToken


class RefreshTokenRepositorySQLAlchemy(IRefreshTokenRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_valid_tokens(self, user_id: int) -> List[RefreshToken]:
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.expires_at > utc_now_naive(),
        )
        return (await self.session.execute(stmt)).scalars().all()

    async def find_all_valid(self) -> List[RefreshToken]:
        stmt = select(RefreshToken).where(
            RefreshToken.expires_at > utc_now_naive()
        )
        return (await self.session.execute(stmt)).scalars().all()

    async def save(self, token: RefreshToken) -> None:
        self.session.add(token)
        await self.session.commit()

    async def delete_all_for_user(self, user_id: int) -> None:
        await self.session.execute(
            delete(RefreshToken).where(RefreshToken.user_id == user_id)
        )
        await self.session.commit()

    async def delete(self, token: RefreshToken) -> None:
        await self.session.delete(token)
        await self.session.commit()
