from datetime import datetime

import grpc

from hsp_order_service.domain.errors import ConflictError, NotFoundError, ValidationError
from hsp_order_service.domain.models import SourceType
from hsp_order_service.service.echo_service import EchoService
from hsp_order_service.service.order_service import OrderService
from hsp_order_service.transport.grpc.mapper import (
    to_domain_order_status,
    to_domain_service_type,
    to_grpc_order,
    to_grpc_record,
)
from rpc.echo.v1 import echo_pb2, echo_pb2_grpc
from rpc.order.v1 import order_pb2, order_pb2_grpc


class EchoGrpcService(echo_pb2_grpc.EchoServiceServicer):
    def __init__(self, echo_service: EchoService) -> None:
        self._echo_service = echo_service

    async def CreateEcho(
        self,
        request: echo_pb2.CreateEchoRequest,
        context: grpc.aio.ServicerContext,
    ) -> echo_pb2.CreateEchoResponse:
        try:
            record = await self._echo_service.create_echo(request.message, SourceType.GRPC)
        except ValidationError as exc:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        return echo_pb2.CreateEchoResponse(record=to_grpc_record(record))

    async def GetEcho(
        self,
        request: echo_pb2.GetEchoRequest,
        context: grpc.aio.ServicerContext,
    ) -> echo_pb2.GetEchoResponse:
        try:
            record = await self._echo_service.get_echo(request.id)
        except ValidationError as exc:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except NotFoundError as exc:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
        return echo_pb2.GetEchoResponse(record=to_grpc_record(record))

    async def Health(
        self,
        request: echo_pb2.HealthRequest,
        context: grpc.aio.ServicerContext,
    ) -> echo_pb2.HealthResponse:
        del request, context
        return echo_pb2.HealthResponse(status="ok")


class OrderGrpcService(order_pb2_grpc.OrderServiceServicer):
    def __init__(self, order_service: OrderService) -> None:
        self._order_service = order_service

    async def CreateOrder(
        self,
        request: order_pb2.CreateOrderRequest,
        context: grpc.aio.ServicerContext,
    ) -> order_pb2.CreateOrderResponse:
        try:
            order = await self._order_service.create_order(
                customer_name=request.customer_name,
                phone=request.phone,
                service_address=request.service_address,
                service_type=to_domain_service_type(request.service_type),
                appointment_time=_parse_iso_datetime(request.appointment_time),
                estimated_duration_minutes=request.estimated_duration_minutes,
            )
        except ValidationError as exc:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        return order_pb2.CreateOrderResponse(order=to_grpc_order(order))

    async def GetOrder(
        self,
        request: order_pb2.GetOrderRequest,
        context: grpc.aio.ServicerContext,
    ) -> order_pb2.GetOrderResponse:
        try:
            order = await self._order_service.get_order(request.order_id)
        except ValidationError as exc:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except NotFoundError as exc:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
        return order_pb2.GetOrderResponse(order=to_grpc_order(order))

    async def ListOrders(
        self,
        request: order_pb2.ListOrdersRequest,
        context: grpc.aio.ServicerContext,
    ) -> order_pb2.ListOrdersResponse:
        try:
            service_type = (
                to_domain_service_type(request.service_type)
                if request.service_type != order_pb2.SERVICE_TYPE_UNSPECIFIED
                else None
            )
            status = (
                to_domain_order_status(request.status)
                if request.status != order_pb2.ORDER_STATUS_UNSPECIFIED
                else None
            )
            page = request.page or 1
            page_size = request.page_size or 20
            items, total = await self._order_service.list_orders(
                customer_name=request.customer_name,
                service_type=service_type,
                status=status,
                page=page,
                page_size=page_size,
            )
        except ValidationError as exc:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))

        return order_pb2.ListOrdersResponse(
            items=[to_grpc_order(item) for item in items],
            page=page,
            page_size=page_size,
            total=total,
        )

    async def UpdateOrderStatus(
        self,
        request: order_pb2.UpdateOrderStatusRequest,
        context: grpc.aio.ServicerContext,
    ) -> order_pb2.UpdateOrderStatusResponse:
        try:
            if request.target_status == order_pb2.ORDER_STATUS_CREATED:
                raise ValidationError("target_status does not allow created")

            order = await self._order_service.update_order_status(
                order_id=request.order_id,
                target_status=to_domain_order_status(request.target_status),
                assigned_worker_id=request.assigned_worker_id,
            )
        except ValidationError as exc:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except NotFoundError as exc:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
        except ConflictError as exc:
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, str(exc))

        return order_pb2.UpdateOrderStatusResponse(order=to_grpc_order(order))


def _parse_iso_datetime(value: str) -> datetime:
    candidate = value.strip()
    if not candidate:
        raise ValidationError("appointment_time must not be empty")

    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValidationError("appointment_time must be valid ISO-8601 datetime") from exc
    return parsed
