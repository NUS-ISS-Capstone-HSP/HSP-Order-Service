from fastapi import APIRouter, Path, Query

from hsp_order_service.domain.models import OrderStatus, ServiceType, SourceType
from hsp_order_service.service.echo_service import EchoService
from hsp_order_service.service.order_service import OrderService
from hsp_order_service.transport.http.mapper import to_http_response, to_order_response
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

    # ── Echo (existing) ──

    @router.post("/echo", response_model=EchoRecordResponse, status_code=201)
    async def create_echo(payload: CreateEchoRequest) -> EchoRecordResponse:
        record = await echo_service.create_echo(payload.message, SourceType.HTTP)
        return to_http_response(record)

    @router.get("/echo/{echo_id}", response_model=EchoRecordResponse)
    async def get_echo(echo_id: str = Path(...)) -> EchoRecordResponse:
        record = await echo_service.get_echo(echo_id)
        return to_http_response(record)

    # ── Orders ──

    @router.post("/orders", response_model=OrderResponse, status_code=201)
    async def create_order(payload: CreateOrderRequest) -> OrderResponse:
        order = await order_service.create_order(
            customer_name=payload.customer_name,
            phone=payload.phone,
            service_address=payload.service_address,
            service_type=ServiceType(payload.service_type.upper()),
            appointment_time=payload.appointment_time,
            estimated_duration_minutes=payload.estimated_duration_minutes,
        )
        return to_order_response(order)

    @router.get("/orders/{order_id}", response_model=OrderResponse)
    async def get_order(order_id: str = Path(...)) -> OrderResponse:
        order = await order_service.get_order(order_id)
        return to_order_response(order)

    @router.get("/orders", response_model=ListOrdersResponse)
    async def list_orders(
        customer_name: str = Query(default=""),
        service_type: str | None = Query(default=None),
        status: str | None = Query(default=None),
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=100),
    ) -> ListOrdersResponse:
        st = ServiceType(service_type.upper()) if service_type else None
        ost = OrderStatus(status.upper()) if status else None
        items, total = await order_service.list_orders(
            customer_name=customer_name,
            service_type=st,
            status=ost,
            page=page,
            page_size=page_size,
        )
        return ListOrdersResponse(
            items=[to_order_response(o) for o in items],
            page=page,
            page_size=page_size,
            total=total,
        )

    @router.patch("/orders/{order_id}/status", response_model=OrderResponse)
    async def update_order_status(
        order_id: str = Path(...),
        payload: UpdateOrderStatusRequest = ...,
    ) -> OrderResponse:
        order = await order_service.update_order_status(
            order_id=order_id,
            target_status=OrderStatus(payload.target_status.upper()),
            assigned_worker_id=payload.assigned_worker_id,
        )
        return to_order_response(order)

    return router
