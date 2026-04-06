from hsp_order_service.domain.errors import ValidationError
from hsp_order_service.domain.models import EchoRecord, Order, OrderStatus, ServiceType
from rpc.echo.v1 import echo_pb2
from rpc.order.v1 import order_pb2


def to_grpc_record(record: EchoRecord) -> echo_pb2.EchoRecord:
    return echo_pb2.EchoRecord(
        id=record.id,
        message=record.message,
        source=record.source.value,
        created_at=record.created_at.isoformat(),
    )


def to_grpc_order(order: Order) -> order_pb2.Order:
    return order_pb2.Order(
        order_id=order.order_id,
        customer_name=order.customer_name,
        phone=order.phone,
        service_address=order.service_address,
        service_type=to_grpc_service_type(order.service_type),
        appointment_time=order.appointment_time.isoformat(),
        estimated_duration_minutes=order.estimated_duration_minutes,
        status=to_grpc_order_status(order.status),
        assigned_worker_id=order.assigned_worker_id or "",
        status_updated_at=order.status_updated_at.isoformat(),
        created_at=order.created_at.isoformat(),
        updated_at=order.updated_at.isoformat(),
    )


def to_grpc_service_type(service_type: ServiceType) -> order_pb2.ServiceType:
    mapping = {
        ServiceType.CLEANING: order_pb2.SERVICE_TYPE_CLEANING,
        ServiceType.REPAIR: order_pb2.SERVICE_TYPE_REPAIR,
        ServiceType.INSTALL: order_pb2.SERVICE_TYPE_INSTALL,
        ServiceType.OTHER: order_pb2.SERVICE_TYPE_OTHER,
    }
    return mapping[service_type]


def to_domain_service_type(service_type: order_pb2.ServiceType) -> ServiceType:
    mapping = {
        order_pb2.SERVICE_TYPE_CLEANING: ServiceType.CLEANING,
        order_pb2.SERVICE_TYPE_REPAIR: ServiceType.REPAIR,
        order_pb2.SERVICE_TYPE_INSTALL: ServiceType.INSTALL,
        order_pb2.SERVICE_TYPE_OTHER: ServiceType.OTHER,
    }
    if service_type not in mapping:
        raise ValidationError("service_type is required")
    return mapping[service_type]


def to_grpc_order_status(status: OrderStatus) -> order_pb2.OrderStatus:
    mapping = {
        OrderStatus.CREATED: order_pb2.ORDER_STATUS_CREATED,
        OrderStatus.PENDING: order_pb2.ORDER_STATUS_PENDING,
        OrderStatus.ACCEPT: order_pb2.ORDER_STATUS_ACCEPT,
        OrderStatus.COMPLETE: order_pb2.ORDER_STATUS_COMPLETE,
        OrderStatus.PAID: order_pb2.ORDER_STATUS_PAID,
    }
    return mapping[status]


def to_domain_order_status(status: order_pb2.OrderStatus) -> OrderStatus:
    mapping = {
        order_pb2.ORDER_STATUS_CREATED: OrderStatus.CREATED,
        order_pb2.ORDER_STATUS_PENDING: OrderStatus.PENDING,
        order_pb2.ORDER_STATUS_ACCEPT: OrderStatus.ACCEPT,
        order_pb2.ORDER_STATUS_COMPLETE: OrderStatus.COMPLETE,
        order_pb2.ORDER_STATUS_PAID: OrderStatus.PAID,
    }
    if status not in mapping:
        raise ValidationError("target_status is required")
    return mapping[status]
