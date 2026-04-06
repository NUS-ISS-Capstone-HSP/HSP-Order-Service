from hsp_order_service.domain.models import EchoRecord, Order
from hsp_order_service.transport.http.schemas import EchoRecordResponse, OrderResponse


def to_http_response(record: EchoRecord) -> EchoRecordResponse:
    return EchoRecordResponse(
        id=record.id,
        message=record.message,
        source=record.source.value,
        created_at=record.created_at.isoformat(),
    )


def to_http_order_response(order: Order) -> OrderResponse:
    return OrderResponse(
        order_id=order.order_id,
        customer_name=order.customer_name,
        phone=order.phone,
        service_address=order.service_address,
        service_type=order.service_type.value,
        appointment_time=order.appointment_time.isoformat(),
        estimated_duration_minutes=order.estimated_duration_minutes,
        status=order.status.value,
        assigned_worker_id=order.assigned_worker_id,
        status_updated_at=order.status_updated_at.isoformat(),
        created_at=order.created_at.isoformat(),
        updated_at=order.updated_at.isoformat(),
    )
