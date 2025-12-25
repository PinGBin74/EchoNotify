from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from echonotify.chat.interfaces import (
    IConnectionManager,
    ISendManager,
    IWebSocketService,
)
from echonotify.chat.repository import MessageRepository, RoomRepository
from echonotify.chat.service import (
    ChatServiceFacade,
    ConnectionManager,
    ConnectionStorage,
    MessageService,
    RoomService,
    SendManager,
    WebSocketService,
)
from echonotify.infrastructure.database.database import get_db_session

# Singleton instances for WebSocket connections
_connection_storage = ConnectionStorage()
_connection_manager: IConnectionManager = ConnectionManager(
    _connection_storage
)
_send_manager: ISendManager = SendManager(_connection_storage)


def get_connection_manager() -> IConnectionManager:
    """Get singleton connection manager instance"""
    return _connection_manager


def get_send_manager() -> ISendManager:
    """Get singleton send manager instance"""
    return _send_manager


async def get_message_repository(
    session: AsyncSession = Depends(get_db_session),
) -> MessageRepository:
    """Factory for message repository following DIP"""
    return MessageRepository(session)


async def get_room_repository(
    session: AsyncSession = Depends(get_db_session),
) -> RoomRepository:
    """Factory for room repository following DIP"""
    return RoomRepository(session)


async def get_room_service(
    room_repository: RoomRepository = Depends(get_room_repository),
) -> RoomService:
    """Factory for room service with dependency injection"""
    return RoomService(room_repository)


async def get_message_service(
    message_repository: MessageRepository = Depends(get_message_repository),
) -> MessageService:
    """Factory for message service with dependency injection"""
    return MessageService(message_repository)


async def get_websocket_service(
    connection_manager: IConnectionManager = Depends(get_connection_manager),
    send_manager: ISendManager = Depends(get_send_manager),
    room_service: RoomService = Depends(get_room_service),
    message_service: MessageService = Depends(get_message_service),
) -> IWebSocketService:
    """Factory for websocket service with all dependencies injected"""
    return WebSocketService(
        connection_manager=connection_manager,
        send_manager=send_manager,
        room_service=room_service,
        message_service=message_service,
    )


async def get_chat_service_facade(
    websocket_service: IWebSocketService = Depends(get_websocket_service),
    room_service: RoomService = Depends(get_room_service),
    message_service: MessageService = Depends(get_message_service),
) -> ChatServiceFacade:
    """
    Factory for chat service facade
    Following Facade pattern and DIP
    """
    return ChatServiceFacade(
        websocket_service=websocket_service,
        room_service=room_service,
        message_service=message_service,
    )
