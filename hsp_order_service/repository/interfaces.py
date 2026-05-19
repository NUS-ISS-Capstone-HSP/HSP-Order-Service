from typing import Protocol

from hsp_order_service.domain.models import (
    EchoRecord,
    Order,
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
    async def create(self, order: Order) -> Order:
        ...

    async def get_by_id(self, order_id: str) -> Order | None:
        ...

    async def list_orders(
        self,
        customer_name: str = "",
        service_type: ServiceType | None = None,
        status: OrderStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Order], int]:
        ...

    async def update(self, order: Order) -> Order:
        ...
