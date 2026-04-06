from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class SourceType(StrEnum):
    HTTP = "HTTP"
    GRPC = "GRPC"


class ServiceType(StrEnum):
    CLEANING = "cleaning"
    REPAIR = "repair"
    INSTALL = "install"
    OTHER = "other"


class OrderStatus(StrEnum):
    CREATED = "created"
    PENDING = "pending"
    ACCEPT = "accept"
    COMPLETE = "complete"
    PAID = "paid"


ORDER_STATUS_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.CREATED: {OrderStatus.PENDING},
    OrderStatus.PENDING: {OrderStatus.ACCEPT},
    OrderStatus.ACCEPT: {OrderStatus.COMPLETE},
    OrderStatus.COMPLETE: {OrderStatus.PAID},
    OrderStatus.PAID: set(),
}


@dataclass(slots=True)
class EchoRecord:
    id: str
    message: str
    source: SourceType
    created_at: datetime


@dataclass(slots=True)
class Order:
    order_id: str
    customer_name: str
    phone: str
    service_address: str
    service_type: ServiceType
    appointment_time: datetime
    estimated_duration_minutes: int
    status: OrderStatus
    assigned_worker_id: str | None
    status_updated_at: datetime
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class OrderListFilters:
    customer_name: str | None = None
    service_type: ServiceType | None = None
    status: OrderStatus | None = None


def can_transition_order_status(current: OrderStatus, target: OrderStatus) -> bool:
    return target in ORDER_STATUS_TRANSITIONS[current]
