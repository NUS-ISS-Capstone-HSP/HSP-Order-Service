import grpc
import pytest
import pytest_asyncio

from hsp_order_service.repository.order_in_memory import InMemoryOrderRepository
from hsp_order_service.service.order_service import OrderService
from hsp_order_service.transport.grpc.service import OrderGrpcService
from rpc.order.v1 import order_pb2, order_pb2_grpc


@pytest_asyncio.fixture
async def grpc_stub() -> order_pb2_grpc.OrderServiceStub:
    service = OrderService(InMemoryOrderRepository())

    server = grpc.aio.server()
    order_pb2_grpc.add_OrderServiceServicer_to_server(OrderGrpcService(service), server)
    port = server.add_insecure_port("127.0.0.1:0")
    await server.start()

    channel = grpc.aio.insecure_channel(f"127.0.0.1:{port}")
    stub = order_pb2_grpc.OrderServiceStub(channel)

    try:
        yield stub
    finally:
        await channel.close()
        await server.stop(0)


@pytest.mark.asyncio
async def test_create_and_get_order_success(grpc_stub: order_pb2_grpc.OrderServiceStub) -> None:
    created = await grpc_stub.CreateOrder(
        order_pb2.CreateOrderRequest(
            customer_name="Alice",
            phone="13812345678",
            service_address="Shanghai Road 100",
            service_type=order_pb2.SERVICE_TYPE_CLEANING,
            appointment_time="2026-04-10T09:00:00+08:00",
            estimated_duration_minutes=120,
        )
    )

    fetched = await grpc_stub.GetOrder(order_pb2.GetOrderRequest(order_id=created.order.order_id))

    assert created.order.status == order_pb2.ORDER_STATUS_CREATED
    assert fetched.order.order_id == created.order.order_id


@pytest.mark.asyncio
async def test_list_orders_with_status_filter(grpc_stub: order_pb2_grpc.OrderServiceStub) -> None:
    created = await grpc_stub.CreateOrder(
        order_pb2.CreateOrderRequest(
            customer_name="Alice",
            phone="13812345678",
            service_address="Shanghai Road 100",
            service_type=order_pb2.SERVICE_TYPE_CLEANING,
            appointment_time="2026-04-10T09:00:00+08:00",
            estimated_duration_minutes=120,
        )
    )

    await grpc_stub.UpdateOrderStatus(
        order_pb2.UpdateOrderStatusRequest(
            order_id=created.order.order_id,
            target_status=order_pb2.ORDER_STATUS_PENDING,
            assigned_worker_id="worker-001",
        )
    )

    listed = await grpc_stub.ListOrders(
        order_pb2.ListOrdersRequest(status=order_pb2.ORDER_STATUS_PENDING, page=1, page_size=20)
    )

    assert listed.total == 1
    assert listed.items[0].status == order_pb2.ORDER_STATUS_PENDING


@pytest.mark.asyncio
async def test_update_order_status_reject_illegal_transition(
    grpc_stub: order_pb2_grpc.OrderServiceStub,
) -> None:
    created = await grpc_stub.CreateOrder(
        order_pb2.CreateOrderRequest(
            customer_name="Alice",
            phone="13812345678",
            service_address="Shanghai Road 100",
            service_type=order_pb2.SERVICE_TYPE_CLEANING,
            appointment_time="2026-04-10T09:00:00+08:00",
            estimated_duration_minutes=120,
        )
    )

    with pytest.raises(grpc.aio.AioRpcError) as exc_info:
        await grpc_stub.UpdateOrderStatus(
            order_pb2.UpdateOrderStatusRequest(
                order_id=created.order.order_id,
                target_status=order_pb2.ORDER_STATUS_COMPLETE,
            )
        )

    assert exc_info.value.code() == grpc.StatusCode.FAILED_PRECONDITION
