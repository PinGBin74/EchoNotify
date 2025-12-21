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
        """Change order's status"""
        try:
            order = await self.order_repository.change_status(
                order_id, new_status
            )
            return order
        except UnavailableChangeStatusError as e:
            raise e from e

    async def cancel_order(self, order_id: int) -> bool:
        try:
            result = await self.order_repository.cancel_order(order_id)
            return result
        except UnableToCancelTheOrder as e:
            raise e from e

    async def complete_delivery(self, order_id: int) -> OrderResponse:
        """Finish delivery"""
        try:
            order = await self.order_repository.complete_delivery(order_id)
            return order
        except UnavailableChangeStatusError as e:
            raise e from e
