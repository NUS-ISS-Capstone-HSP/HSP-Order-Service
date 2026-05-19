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


_PROTO_SERVICE_TYPE: dict[ServiceType, int] = {
    ServiceType.CLEANING: order_pb2.SERVICE_TYPE_CLEANING,
    ServiceType.REPAIR: order_pb2.SERVICE_TYPE_REPAIR,
    ServiceType.INSTALL: order_pb2.SERVICE_TYPE_INSTALL,
    ServiceType.OTHER: order_pb2.SERVICE_TYPE_OTHER,
}

_PROTO_STATUS: dict[OrderStatus, int] = {
    OrderStatus.CREATED: order_pb2.ORDER_STATUS_CREATED,
    OrderStatus.PENDING: order_pb2.ORDER_STATUS_PENDING,
    OrderStatus.ACCEPT: order_pb2.ORDER_STATUS_ACCEPT,
    OrderStatus.COMPLETE: order_pb2.ORDER_STATUS_COMPLETE,
    OrderStatus.PAID: order_pb2.ORDER_STATUS_PAID,
}

_SERVICE_TYPE_REVERSE: dict[int, ServiceType] = {
    order_pb2.SERVICE_TYPE_CLEANING: ServiceType.CLEANING,
    order_pb2.SERVICE_TYPE_REPAIR: ServiceType.REPAIR,
    order_pb2.SERVICE_TYPE_INSTALL: ServiceType.INSTALL,
    order_pb2.SERVICE_TYPE_OTHER: ServiceType.OTHER,
}

_STATUS_REVERSE: dict[int, OrderStatus] = {
    order_pb2.ORDER_STATUS_CREATED: OrderStatus.CREATED,
    order_pb2.ORDER_STATUS_PENDING: OrderStatus.PENDING,
    order_pb2.ORDER_STATUS_ACCEPT: OrderStatus.ACCEPT,
    order_pb2.ORDER_STATUS_COMPLETE: OrderStatus.COMPLETE,
    order_pb2.ORDER_STATUS_PAID: OrderStatus.PAID,
}


def to_grpc_order(order: Order) -> order_pb2.Order:
    return order_pb2.Order(
        order_id=order.order_id,
        customer_name=order.customer_name,
        phone=order.phone,
        service_address=order.service_address,
        service_type=_PROTO_SERVICE_TYPE.get(order.service_type, 0),
        appointment_time=order.appointment_time,
        estimated_duration_minutes=order.estimated_duration_minutes,
        status=_PROTO_STATUS.get(order.status, 0),
        assigned_worker_id=order.assigned_worker_id,
        status_updated_at=order.status_updated_at.isoformat() if order.status_updated_at else "",
        created_at=order.created_at.isoformat(),
        updated_at=order.updated_at.isoformat(),
    )


def service_type_from_proto(proto_val: int) -> ServiceType:
    return _SERVICE_TYPE_REVERSE.get(proto_val, ServiceType.OTHER)


def order_status_from_proto(proto_val: int) -> OrderStatus | None:
    if proto_val == order_pb2.ORDER_STATUS_UNSPECIFIED:
        return None
    return _STATUS_REVERSE.get(proto_val)
