from typing import Any, Protocol

from fastapi import WebSocket

from echonotify.chat.models import ChatRoom
from echonotify.chat.schemas import ChatHistoryResponse


class IConnectionManager(Protocol):
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Connects a client to chat server."""
        ...

    async def disconnect(self, websocket: WebSocket, client_id: str) -> None:
        """Disconnects a client from chat server."""
        ...

    async def set_user_room(self, user_id: int, room_id: int) -> None:
        """Sets room for user."""
        ...

    async def remove_user_room(self, user_id: int) -> None:
        """Removes room for user."""
        ...


class ISendManager(Protocol):
    async def send_message(
        self, message: dict[str, Any], client_id: str
    ) -> None:
        """Sends a message to a client."""
        ...

    async def broadcast_message(self, message: dict[str, Any]) -> None:
        """Broadcasts message to all clients."""
        ...

    async def send_to_room(
        self, message: dict[str, Any], user_id: int
    ) -> None:
        """Sends message to user and assigned support in room."""
        ...


class IMessageRepository(Protocol):
    async def get_messages(self, room_id: int) -> list[Any]:
        """Gets a list of messages for a room."""
        ...

    async def save_message(
        self, room_id: int, sender_id: int, sender_role: str, message: str
    ) -> Any:
        """Saves a message for a room."""
        ...

    async def update_message_status(
        self, message_id: int, status: str
    ) -> None:
        """Updates the status of a message."""
        ...

    async def get_message_by_id(self, message_id: int) -> Any | None:
        """Gets a message by ID."""
        ...


class IChatServiceFacade(Protocol):
    async def handle_connection(
        self,
        websocket: WebSocket,
        client_id: str,
        user_id: int,
        is_support: bool,
        room_id: int | None,
    ) -> None:
        """Handle WebSocket connection"""
        ...

    async def handle_disconnection(
        self, websocket: WebSocket, client_id: str
    ) -> None:
        """Handle WebSocket disconnection"""
        ...

    async def handle_message(
        self,
        message: dict[str, Any],
        client_id: str,
        user_id: int,
        user_name: str,
        is_support: bool,
    ) -> None:
        """Handle WebSocket message"""
        ...

    async def get_or_create_room(
        self, user_id: int, support_id: int | None
    ) -> ChatRoom:
        """Get or create room"""
        ...

    async def get_room_by_id(self, room_id: int) -> ChatRoom | None:
        """Get room by ID"""
        ...

    async def close_room(self, room_id: int) -> bool:
        """Close room"""
        ...

    async def get_all_active_rooms(self) -> list[ChatRoom]:
        """Get all active rooms"""
        ...

    async def get_chat_history(
        self, room_id: int, limit: int
    ) -> ChatHistoryResponse:
        """Get chat history"""
        ...

    async def mark_message_as_read(self, message_id: int) -> bool:
        """Mark message as read"""
        ...


class IWebSocketService(Protocol):
    async def handle_connection(
        self,
        websocket: WebSocket,
        client_id: str,
        user_id: int,
        is_support: bool,
        room_id: int | None,
    ) -> None:
        """Handle WebSocket connection"""
        ...

    async def handle_disconnection(
        self, websocket: WebSocket, client_id: str
    ) -> None:
        """Handle WebSocket disconnection"""
        ...

    async def handle_message(
        self,
        message: dict[str, Any],
        client_id: str,
        user_id: int,
        user_name: str,
        is_support: bool,
    ) -> None:
        """Handle WebSocket message"""
        ...


class IConnectionStorage(Protocol):
    async def add_connection(
        self, client_id: str, websocket: WebSocket
    ) -> None:
        """Adds a WebSocket connection for a client."""
        ...

    async def remove_connection(self, client_id: str) -> None:
        """Removes a WebSocket connection for a client."""
        ...

    async def set_user_room(self, user_id: int, room_id: int) -> None:
        """Sets room for user."""
        ...

    async def get_user_room(self, user_id: int) -> int | None:
        """Gets room for user."""
        ...

    async def get_connection(self, client_id: str) -> WebSocket | None:
        """Gets a WebSocket connection for a client."""
        ...

    async def get_all_connections(self) -> dict[str, WebSocket]:
        """Gets all WebSocket connections."""
        ...
