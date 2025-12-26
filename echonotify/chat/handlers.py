import json
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)

from echonotify.chat.dependencies import (
    get_chat_service_facade,
    get_connection_manager,
)
from echonotify.chat.interfaces import IConnectionManager
from echonotify.chat.schemas import ChatHistoryResponse, ChatRoomResponse
from echonotify.chat.service import ChatServiceFacade
from echonotify.infrastructure.database.database import get_db_session
from echonotify.users.dependencies import get_auth_service, get_current_user_id
from echonotify.users.user_creation.repository import UserRepository

router = APIRouter(prefix="/chat", tags=["chat"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    is_support: bool = Query(False),
    room_id: int | None = Query(None),
    connection_manager: IConnectionManager = Depends(get_connection_manager),
    chat_service: ChatServiceFacade = Depends(get_chat_service_facade),
):
    # Authenticate user
    try:
        auth_service = await get_auth_service()
        user_id = auth_service.get_user_id_from_access_token(token)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_name = None

    # Get user info
    async for session in get_db_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_id(user_id)

        if not user:
            await session.close()
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        user_name = user.name
        await session.close()
        break

    if user_name is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Generate client ID
    prefix = "support" if is_support else "user"
    client_id = f"{prefix}_{user_id}"

    # Handle connection
    try:
        await chat_service.handle_connection(
            websocket, client_id, user_id, is_support, room_id
        )

        # Send user_id to client
        await websocket.send_json(
            {"type": "auth", "user_id": user_id, "user_name": user_name}
        )

        # Message loop
        while True:
            data = await websocket.receive_text()

            try:
                message_data: dict[str, Any] = json.loads(data)
            except json.JSONDecodeError:
                message_data = {"type": "message", "message": data}

            await chat_service.handle_message(
                message_data, client_id, user_id, user_name, is_support
            )

    except WebSocketDisconnect:
        await chat_service.handle_disconnection(websocket, client_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await chat_service.handle_disconnection(websocket, client_id)


@router.get("/rooms", response_model=list[ChatRoomResponse])
async def get_active_rooms(
    user_id: int = Depends(get_current_user_id),
    chat_service: ChatServiceFacade = Depends(get_chat_service_facade),
):
    """Get all active chat rooms (for support dashboard)"""
    rooms = await chat_service.get_all_active_rooms()
    return [ChatRoomResponse.model_validate(room) for room in rooms]


@router.get("/rooms/{room_id}/history", response_model=ChatHistoryResponse)
async def get_room_history(
    room_id: int,
    limit: int = Query(50, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    chat_service: ChatServiceFacade = Depends(get_chat_service_facade),
):
    """Get chat history for a specific room"""
    room = await chat_service.get_room_by_id(room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )

    return await chat_service.get_chat_history(room_id, limit)


@router.post("/rooms/{room_id}/close")
async def close_chat_room(
    room_id: int,
    user_id: int = Depends(get_current_user_id),
    chat_service: ChatServiceFacade = Depends(get_chat_service_facade),
):
    """Close/deactivate a chat room"""
    success = await chat_service.close_room(room_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )

    return {"message": "Room closed successfully", "room_id": room_id}


@router.get("/my-room", response_model=ChatRoomResponse)
async def get_my_room(
    user_id: int = Depends(get_current_user_id),
    chat_service: ChatServiceFacade = Depends(get_chat_service_facade),
):
    """Get current user's active chat room"""
    room = await chat_service.get_or_create_room(user_id)
    return ChatRoomResponse.model_validate(room)
