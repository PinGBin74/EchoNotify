from datetime import datetime
from enum import Enum

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from echonotify.auth.utils import utc_now_naive
from echonotify.infrastructure.database.models import Base


class MessageStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"


class UserRole(str, Enum):
    USER = "user"
    SUPPORT = "support"


class ChatRoom(Base):
    __tablename__ = "chat_room"

    id: Mapped[int] = mapped_column(
        primary_key=True, nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_profile.id"), nullable=False, index=True
    )
    support_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_profile.id"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_public: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=utc_now_naive, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=utc_now_naive,
        onupdate=utc_now_naive,
        nullable=False,
    )


class ChatMessage(Base):
    __tablename__ = "chat_message"

    id: Mapped[int] = mapped_column(
        primary_key=True, nullable=False, index=True
    )
    room_id: Mapped[int] = mapped_column(
        ForeignKey("chat_room.id"), nullable=False, index=True
    )
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("user_profile.id"), nullable=False
    )
    sender_role: Mapped[str] = mapped_column(nullable=False)
    message: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(
        default=MessageStatus.SENT.value, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        default=utc_now_naive, nullable=False, index=True
    )
