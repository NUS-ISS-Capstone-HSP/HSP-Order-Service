from datetime import datetime
from typing import Protocol

from hsp_order_service.domain.models import (
    EchoRecord,
    Order,
    OrderListFilters,
    OrderStatus,
    ServiceType,
    SourceType,
)


class EchoRepository(Protocol):
    async def create(self, message: str, source: SourceType) -> EchoRecord:
        ...

    async def get_by_id(self, record_id: str) -> EchoRecord | None:
        ...


class OrderRepository(Protocol):
    async def create(
        self,
        *,
        customer_name: str,
        phone: str,
        service_address: str,
        service_type: ServiceType,
        appointment_time: datetime,
        estimated_duration_minutes: int,
    ) -> Order:
        ...

    async def get_by_id(self, order_id: str) -> Order | None:
        ...

    async def list(
        self,
        *,
        filters: OrderListFilters,
        page: int,
        page_size: int,
    ) -> tuple[list[Order], int]:
        ...

    async def update_status(
        self,
        *,
        order_id: str,
        target_status: OrderStatus,
        assigned_worker_id: str | None,
        status_updated_at: datetime,
    ) -> Order | None:
        ...
