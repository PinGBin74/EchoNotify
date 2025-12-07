from abc import ABC, abstractmethod
from typing import List

from echonotify.users.user_profile.models import RefreshToken


class IRefreshTokenRepository(ABC):
    @abstractmethod
    async def find_valid_tokens(self, user_id: int) -> List[RefreshToken]:
        pass

    @abstractmethod
    async def find_all_valid(self) -> List[RefreshToken]:
        pass

    @abstractmethod
    async def save(self, token: RefreshToken) -> None:
        pass

    @abstractmethod
    async def delete(self, token: RefreshToken) -> None:
        pass

    @abstractmethod
    async def delete_all_for_user(self, user_id: int) -> None:
        pass
