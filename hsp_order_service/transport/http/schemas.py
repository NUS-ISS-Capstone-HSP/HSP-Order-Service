from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from hsp_order_service.domain.models import OrderStatus, ServiceType

OrderTargetStatus = Literal["pending", "accept", "complete", "paid"]


class CreateEchoRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"message": "Hello from HTTP"}},
    )

    message: str = Field(
        min_length=1,
        max_length=2048,
        description="Message content to be stored as an echo record.",
    )


class EchoRecordResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "6f88f9f2-65fd-4ef7-80de-2c96d8ab7b5b",
                "message": "Hello from HTTP",
                "source": "HTTP",
                "created_at": "2026-03-18T12:34:56+00:00",
            }
        },
    )

    id: str = Field(description="Echo record id (UUID).")
    message: str = Field(description="Stored message.")
    source: str = Field(description="Record source. HTTP or GRPC.")
    created_at: str = Field(description="Creation time in ISO-8601 format.")


class CreateOrderRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "customer_name": "Alice Zhang",
                "phone": "+8613812345678",
                "service_address": "Shanghai Pudong XX Road 100",
                "service_type": "cleaning",
                "appointment_time": "2026-04-07T09:30:00+08:00",
                "estimated_duration_minutes": 120,
            }
        },
    )

    customer_name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=1, max_length=32, pattern=r"^\+?\d{6,20}$")
    service_address: str = Field(min_length=1, max_length=255)
    service_type: ServiceType
    appointment_time: datetime
    estimated_duration_minutes: int = Field(gt=0)


class OrderResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "order_id": "f5dd96bf-49cf-4fd5-816d-e13bc86068d2",
                "customer_name": "Alice Zhang",
                "phone": "+8613812345678",
                "service_address": "Shanghai Pudong XX Road 100",
                "service_type": "cleaning",
                "appointment_time": "2026-04-07T09:30:00+08:00",
                "estimated_duration_minutes": 120,
                "status": "created",
                "assigned_worker_id": None,
                "status_updated_at": "2026-04-06T10:00:00+00:00",
                "created_at": "2026-04-06T10:00:00+00:00",
                "updated_at": "2026-04-06T10:00:00+00:00",
            }
        },
    )

    order_id: str
    customer_name: str
    phone: str
    service_address: str
    service_type: str
    appointment_time: str
    estimated_duration_minutes: int
    status: str
    assigned_worker_id: str | None
    status_updated_at: str
    created_at: str
    updated_at: str


class ListOrdersResponse(BaseModel):
    items: list[OrderResponse]
    page: int
    page_size: int
    total: int


class UpdateOrderStatusRequest(BaseModel):
    target_status: OrderTargetStatus
    assigned_worker_id: str | None = Field(default=None, max_length=64)


class ListOrdersQuery(BaseModel):
    customer_name: str | None = None
    service_type: ServiceType | None = None
    status: OrderStatus | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
