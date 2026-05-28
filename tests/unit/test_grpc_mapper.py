from datetime import UTC, datetime

from hsp_order_service.domain.models import Order, OrderStatus, ServiceType
from hsp_order_service.transport.grpc.mapper import (
    order_status_from_proto,
    service_type_from_proto,
    to_grpc_order,
)
from rpc.order.v1 import order_pb2


def build_order() -> Order:
    timestamp = datetime(2026, 4, 8, 2, 0, tzinfo=UTC)
    return Order(
        order_id="order-1",
        customer_name="Alice",
        phone="13800000000",
        service_address="Shanghai",
        service_type=ServiceType.INSTALL,
        appointment_time="2026-04-08T10:00:00+08:00",
        estimated_duration_minutes=90,
        status=OrderStatus.ACCEPT,
        assigned_worker_id="worker-1",
        status_updated_at=timestamp,
        created_at=timestamp,
        updated_at=timestamp,
    )


def test_to_grpc_order_maps_domain_fields() -> None:
    order = build_order()

    result = to_grpc_order(order)

    assert result.order_id == "order-1"
    assert result.service_type == order_pb2.SERVICE_TYPE_INSTALL
    assert result.status == order_pb2.ORDER_STATUS_ACCEPT
    assert result.assigned_worker_id == "worker-1"
    assert result.status_updated_at == "2026-04-08T02:00:00+00:00"


def test_service_type_from_proto_maps_known_and_unknown_values() -> None:
    assert service_type_from_proto(order_pb2.SERVICE_TYPE_CLEANING) == ServiceType.CLEANING
    assert service_type_from_proto(order_pb2.SERVICE_TYPE_REPAIR) == ServiceType.REPAIR
    assert service_type_from_proto(order_pb2.SERVICE_TYPE_INSTALL) == ServiceType.INSTALL
    assert service_type_from_proto(order_pb2.SERVICE_TYPE_OTHER) == ServiceType.OTHER
    assert service_type_from_proto(999) == ServiceType.OTHER


def test_order_status_from_proto_maps_known_unspecified_and_unknown_values() -> None:
    assert order_status_from_proto(order_pb2.ORDER_STATUS_CREATED) == OrderStatus.CREATED
    assert order_status_from_proto(order_pb2.ORDER_STATUS_PENDING) == OrderStatus.PENDING
    assert order_status_from_proto(order_pb2.ORDER_STATUS_ACCEPT) == OrderStatus.ACCEPT
    assert order_status_from_proto(order_pb2.ORDER_STATUS_COMPLETE) == OrderStatus.COMPLETE
    assert order_status_from_proto(order_pb2.ORDER_STATUS_PAID) == OrderStatus.PAID
    assert order_status_from_proto(order_pb2.ORDER_STATUS_UNSPECIFIED) is None
    assert order_status_from_proto(999) is None
