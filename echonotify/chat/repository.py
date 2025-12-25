from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from echonotify.chat.models import ChatMessage, ChatRoom


class MessageRepository:
    """Repository for ChatMessage - only database operations"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_messages(self, room_id: int) -> list[ChatMessage]:
        """Get all messages for a room from database"""
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.room_id == room_id)
            .order_by(ChatMessage.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def save_message(
        self,
        room_id: int,
        sender_id: int,
        sender_role: str,
        message: str,
    ) -> ChatMessage:
        """Save a message to database"""
        chat_message = ChatMessage(
            room_id=room_id,
            sender_id=sender_id,
            sender_role=sender_role,
            message=message,
        )
        self._session.add(chat_message)
        await self._session.commit()
        await self._session.refresh(chat_message)
        return chat_message

    async def update_message_status(
        self, message_id: int, status: str
    ) -> None:
        """Update message status in database"""
        stmt = (
            update(ChatMessage)
            .where(ChatMessage.id == message_id)
            .values(status=status)
        )
        await self._session.execute(stmt)
        await self._session.commit()

    async def get_message_by_id(
        self, message_id: int
    ) -> Optional[ChatMessage]:
        """Get message by ID from database"""
        stmt = select(ChatMessage).where(ChatMessage.id == message_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class RoomRepository:
    """Repository for ChatRoom - only database operations"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_room(
        self, user_id: int, support_id: Optional[int] = None
    ) -> ChatRoom:
        """Create new chat room in database"""
        room = ChatRoom(user_id=user_id, support_id=support_id)
        self._session.add(room)
        await self._session.commit()
        await self._session.refresh(room)
        return room

    async def get_or_create_public_room(
        self, room_id: int, user_id: int
    ) -> ChatRoom:
        """Get public room by ID or create one"""
        room = await self.get_room_by_id(room_id)
        if room:
            return room

        room = ChatRoom(user_id=user_id, is_public=True)
        self._session.add(room)
        await self._session.commit()
        await self._session.refresh(room)
        return room

    async def get_room_by_id(self, room_id: int) -> Optional[ChatRoom]:
        """Get room by ID from database"""
        stmt = select(ChatRoom).where(ChatRoom.id == room_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_room_by_user_id(
        self, user_id: int
    ) -> Optional[ChatRoom]:
        """Get active room for user from database"""
        stmt = select(ChatRoom).where(
            ChatRoom.user_id == user_id, ChatRoom.is_active == True
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_active_rooms(self) -> list[ChatRoom]:
        """Get all active rooms from database"""
        stmt = select(ChatRoom).where(ChatRoom.is_active == True)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_room_support(self, room_id: int, support_id: int) -> None:
        """Update support assignment in database"""
        stmt = (
            update(ChatRoom)
            .where(ChatRoom.id == room_id)
            .values(support_id=support_id)
        )
        await self._session.execute(stmt)
        await self._session.commit()

    async def deactivate_room(self, room_id: int) -> None:
        """Deactivate room in database"""
        stmt = (
            update(ChatRoom)
            .where(ChatRoom.id == room_id)
            .values(is_active=False)
        )
        await self._session.execute(stmt)
        await self._session.commit()

    async def get_rooms_by_support_id(self, support_id: int) -> list[ChatRoom]:
        """Get all rooms assigned to support from database"""
        stmt = select(ChatRoom).where(
            ChatRoom.support_id == support_id, ChatRoom.is_active == True
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
