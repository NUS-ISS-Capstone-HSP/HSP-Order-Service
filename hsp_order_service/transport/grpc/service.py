import grpc

from hsp_order_service.domain.errors import NotFoundError, TransitionError, ValidationError
from hsp_order_service.domain.models import SourceType
from hsp_order_service.service.echo_service import EchoService
from hsp_order_service.service.order_service import OrderService
from hsp_order_service.transport.grpc.mapper import (
    order_status_from_proto,
    service_type_from_proto,
    to_grpc_order,
    to_grpc_record,
)
from rpc.echo.v1 import echo_pb2, echo_pb2_grpc
from rpc.order.v1 import order_pb2, order_pb2_grpc


class EchoGrpcService(echo_pb2_grpc.EchoServiceServicer):
    def __init__(self, echo_service: EchoService) -> None:
        self._echo_service = echo_service

    async def CreateEcho(self, request, context):
        try:
            record = await self._echo_service.create_echo(request.message, SourceType.GRPC)
        except ValidationError as exc:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        return echo_pb2.CreateEchoResponse(record=to_grpc_record(record))

    async def GetEcho(self, request, context):
        try:
            record = await self._echo_service.get_echo(request.id)
        except ValidationError as exc:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except NotFoundError as exc:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
        return echo_pb2.GetEchoResponse(record=to_grpc_record(record))

    async def Health(self, request, context):
        del request, context
        return echo_pb2.HealthResponse(status="ok")


class OrderGrpcService(order_pb2_grpc.OrderServiceServicer):
    def __init__(self, order_service: OrderService) -> None:
        self._order_service = order_service

    async def CreateOrder(self, request, context):
        try:
            order = await self._order_service.create_order(
                customer_name=request.customer_name,
                phone=request.phone,
                service_address=request.service_address,
                service_type=service_type_from_proto(request.service_type),
                appointment_time=request.appointment_time,
                estimated_duration_minutes=request.estimated_duration_minutes,
            )
        except ValidationError as exc:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        return order_pb2.CreateOrderResponse(order=to_grpc_order(order))

    async def GetOrder(self, request, context):
        try:
            order = await self._order_service.get_order(request.order_id)
        except ValidationError as exc:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except NotFoundError as exc:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
        return order_pb2.GetOrderResponse(order=to_grpc_order(order))

    async def ListOrders(self, request, context):
        status = order_status_from_proto(request.status)
        service_type = None
        if request.service_type != order_pb2.SERVICE_TYPE_UNSPECIFIED:
            service_type = service_type_from_proto(request.service_type)
        items, total = await self._order_service.list_orders(
            customer_name=request.customer_name,
            service_type=service_type,
            status=status,
            page=request.page,
            page_size=request.page_size,
        )
        return order_pb2.ListOrdersResponse(
            items=[to_grpc_order(o) for o in items],
            page=request.page,
            page_size=request.page_size,
            total=total,
        )

    async def UpdateOrderStatus(self, request, context):
        target = order_status_from_proto(request.target_status)
        if target is None:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "invalid target status")
            return order_pb2.UpdateOrderStatusResponse()
        try:
            order = await self._order_service.update_order_status(
                order_id=request.order_id,
                target_status=target,
                assigned_worker_id=request.assigned_worker_id,
            )
        except ValidationError as exc:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except NotFoundError as exc:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
        except TransitionError as exc:
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, str(exc))
        return order_pb2.UpdateOrderStatusResponse(order=to_grpc_order(order))
