from fastapi import APIRouter, Depends, HTTPException, Query
from starlette import status as http_status

from echonotify.exception import (
    OrderWasNotFoundError,
    UnableToCancelTheOrder,
    UnavailableChangeStatusError,
)
from echonotify.orders.dependencies import get_order_service
from echonotify.orders.models import OrderStatus
from echonotify.orders.schema import OrderResponse
from echonotify.orders.service import OrderService
from echonotify.users.dependencies import get_current_user_id

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/", response_model=list[OrderResponse])
async def get_user_orders(
    status: OrderStatus | None = Query(
        None, description="Filter orders by status"
    ),
    user_id: int = Depends(get_current_user_id),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Get all orders for the current user.
    Optionally filter by order status.
    """
    orders = await order_service.get_user_orders(user_id, status)
    return orders


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def change_order_status(
    order_id: int,
    new_status: OrderStatus,
    user_id: int = Depends(get_current_user_id),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Change the status of an order.
    Valid transitions:
    - PENDING -> PAID, CANCELLED
    - PAID -> SHIPPED, CANCELLED
    - SHIPPED -> DELIVERED
    """
    try:
        order = await order_service.change_status(order_id, new_status)
        return order
    except OrderWasNotFoundError as e:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        ) from e
    except UnavailableChangeStatusError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/{order_id}/cancel", response_model=dict)
async def cancel_order(
    order_id: int,
    user_id: int = Depends(get_current_user_id),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Cancel an order.
    Only orders with status PENDING or PAID can be cancelled.
    """
    try:
        result = await order_service.cancel_order(order_id)
        if result:
            return {
                "message": "Order cancelled successfully",
                "order_id": order_id,
            }
    except OrderWasNotFoundError as e:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        ) from e
    except UnableToCancelTheOrder as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/{order_id}/complete", response_model=OrderResponse)
async def complete_order_delivery(
    order_id: int,
    user_id: int = Depends(get_current_user_id),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Complete order delivery.
    Only orders with status SHIPPED can be marked as DELIVERED.
    """
    try:
        order = await order_service.complete_delivery(order_id)
        return order
    except OrderWasNotFoundError as e:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        ) from e
    except UnavailableChangeStatusError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
