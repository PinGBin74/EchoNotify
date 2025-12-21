from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from echonotify.exception import (
    OrderWasNotFoundError,
    UnableToCancelTheOrder,
    UnavailableChangeStatusError,
)
from echonotify.orders.interfaces import IOrderRepository, IUserOrderRepository
from echonotify.orders.models import Orders, OrderStatus, UsersOrder
from echonotify.orders.schema import OrderResponse


class OrderRepository(IOrderRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_order_by_id(self, order_id: int) -> Orders:
        result = await self.session.get(Orders, order_id)
        if result is None:
            raise OrderWasNotFoundError()
        return result

    async def update_status(
        self, order_id: int, status: OrderStatus
    ) -> UsersOrder:
        stmt = (
            update(UsersOrder)
            .where(UsersOrder.order_id == order_id)
            .values(delivery_status=status)
            .returning(UsersOrder)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        order = result.scalar_one_or_none()
        if not order:
            raise ValueError(f"Order {order_id} not found")
        return order

    async def delete_order(self, order_id: int) -> None:
        stmt = delete(Orders).where(Orders.id == order_id)
        await self.session.execute(stmt)
        await self.session.commit()

    async def change_status(
        self, order_id: int, new_status: OrderStatus
    ) -> OrderResponse:
        """Change order status with validation"""
        # Get current order status
        stmt = select(UsersOrder).where(UsersOrder.order_id == order_id)
        result = await self.session.execute(stmt)
        user_order = result.scalar_one_or_none()

        if not user_order:
            raise OrderWasNotFoundError()

        current_status = OrderStatus(user_order.delivery_status)

        # Validate status transitions
        valid_transitions = {
            OrderStatus.PENDING: [OrderStatus.PAID, OrderStatus.CANCELLED],
            OrderStatus.PAID: [OrderStatus.SHIPPED, OrderStatus.CANCELLED],
            OrderStatus.SHIPPED: [OrderStatus.DELIVERED],
            OrderStatus.DELIVERED: [],
            OrderStatus.CANCELLED: [],
        }

        if new_status not in valid_transitions.get(current_status, []):
            raise UnavailableChangeStatusError(
                f"Cannot change status from {current_status} to {new_status}"
            )

        # Update status
        updated_order = await self.update_status(order_id, new_status)

        # Get order details
        order = await self.get_order_by_id(order_id)

        return OrderResponse(
            id=updated_order.id,
            title=order.title,
            price=order.price,
            delivery_status=OrderStatus(updated_order.delivery_status),
            created_at=updated_order.created_at,
            updated_at=updated_order.created_at,
        )

    async def cancel_order(self, order_id: int) -> bool:
        """Cancel order (only PENDING or PAID status)"""
        stmt = select(UsersOrder).where(UsersOrder.order_id == order_id)
        result = await self.session.execute(stmt)
        user_order = result.scalar_one_or_none()

        if not user_order:
            raise OrderWasNotFoundError()

        current_status = OrderStatus(user_order.delivery_status)

        # Can only cancel PENDING or PAID orders
        if current_status not in [OrderStatus.PENDING, OrderStatus.PAID]:
            raise UnableToCancelTheOrder(
                f"Cannot cancel order with status {current_status}"
            )

        # Update status to CANCELLED
        await self.update_status(order_id, OrderStatus.CANCELLED)
        return True

    async def complete_delivery(self, order_id: int) -> OrderResponse:
        """Complete delivery (change status to DELIVERED)"""
        stmt = select(UsersOrder).where(UsersOrder.order_id == order_id)
        result = await self.session.execute(stmt)
        user_order = result.scalar_one_or_none()

        if not user_order:
            raise OrderWasNotFoundError()

        current_status = OrderStatus(user_order.delivery_status)

        # Can only complete delivery from SHIPPED status
        if current_status != OrderStatus.SHIPPED:
            raise UnavailableChangeStatusError(
                f"Cannot complete delivery from status {current_status}"
            )

        # Update status to DELIVERED
        updated_order = await self.update_status(
            order_id, OrderStatus.DELIVERED
        )

        # Get order details
        order = await self.get_order_by_id(order_id)

        return OrderResponse(
            id=updated_order.id,
            title=order.title,
            price=order.price,
            delivery_status=OrderStatus(updated_order.delivery_status),
            created_at=updated_order.created_at,
            updated_at=updated_order.created_at,
        )


class UserOrderRepository(IUserOrderRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_order(self, user_id: int, order_id: int) -> UsersOrder:
        user_order = UsersOrder(
            user_id=user_id,
            order_id=order_id,
            delivery_status=OrderStatus.PENDING,
        )
        self.session.add(user_order)
        await self.session.commit()
        await self.session.refresh(user_order)
        return user_order

    async def get_user_order(
        self, user_id: int, order_id: int
    ) -> list[UsersOrder]:
        stmt = select(UsersOrder).where(
            UsersOrder.user_id == user_id, UsersOrder.order_id == order_id
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_user_orders(
        self, user_id: int, status: OrderStatus | None = None
    ) -> list[OrderResponse]:
        """Get all orders by user's id with optional status filter"""
        if status:
            stmt = (
                select(UsersOrder, Orders)
                .join(Orders, UsersOrder.order_id == Orders.id)
                .where(
                    UsersOrder.user_id == user_id,
                    UsersOrder.delivery_status == status,
                )
            )
        else:
            stmt = (
                select(UsersOrder, Orders)
                .join(Orders, UsersOrder.order_id == Orders.id)
                .where(UsersOrder.user_id == user_id)
            )

        result = await self.session.execute(stmt)
        orders_data = result.all()

        return [
            OrderResponse(
                id=user_order.id,
                title=order.title,
                price=order.price,
                delivery_status=OrderStatus(user_order.delivery_status),
                created_at=user_order.created_at,
                updated_at=user_order.created_at,
            )
            for user_order, order in orders_data
        ]
