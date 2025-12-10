from datetime import datetime
from enum import Enum

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from echonotify.auth.utils import utc_now_naive
from echonotify.infrastructure.database.models import Base


class OrderStatus(str, Enum):
    PENDING = "pending"  # new order
    PAID = "paid"  # paid
    SHIPPED = "shipped"  # in delivery
    DELIVERED = "delivered"  # delivered
    CANCELLED = "cancelled"  # cancelled


class Orders(Base):
    __tablename__ = "Orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(nullable=False)
    created_ad: Mapped[datetime] = mapped_column(nullable=False)
    price: Mapped[float] = mapped_column(default=0.0)

    orders = relationship("UsersOrder", back_populates="order", uselist=False)


class UsersOrder(Base):
    __tablename__ = "UsersOrders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("UserProfile.id"), index=True
    )
    order_id: Mapped[int] = mapped_column(ForeignKey("Orders.id"), index=True)
    delivery_status: Mapped[Enum] = mapped_column(default=OrderStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(default=utc_now_naive)

    users_orders = relationship("Orders", back_populates="user", uselist=False)
