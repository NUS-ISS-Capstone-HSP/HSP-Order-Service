from datetime import UTC, datetime
from uuid import uuid4

from hsp_order_service.domain.errors import NotFoundError, TransitionError, ValidationError
from hsp_order_service.domain.models import Order, OrderStatus, ServiceType
from hsp_order_service.repository.interfaces import OrderRepository


class OrderService:
    def __init__(self, repository: OrderRepository) -> None:
        self._repository = repository

    async def create_order(
        self,
        customer_name: str,
        phone: str,
        service_address: str,
        service_type: ServiceType,
        appointment_time: str,
        estimated_duration_minutes: int,
    ) -> Order:
        if not customer_name.strip():
            raise ValidationError("customer_name must not be empty")
        if not phone.strip():
            raise ValidationError("phone must not be empty")
        if not service_address.strip():
            raise ValidationError("service_address must not be empty")
        if estimated_duration_minutes <= 0:
            raise ValidationError("estimated_duration_minutes must be positive")

        order = Order(
            order_id=str(uuid4()),
            customer_name=customer_name.strip(),
            phone=phone.strip(),
            service_address=service_address.strip(),
            service_type=service_type,
            appointment_time=appointment_time,
            estimated_duration_minutes=estimated_duration_minutes,
            status=OrderStatus.CREATED,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        return await self._repository.create(order)

    async def get_order(self, order_id: str) -> Order:
        if not order_id.strip():
            raise ValidationError("order_id must not be empty")
        order = await self._repository.get_by_id(order_id.strip())
        if order is None:
            raise NotFoundError(f"order '{order_id}' not found")
        return order

    async def list_orders(
        self,
        customer_name: str = "",
        service_type: ServiceType | None = None,
        status: OrderStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Order], int]:
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20
        return await self._repository.list_orders(
            customer_name=customer_name,
            service_type=service_type,
            status=status,
            page=page,
            page_size=page_size,
        )

    async def update_order_status(
        self,
        order_id: str,
        target_status: OrderStatus,
        assigned_worker_id: str = "",
    ) -> Order:
        if not order_id.strip():
            raise ValidationError("order_id must not be empty")

        order = await self._repository.get_by_id(order_id.strip())
        if order is None:
            raise NotFoundError(f"order '{order_id}' not found")

        if not order.can_transition_to(target_status):
            raise TransitionError(
                f"cannot transition from {order.status.value} to {target_status.value}"
            )

        order.status = target_status
        order.status_updated_at = datetime.now(UTC)
        order.updated_at = datetime.now(UTC)
        if assigned_worker_id:
            order.assigned_worker_id = assigned_worker_id
        return await self._repository.update(order)
