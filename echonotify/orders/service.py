from sqlalchemy.ext.asyncio import AsyncSession

from echonotify.exception import (
    UnableToCancelTheOrder,
    UnavailableChangeStatusError,
)
from echonotify.orders.interfaces import (
    IOrderRepository,
    IOrderService,
    IUserOrderRepository,
)
from echonotify.orders.models import OrderStatus
from echonotify.orders.schema import OrderResponse


class OrderService(IOrderService):
    VALID_TRANSITIONS = {
        OrderStatus.PENDING: [OrderStatus.PAID, OrderStatus.CANCELLED],
        OrderStatus.PAID: [OrderStatus.SHIPPED, OrderStatus.CANCELLED],
        OrderStatus.SHIPPED: [OrderStatus.DELIVERED],
        OrderStatus.DELIVERED: [],
        OrderStatus.CANCELLED: [],
    }

    def __init__(
        self,
        session: AsyncSession,
        order_repository: IOrderRepository,
        user_repository: IUserOrderRepository,
    ):
        self.session = session
        self.order_repository = order_repository
        self.user_repository = user_repository

    async def get_user_orders(
        self, user_id: int, status: OrderStatus | None = None
    ) -> list[OrderResponse]:
        """Get all orders by user's id"""
        orders = await self.user_repository.get_user_orders(user_id, status)
        return orders

    async def change_status(
        self, order_id: int, new_status: OrderStatus
    ) -> OrderResponse:
        """Change order's status with validation"""
        user_order = await self.order_repository.get_user_order_by_order_id(
            order_id
        )
        current_status = OrderStatus(user_order.delivery_status)

        if new_status not in self.VALID_TRANSITIONS.get(current_status, []):
            raise UnavailableChangeStatusError(
                f"Cannot change status from {current_status} to {new_status}"
            )

        order = await self.order_repository.change_status(order_id, new_status)
        return order

    async def cancel_order(self, order_id: int) -> bool:
        """Cancel order (only PENDING or PAID status)"""
        user_order = await self.order_repository.get_user_order_by_order_id(
            order_id
        )
        current_status = OrderStatus(user_order.delivery_status)

        if current_status not in [OrderStatus.PENDING, OrderStatus.PAID]:
            raise UnableToCancelTheOrder(
                f"Cannot cancel order with status {current_status}"
            )

        result = await self.order_repository.cancel_order(order_id)
        return result

    async def complete_delivery(self, order_id: int) -> OrderResponse:
        """Complete delivery (only SHIPPED status)"""
        user_order = await self.order_repository.get_user_order_by_order_id(
            order_id
        )
        current_status = OrderStatus(user_order.delivery_status)

        if current_status != OrderStatus.SHIPPED:
            raise UnavailableChangeStatusError(
                f"Cannot complete delivery from status {current_status}"
            )

        order = await self.order_repository.complete_delivery(order_id)
        return order
