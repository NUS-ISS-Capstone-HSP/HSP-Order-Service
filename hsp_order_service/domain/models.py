from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class SourceType(StrEnum):
    HTTP = "HTTP"
    GRPC = "GRPC"


class ServiceType(StrEnum):
    CLEANING = "CLEANING"
    REPAIR = "REPAIR"
    INSTALL = "INSTALL"
    OTHER = "OTHER"


class OrderStatus(StrEnum):
    CREATED = "CREATED"
    PENDING = "PENDING"
    ACCEPT = "ACCEPT"
    COMPLETE = "COMPLETE"
    PAID = "PAID"


VALID_TRANSITIONS: dict[OrderStatus, list[OrderStatus]] = {
    OrderStatus.CREATED: [OrderStatus.PENDING],
    OrderStatus.PENDING: [OrderStatus.ACCEPT],
    OrderStatus.ACCEPT: [OrderStatus.COMPLETE],
    OrderStatus.COMPLETE: [OrderStatus.PAID],
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
    appointment_time: str
    estimated_duration_minutes: int
    status: OrderStatus = OrderStatus.CREATED
    assigned_worker_id: str = ""
    status_updated_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def can_transition_to(self, target: OrderStatus) -> bool:
        return target in VALID_TRANSITIONS.get(self.status, [])
