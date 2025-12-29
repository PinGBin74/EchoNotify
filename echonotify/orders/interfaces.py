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
    ) -> UsersOrder:
        """Update status by order_id"""
        ...

    async def delete_order(self, order_id: int) -> None:
        """Delete order by order_id"""
        ...

    async def get_user_order_by_order_id(self, order_id: int) -> UsersOrder:
        """Get user order by order_id"""
        ...

    async def change_status(
        self, order_id: int, new_status: OrderStatus
    ) -> OrderResponse:
        """Change order status"""
        ...

    async def cancel_order(self, order_id: int) -> bool:
        """Cancel order"""
        ...

    async def complete_delivery(self, order_id: int) -> OrderResponse:
        """Complete delivery"""
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

    async def get_user_orders(
        self, user_id: int, status: OrderStatus | None = None
    ) -> list[OrderResponse]:
        """Get all orders by user's id with optional status filter"""
        ...


class IOrderService(Protocol):
    """Interface for business logic(Orders)"""

    async def get_user_orders(
        self, user_id: int, status: OrderStatus | None = None
    ) -> list[OrderResponse]:
        """Get user's orders"""
        ...

    async def change_status(
        self, order_id: int, new_status: OrderStatus
    ) -> OrderResponse:
        """Change order's status"""
        ...

    async def cancel_order(self, order_id: int) -> bool:
        """Cancel order (only PENDING/PAID)"""
        ...

    async def complete_delivery(self, order_id: int) -> OrderResponse:
        """Finish delivery"""
        ...
