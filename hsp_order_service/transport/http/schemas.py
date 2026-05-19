from pydantic import BaseModel, ConfigDict, Field


class CreateEchoRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"message": "Hello from HTTP"}},
    )
    message: str = Field(
        min_length=1, max_length=2048, description="Message content."
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
    id: str
    message: str
    source: str
    created_at: str


# ── Order schemas ──

class CreateOrderRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "customer_name": "张三",
                "phone": "13800000000",
                "service_address": "上海市浦东新区XX路100号",
                "service_type": "CLEANING",
                "appointment_time": "2026-04-08T10:00:00+08:00",
                "estimated_duration_minutes": 120,
            }
        },
    )
    customer_name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=1, max_length=20)
    service_address: str = Field(min_length=1, max_length=500)
    service_type: str = Field(description="CLEANING | REPAIR | INSTALL | OTHER")
    appointment_time: str
    estimated_duration_minutes: int = Field(gt=0)


class OrderResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "order_id": "uuid-xxxx",
                "customer_name": "张三",
                "phone": "13800000000",
                "service_address": "上海市浦东新区XX路100号",
                "service_type": "CLEANING",
                "appointment_time": "2026-04-08T10:00:00+08:00",
                "estimated_duration_minutes": 120,
                "status": "CREATED",
                "assigned_worker_id": "",
                "status_updated_at": None,
                "created_at": "2026-04-01T10:00:00+00:00",
                "updated_at": "2026-04-01T10:00:00+00:00",
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
    assigned_worker_id: str = ""
    status_updated_at: str | None = None
    created_at: str
    updated_at: str


class ListOrdersResponse(BaseModel):
    items: list[OrderResponse]
    page: int
    page_size: int
    total: int


class UpdateOrderStatusRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "target_status": "ACCEPT",
                "assigned_worker_id": "worker-1001",
            }
        },
    )
    target_status: str = Field(description="PENDING | ACCEPT | COMPLETE | PAID")
    assigned_worker_id: str = ""
