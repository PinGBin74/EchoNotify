from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from echonotify.infrastructure.database.database import get_db_session
from echonotify.orders.repository import OrderRepository, UserOrderRepository
from echonotify.orders.service import OrderService


async def get_order_service(
    session: AsyncSession = Depends(get_db_session),
) -> OrderService:
    """Dependency for getting OrderService instance"""
    order_repository = OrderRepository(session)
    user_repository = UserOrderRepository(session)

    return OrderService(
        session=session,
        order_repository=order_repository,
        user_repository=user_repository,
    )
