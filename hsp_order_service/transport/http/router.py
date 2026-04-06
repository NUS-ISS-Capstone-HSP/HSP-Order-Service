from typing import Annotated

from fastapi import APIRouter, Path, Query

from hsp_order_service.domain.models import OrderStatus, ServiceType, SourceType
from hsp_order_service.service.echo_service import EchoService
from hsp_order_service.service.order_service import OrderService
from hsp_order_service.transport.http.mapper import to_http_order_response, to_http_response
from hsp_order_service.transport.http.schemas import (
    CreateEchoRequest,
    CreateOrderRequest,
    EchoRecordResponse,
    ListOrdersResponse,
    OrderResponse,
    UpdateOrderStatusRequest,
)


def build_router(echo_service: EchoService, order_service: OrderService) -> APIRouter:
    router = APIRouter(prefix="/api/orders/v1", tags=["orders"])

    @router.post(
        "/echo",
        response_model=EchoRecordResponse,
        status_code=201,
        summary="Create echo record",
        description="Store an echo message and return the created record.",
        response_description="Created echo record.",
        responses={
            400: {"description": "Business validation failed."},
            422: {"description": "Request payload validation failed."},
        },
    )
    async def create_echo(payload: CreateEchoRequest) -> EchoRecordResponse:
        """Create an echo record using shared service logic."""
        record = await echo_service.create_echo(payload.message, SourceType.HTTP)
        return to_http_response(record)

    @router.get(
        "/echo/{echo_id}",
        response_model=EchoRecordResponse,
        summary="Get echo record by id",
        description="Query a previously created echo record.",
        response_description="Echo record details.",
        responses={
            400: {"description": "Business validation failed."},
            404: {"description": "Echo record was not found."},
        },
    )
    async def get_echo(
        echo_id: str = Path(..., description="Echo record id (UUID)."),
    ) -> EchoRecordResponse:
        """Get one echo record by its id."""
        record = await echo_service.get_echo(echo_id)
        return to_http_response(record)

    @router.post(
        "/orders",
        response_model=OrderResponse,
        status_code=201,
        summary="Create order",
        description="Create an order with structured fields.",
        responses={
            400: {"description": "Business validation failed."},
            422: {"description": "Request payload validation failed."},
        },
    )
    async def create_order(payload: CreateOrderRequest) -> OrderResponse:
        order = await order_service.create_order(
            customer_name=payload.customer_name,
            phone=payload.phone,
            service_address=payload.service_address,
            service_type=payload.service_type,
            appointment_time=payload.appointment_time,
            estimated_duration_minutes=payload.estimated_duration_minutes,
        )
        return to_http_order_response(order)

    @router.get(
        "/orders/{order_id}",
        response_model=OrderResponse,
        summary="Get order by id",
        description="Query one order by order id.",
        responses={
            400: {"description": "Business validation failed."},
            404: {"description": "Order was not found."},
        },
    )
    async def get_order(order_id: str = Path(..., description="Order id (UUID).")) -> OrderResponse:
        order = await order_service.get_order(order_id)
        return to_http_order_response(order)

    @router.get(
        "/orders",
        response_model=ListOrdersResponse,
        summary="List orders",
        description="List orders with filters and pagination.",
        responses={
            400: {"description": "Business validation failed."},
        },
    )
    async def list_orders(
        customer_name: str | None = None,
        service_type: Annotated[ServiceType | None, Query()] = None,
        status: Annotated[OrderStatus | None, Query()] = None,
        page: Annotated[int, Query(ge=1)] = 1,
        page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    ) -> ListOrdersResponse:
        items, total = await order_service.list_orders(
            customer_name=customer_name,
            service_type=service_type,
            status=status,
            page=page,
            page_size=page_size,
        )
        return ListOrdersResponse(
            items=[to_http_order_response(item) for item in items],
            page=page,
            page_size=page_size,
            total=total,
        )

    @router.patch(
        "/orders/{order_id}/status",
        response_model=OrderResponse,
        summary="Update order status",
        description="Transit order status by finite state machine.",
        responses={
            400: {"description": "Business validation failed."},
            404: {"description": "Order was not found."},
            409: {"description": "Illegal order status transition."},
        },
    )
    async def update_order_status(
        payload: UpdateOrderStatusRequest,
        order_id: str = Path(..., description="Order id (UUID)."),
    ) -> OrderResponse:
        order = await order_service.update_order_status(
            order_id=order_id,
            target_status=OrderStatus(payload.target_status),
            assigned_worker_id=payload.assigned_worker_id,
        )
        return to_http_order_response(order)

    return router
