from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ChatMessageCreate(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_id: int
    sender_id: int
    sender_role: str
    message: str
    status: str
    created_at: datetime


class ChatRoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    support_id: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class WebSocketMessage(BaseModel):
    type: str  # "message", "typing", "notification"
    room_id: Optional[int] = None
    sender_id: Optional[int] = None
    sender_name: Optional[str] = None
    sender_role: Optional[str] = None
    message: Optional[str] = None
    timestamp: Optional[datetime] = None
    message_id: Optional[int] = None


class ChatHistoryResponse(BaseModel):
    room_id: int
    messages: list[ChatMessageResponse]
    total: int
