from typing import Any, Optional

from fastapi import WebSocket

from echonotify.chat.interfaces import (
    IConnectionManager,
    IConnectionStorage,
    ISendManager,
    IWebSocketService,
)
from echonotify.chat.models import ChatMessage, ChatRoom, UserRole
from echonotify.chat.repository import MessageRepository, RoomRepository
from echonotify.chat.schemas import (
    ChatHistoryResponse,
    ChatMessageResponse,
)


class ConnectionStorage:
    """Storage for WebSocket connections following SRP"""

    def __init__(self):
        self._connections: dict[str, WebSocket] = {}
        self._user_rooms: dict[int, int] = {}

    async def add_connection(
        self, client_id: str, websocket: WebSocket
    ) -> None:
        """Add WebSocket connection"""
        self._connections[client_id] = websocket

    async def remove_connection(self, client_id: str) -> None:
        """Remove WebSocket connection"""
        if client_id in self._connections:
            del self._connections[client_id]

    async def set_user_room(self, user_id: int, room_id: int) -> None:
        """Set room for user"""
        self._user_rooms[user_id] = room_id

    async def get_user_room(self, user_id: int) -> Optional[int]:
        """Get room for user"""
        return self._user_rooms.get(user_id)

    async def get_connection(self, client_id: str) -> Optional[WebSocket]:
        """Get WebSocket connection for client"""
        return self._connections.get(client_id)

    async def get_all_connections(self) -> dict[str, WebSocket]:
        """Get all WebSocket connections"""
        return self._connections.copy()


class ConnectionManager:
    """Manages WebSocket connections following SRP"""

    def __init__(self, storage: IConnectionStorage):
        self._storage = storage

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Connect client to WebSocket"""
        await websocket.accept()
        await self._storage.add_connection(client_id, websocket)

    async def disconnect(self, websocket: WebSocket, client_id: str) -> None:
        """Disconnect client from WebSocket"""
        await self._storage.remove_connection(client_id)

    async def set_user_room(self, user_id: int, room_id: int) -> None:
        """Set room for user"""
        await self._storage.set_user_room(user_id, room_id)


class SendManager:
    """Manages sending messages to WebSocket clients following SRP"""

    def __init__(self, storage: IConnectionStorage):
        self._storage = storage

    async def send_message(
        self, message: dict[str, Any], client_id: str
    ) -> None:
        """Send message to specific client"""
        connection = await self._storage.get_connection(client_id)
        if connection:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending message to {client_id}: {e}")

    async def broadcast_message(self, message: dict[str, Any]) -> None:
        """Broadcast message to all connected clients"""
        connections = await self._storage.get_all_connections()
        for client_id, websocket in connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to {client_id}: {e}")

    async def send_to_room(
        self, message: dict[str, Any], user_id: int
    ) -> None:
        """Send message to user and all clients in the same room"""
        room_id = await self._storage.get_user_room(user_id)
        if not room_id:
            return

        connections = await self._storage.get_all_connections()
        for client_id, ws in connections.items():
            try:
                room_id_for_client = await self._storage.get_user_room(
                    int(client_id.split("_")[1])
                )
                if room_id_for_client == room_id:
                    await ws.send_json(message)
            except Exception as e:
                print(f"Error sending to room: {e}")


class RoomService:
    """Business logic for chat rooms following SRP"""

    def __init__(self, room_repository: RoomRepository):
        self._repository = room_repository

    async def get_or_create_room(
        self, user_id: int, support_id: Optional[int] = None
    ) -> ChatRoom:
        """
        Business logic: Get existing active room or create new one
        One active room per user rule
        """
        existing_room = await self._repository.get_active_room_by_user_id(
            user_id
        )

        if existing_room:
            # If support is provided and room has no support, assign it
            if support_id and not existing_room.support_id:
                await self._repository.update_room_support(
                    existing_room.id, support_id
                )
                existing_room.support_id = support_id
            return existing_room

        # Create new room
        return await self._repository.create_room(user_id, support_id)

    async def get_room_by_id(self, room_id: int) -> Optional[ChatRoom]:
        """Get room by ID"""
        return await self._repository.get_room_by_id(room_id)

    async def assign_support_to_room(
        self, room_id: int, support_id: int
    ) -> Optional[ChatRoom]:
        """
        Business logic: Assign support to room
        Validates room exists before assignment
        """
        room = await self._repository.get_room_by_id(room_id)
        if not room:
            return None

        await self._repository.update_room_support(room_id, support_id)
        room.support_id = support_id
        return room

    async def close_room(self, room_id: int) -> bool:
        """
        Business logic: Close room
        Returns True if successful
        """
        room = await self._repository.get_room_by_id(room_id)
        if not room:
            return False

        await self._repository.deactivate_room(room_id)
        return True

    async def get_all_active_rooms(self) -> list[ChatRoom]:
        """Get all active rooms"""
        return await self._repository.get_all_active_rooms()

    async def get_support_rooms(self, support_id: int) -> list[ChatRoom]:
        """Get rooms assigned to support user"""
        return await self._repository.get_rooms_by_support_id(support_id)


class MessageService:
    """Business logic for messages following SRP"""

    def __init__(self, message_repository: MessageRepository):
        self._repository = message_repository

    async def save_message(
        self,
        room_id: int,
        sender_id: int,
        sender_role: str,
        message: str,
    ) -> ChatMessage:
        """
        Business logic: Save message
        Validates message content before saving
        """
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")

        return await self._repository.save_message(
            room_id=room_id,
            sender_id=sender_id,
            sender_role=sender_role,
            message=message.strip(),
        )

    async def get_room_messages(self, room_id: int) -> list[ChatMessage]:
        """Get all messages for a room"""
        return await self._repository.get_messages(room_id)

    async def get_chat_history(
        self, room_id: int, limit: int = 50
    ) -> ChatHistoryResponse:
        """
        Business logic: Get formatted chat history
        Returns history in chronological order
        """
        messages = await self._repository.get_messages(room_id)

        # Apply limit
        if limit and len(messages) > limit:
            messages = messages[-limit:]

        message_responses = [
            ChatMessageResponse.model_validate(msg) for msg in messages
        ]

        return ChatHistoryResponse(
            room_id=room_id,
            messages=message_responses,
            total=len(message_responses),
        )

    async def mark_as_read(self, message_id: int) -> bool:
        """
        Business logic: Mark message as read
        Returns True if successful
        """
        message = await self._repository.get_message_by_id(message_id)
        if not message:
            return False

        await self._repository.update_message_status(message_id, "read")
        return True


class WebSocketService:
    """Main WebSocket business logic following SRP"""

    def __init__(
        self,
        connection_manager: IConnectionManager,
        send_manager: ISendManager,
        room_service: RoomService,
        message_service: MessageService,
    ):
        self._connection_manager = connection_manager
        self._send_manager = send_manager
        self._room_service = room_service
        self._message_service = message_service

    async def handle_connection(
        self,
        websocket: WebSocket,
        client_id: str,
        user_id: int,
        is_support: bool,
        room_id: int | None,
    ) -> None:
        """
        Business logic: Handle new connection
        Creates/gets room for users, sends history
        """
        await self._connection_manager.connect(websocket, client_id)

        # Get or create room
        if room_id:
            room = await self._room_service.get_room_by_id(room_id)
            if not room:
                # Create new room
                room = await self._room_service.get_or_create_room(user_id)
        else:
            room = await self._room_service.get_or_create_room(user_id)

        # Store user's room
        await self._connection_manager.set_user_room(user_id, room.id)

        # Send chat history
        history = await self._message_service.get_chat_history(room.id)
        welcome_msg = {
            "type": "history",
            "room_id": room.id,
            "user_id": user_id,
            "messages": [
                msg.model_dump(mode="json") for msg in history.messages
            ],
        }
        await self._send_manager.send_message(welcome_msg, client_id)

        # Send user info to client
        auth_msg = {
            "type": "auth",
            "user_id": user_id,
        }
        await self._send_manager.send_message(auth_msg, client_id)

    async def handle_disconnection(
        self, websocket: WebSocket, client_id: str
    ) -> None:
        """Business logic: Handle disconnection"""
        await self._connection_manager.disconnect(websocket, client_id)

    async def handle_message(
        self,
        message_data: dict[str, Any],
        client_id: str,
        user_id: int,
        user_name: str,
        is_support: bool,
    ) -> None:
        """
        Business logic: Handle incoming message
        Routes to appropriate handler based on message type
        """
        msg_type = message_data.get("type", "message")

        if msg_type == "message":
            await self._handle_chat_message(
                message_data, client_id, user_id, user_name, is_support
            )
        elif msg_type == "typing":
            await self._handle_typing_indicator(
                message_data, client_id, user_id, user_name, is_support
            )

    async def _handle_chat_message(
        self,
        message_data: dict[str, Any],
        client_id: str,
        user_id: int,
        user_name: str,
        is_support: bool,
    ) -> None:
        """Handle chat message business logic"""
        message_text = message_data.get("message", "")
        if not message_text:
            return

        if is_support:
            await self._handle_support_message(
                message_data, user_id, user_name, message_text
            )
        else:
            await self._handle_user_message(
                client_id, user_id, user_name, message_text
            )

    async def _handle_support_message(
        self,
        message_data: dict[str, Any],
        support_id: int,
        support_name: str,
        message_text: str,
    ) -> None:
        """Business logic: Handle message from support"""
        room_id = message_data.get("room_id")
        if not room_id:
            return

        room = await self._room_service.get_room_by_id(room_id)
        if not room:
            return

        # Assign support to room if needed
        if not room.support_id:
            await self._room_service.assign_support_to_room(
                room_id, support_id
            )

        # Save message
        saved_msg = await self._message_service.save_message(
            room_id=room_id,
            sender_id=support_id,
            sender_role=UserRole.SUPPORT.value,
            message=message_text,
        )

        # Send to all connected clients
        response = {
            "type": "message",
            "room_id": room_id,
            "sender_id": support_id,
            "sender_name": support_name,
            "sender_role": UserRole.SUPPORT.value,
            "message": message_text,
            "timestamp": saved_msg.created_at.isoformat(),
            "message_id": saved_msg.id,
        }

        await self._send_manager.broadcast_message(response)

    async def _handle_user_message(
        self,
        client_id: str,
        user_id: int,
        user_name: str,
        message_text: str,
    ) -> None:
        """Business logic: Handle message from user"""
        # Get or create room
        room = await self._room_service.get_or_create_room(user_id)

        # Save message
        saved_msg = await self._message_service.save_message(
            room_id=room.id,
            sender_id=user_id,
            sender_role=UserRole.USER.value,
            message=message_text,
        )

        # Build response
        response = {
            "type": "message",
            "room_id": room.id,
            "sender_id": user_id,
            "sender_name": user_name,
            "sender_role": UserRole.USER.value,
            "message": message_text,
            "timestamp": saved_msg.created_at.isoformat(),
            "message_id": saved_msg.id,
        }

        # Send to room
        await self._send_manager.send_to_room(response, user_id)

    async def _handle_typing_indicator(
        self,
        message_data: dict[str, Any],
        client_id: str,
        user_id: int,
        user_name: str,
        is_support: bool,
    ) -> None:
        """Business logic: Handle typing indicator"""
        if is_support:
            return  # Support doesn't send typing indicators

        # Get user's room
        room = await self._room_service.get_or_create_room(user_id)
        if not room.support_id:
            return

        # Send typing indicator to support
        typing_msg = {
            "type": "typing",
            "room_id": room.id,
            "sender_id": user_id,
            "sender_name": user_name,
        }

        support_client_id = f"support_{room.support_id}"
        await self._send_manager.send_message(typing_msg, support_client_id)


class ChatServiceFacade:
    """Facade for all chat services following Facade pattern"""

    def __init__(
        self,
        websocket_service: IWebSocketService,
        room_service: RoomService,
        message_service: MessageService,
    ):
        self._websocket_service = websocket_service
        self._room_service = room_service
        self._message_service = message_service

    # WebSocket operations
    async def handle_connection(
        self,
        websocket: WebSocket,
        client_id: str,
        user_id: int,
        is_support: bool,
        room_id: int | None = None,
    ) -> None:
        """Handle WebSocket connection"""
        return await self._websocket_service.handle_connection(
            websocket, client_id, user_id, is_support, room_id
        )

    async def handle_disconnection(
        self, websocket: WebSocket, client_id: str
    ) -> None:
        """Handle WebSocket disconnection"""
        return await self._websocket_service.handle_disconnection(
            websocket, client_id
        )

    async def handle_message(
        self,
        message_data: dict[str, Any],
        client_id: str,
        user_id: int,
        user_name: str,
        is_support: bool,
    ) -> None:
        """Handle WebSocket message"""
        return await self._websocket_service.handle_message(
            message_data, client_id, user_id, user_name, is_support
        )

    # Room operations
    async def get_or_create_room(
        self, user_id: int, support_id: Optional[int] = None
    ) -> ChatRoom:
        """Get or create room"""
        return await self._room_service.get_or_create_room(user_id, support_id)

    async def get_room_by_id(self, room_id: int) -> Optional[ChatRoom]:
        """Get room by ID"""
        return await self._room_service.get_room_by_id(room_id)

    async def close_room(self, room_id: int) -> bool:
        """Close room"""
        return await self._room_service.close_room(room_id)

    async def get_all_active_rooms(self) -> list[ChatRoom]:
        """Get all active rooms"""
        return await self._room_service.get_all_active_rooms()

    # Message operations
    async def get_chat_history(
        self, room_id: int, limit: int = 50
    ) -> ChatHistoryResponse:
        """Get chat history"""
        return await self._message_service.get_chat_history(room_id, limit)

    async def mark_message_as_read(self, message_id: int) -> bool:
        """Mark message as read"""
        return await self._message_service.mark_as_read(message_id)
