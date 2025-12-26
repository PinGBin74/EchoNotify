from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from echonotify.orders.models import OrderStatus


class OrderCreate(BaseModel):
    order_id: int
    user_id: int
    title: str


class OrderUpdate(BaseModel):
    title: Optional[str] = None
    price: Optional[float] = None
    delivery_status: OrderStatus


class OrderResponse(BaseModel):
    id: int
    title: str
    price: float
    delivery_status: OrderStatus
    created_at: datetime
    updated_at: datetime
