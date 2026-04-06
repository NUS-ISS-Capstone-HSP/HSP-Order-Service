import grpc

from hsp_order_service.config import Settings
from hsp_order_service.service.echo_service import EchoService
from hsp_order_service.service.order_service import OrderService
from hsp_order_service.transport.grpc.service import EchoGrpcService, OrderGrpcService
from rpc.echo.v1 import echo_pb2_grpc
from rpc.order.v1 import order_pb2_grpc


def build_grpc_server(
    settings: Settings,
    echo_service: EchoService,
    order_service: OrderService,
) -> grpc.aio.Server:
    server = grpc.aio.server()
    echo_pb2_grpc.add_EchoServiceServicer_to_server(EchoGrpcService(echo_service), server)
    order_pb2_grpc.add_OrderServiceServicer_to_server(OrderGrpcService(order_service), server)
    server.add_insecure_port(f"{settings.grpc_host}:{settings.grpc_port}")
    return server
