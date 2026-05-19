from datetime import UTC, datetime
from uuid import uuid4

from hsp_order_service.domain.models import (
    EchoRecord,
    Order,
    OrderStatus,
    ServiceType,
    SourceType,
)
from hsp_order_service.repository.interfaces import EchoRepository, OrderRepository


class InMemoryEchoRepository(EchoRepository):
    def __init__(self) -> None:
        self._store: dict[str, EchoRecord] = {}

    async def create(self, message: str, source: SourceType) -> EchoRecord:
        record = EchoRecord(
            id=str(uuid4()),
            message=message,
            source=source,
            created_at=datetime.now(UTC),
        )
        self._store[record.id] = record
        return record

    async def get_by_id(self, record_id: str) -> EchoRecord | None:
        return self._store.get(record_id)


class InMemoryOrderRepository(OrderRepository):
    def __init__(self) -> None:
        self._store: dict[str, Order] = {}

    async def create(self, order: Order) -> Order:
        self._store[order.order_id] = order
        return order

    async def get_by_id(self, order_id: str) -> Order | None:
        return self._store.get(order_id)

    async def list_orders(
        self,
        customer_name: str = "",
        service_type: ServiceType | None = None,
        status: OrderStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Order], int]:
        items = list(self._store.values())
        if customer_name:
            items = [o for o in items if customer_name in o.customer_name]
        if service_type:
            items = [o for o in items if o.service_type == service_type]
        if status:
            items = [o for o in items if o.status == status]
        items.sort(key=lambda o: o.created_at, reverse=True)
        total = len(items)
        start = (page - 1) * page_size
        return items[start : start + page_size], total

    async def update(self, order: Order) -> Order:
        self._store[order.order_id] = order
        return order
