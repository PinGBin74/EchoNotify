from datetime import datetime

from pydantic import BaseModel

from echonotify.orders.models import OrderStatus


class OrderCreate(BaseModel):
    order_id: int
    user_id: int
    title: str


class OrderUpdate(BaseModel):
    title: str | None = None
    price: float | None = None
    delivery_status: OrderStatus


class OrderResponse(BaseModel):
    id: int
    title: str
    price: float
    delivery_status: OrderStatus
    created_at: datetime
    updated_at: datetime
