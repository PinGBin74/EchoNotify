from datetime import datetime
from typing import Protocol

from echonotify.orders.models import Orders, OrderStatus, UsersOrder
from echonotify.orders.schema import OrderResponse


class IOrderRepository(Protocol):
    """Interface for work with orders"""

    async def get_order_by_id(self, order_id: int) -> Orders:
        """Get order by id"""
        ...

    async def update_status(
        self, order_id: int, status: OrderStatus
    ) -> Orders:
        """Update status by order_id"""
        ...

    async def delete_order(self, order_id: int) -> None:
        """Delete order by order_id"""
        ...


class IUserOrderRepository(Protocol):
    """Interface for work with orders"""

    async def create_order(self, user_id: int, order_id: int) -> UsersOrder:
        """Create order for user by user_id and order_id"""
        ...

    async def get_user_order(
        self, user_id: int, order_id: int
    ) -> list[UsersOrder]:
        """Get user's orders by user_id and order_id"""
        ...


class IOrderService(Protocol):
    """Interface for business logic(Orders)"""

    async def get_user_orders(
        self, user_id: int, status: OrderStatus = None
    ) -> list[OrderResponse]:
        """Get user's orders"""
        pass

    async def change_status(
        self, order_id: int, new_status: OrderStatus
    ) -> OrderResponse:
        """Change order's status"""
        pass

    async def cancel_order(self, order_id: int) -> bool:
        """Cancell order (only PENDING/PAID)"""
        pass

    async def complete_delivery(self, order_id: int) -> OrderResponse:
        """Finish delivery"""
        pass


class IOrderStatistics(Protocol):
    """Statistics about orders"""

    async def get_user_stats(self, user_id: int) -> dict:
        """User's statistics about orders: quantity, amount, average check bill"""
        pass

    async def get_total_revenue(
        self, status: OrderStatus, date_from: datetime, date_to: datetime
    ) -> float:
        """Get total revenue"""
        pass
