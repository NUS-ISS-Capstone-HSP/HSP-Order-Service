from datetime import UTC, datetime
from uuid import uuid4

from hsp_order_service.domain.models import Order, OrderListFilters, OrderStatus, ServiceType
from hsp_order_service.repository.interfaces import OrderRepository


class InMemoryOrderRepository(OrderRepository):
    def __init__(self) -> None:
        self._store: dict[str, Order] = {}

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
        now = datetime.now(UTC)
        record = Order(
            order_id=str(uuid4()),
            customer_name=customer_name,
            phone=phone,
            service_address=service_address,
            service_type=service_type,
            appointment_time=appointment_time,
            estimated_duration_minutes=estimated_duration_minutes,
            status=OrderStatus.CREATED,
            assigned_worker_id=None,
            status_updated_at=now,
            created_at=now,
            updated_at=now,
        )
        self._store[record.order_id] = record
        return record

    async def get_by_id(self, order_id: str) -> Order | None:
        return self._store.get(order_id)

    async def list(
        self,
        *,
        filters: OrderListFilters,
        page: int,
        page_size: int,
    ) -> tuple[list[Order], int]:
        records = list(self._store.values())

        if filters.customer_name:
            keyword = filters.customer_name.lower()
            records = [item for item in records if keyword in item.customer_name.lower()]
        if filters.service_type:
            records = [item for item in records if item.service_type == filters.service_type]
        if filters.status:
            records = [item for item in records if item.status == filters.status]

        records.sort(key=lambda item: item.created_at, reverse=True)

        total = len(records)
        start = (page - 1) * page_size
        end = start + page_size
        return records[start:end], total

    async def update_status(
        self,
        *,
        order_id: str,
        target_status: OrderStatus,
        assigned_worker_id: str | None,
        status_updated_at: datetime,
    ) -> Order | None:
        record = self._store.get(order_id)
        if record is None:
            return None

        updated = Order(
            order_id=record.order_id,
            customer_name=record.customer_name,
            phone=record.phone,
            service_address=record.service_address,
            service_type=record.service_type,
            appointment_time=record.appointment_time,
            estimated_duration_minutes=record.estimated_duration_minutes,
            status=target_status,
            assigned_worker_id=assigned_worker_id,
            status_updated_at=status_updated_at,
            created_at=record.created_at,
            updated_at=status_updated_at,
        )
        self._store[order_id] = updated
        return updated
