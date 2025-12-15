from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from echonotify.exception import OrderWasNotFoundError
from echonotify.orders.interfaces import IOrderRepository, IUserOrderRepository
from echonotify.orders.models import Orders, OrderStatus, UsersOrder


class OrderRepository(IOrderRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_order_by_id(self, order_id: int) -> Orders:
        try:
            result = await self.session.get(Orders, order_id)
            return result

        except Exception as e:
            raise OrderWasNotFoundError() from e

    async def update_status(self, order_id: int, status: OrderStatus):
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
        result = await self.session.execute(stmt)
        await self.session.commit()

        if result.rowcount == 0:
            raise ValueError(f"Order {order_id} not found")


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
        return result.scalars().all()
