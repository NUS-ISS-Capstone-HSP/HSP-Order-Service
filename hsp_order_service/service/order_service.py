import re
from datetime import UTC, datetime

from hsp_order_service.domain.errors import ConflictError, NotFoundError, ValidationError
from hsp_order_service.domain.models import (
    Order,
    OrderListFilters,
    OrderStatus,
    ServiceType,
    can_transition_order_status,
)
from hsp_order_service.repository.interfaces import OrderRepository

PHONE_PATTERN = re.compile(r"^\+?\d{6,20}$")


class OrderService:
    def __init__(self, repository: OrderRepository) -> None:
        self._repository = repository

    async def create_order(
        self,
        *,
        customer_name: str,
        phone: str,
        service_address: str,
        service_type: ServiceType,
        appointment_time: datetime,
        estimated_duration_minutes: int,
    ) -> Order:
        normalized_customer_name = customer_name.strip()
        if not normalized_customer_name:
            raise ValidationError("customer_name must not be empty")
        if len(normalized_customer_name) > 100:
            raise ValidationError("customer_name must be at most 100 characters")

        normalized_phone = phone.strip()
        if not normalized_phone:
            raise ValidationError("phone must not be empty")
        if not PHONE_PATTERN.fullmatch(normalized_phone):
            raise ValidationError("phone format is invalid")

        normalized_service_address = service_address.strip()
        if not normalized_service_address:
            raise ValidationError("service_address must not be empty")
        if len(normalized_service_address) > 255:
            raise ValidationError("service_address must be at most 255 characters")

        if appointment_time.tzinfo is None:
            raise ValidationError("appointment_time must include timezone")

        if estimated_duration_minutes <= 0:
            raise ValidationError("estimated_duration_minutes must be greater than 0")

        return await self._repository.create(
            customer_name=normalized_customer_name,
            phone=normalized_phone,
            service_address=normalized_service_address,
            service_type=service_type,
            appointment_time=appointment_time,
            estimated_duration_minutes=estimated_duration_minutes,
        )

    async def get_order(self, order_id: str) -> Order:
        normalized_order_id = order_id.strip()
        if not normalized_order_id:
            raise ValidationError("order_id must not be empty")

        order = await self._repository.get_by_id(normalized_order_id)
        if order is None:
            raise NotFoundError(f"order '{normalized_order_id}' not found")
        return order

    async def list_orders(
        self,
        *,
        customer_name: str | None,
        service_type: ServiceType | None,
        status: OrderStatus | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Order], int]:
        if page < 1:
            raise ValidationError("page must be greater than or equal to 1")
        if page_size < 1 or page_size > 100:
            raise ValidationError("page_size must be between 1 and 100")

        normalized_customer_name = None
        if customer_name is not None:
            candidate = customer_name.strip()
            if candidate:
                normalized_customer_name = candidate

        filters = OrderListFilters(
            customer_name=normalized_customer_name,
            service_type=service_type,
            status=status,
        )
        return await self._repository.list(filters=filters, page=page, page_size=page_size)

    async def update_order_status(
        self,
        *,
        order_id: str,
        target_status: OrderStatus,
        assigned_worker_id: str | None,
    ) -> Order:
        order = await self.get_order(order_id)

        if not can_transition_order_status(order.status, target_status):
            raise ConflictError(
                f"invalid status transition: {order.status.value} -> {target_status.value}",
            )

        normalized_worker_id = None
        if assigned_worker_id is not None:
            candidate = assigned_worker_id.strip()
            if candidate:
                normalized_worker_id = candidate

        next_worker_id = order.assigned_worker_id
        if target_status is OrderStatus.PENDING:
            if normalized_worker_id is None:
                raise ValidationError(
                    "assigned_worker_id is required when target_status is pending",
                )
            next_worker_id = normalized_worker_id

        updated = await self._repository.update_status(
            order_id=order.order_id,
            target_status=target_status,
            assigned_worker_id=next_worker_id,
            status_updated_at=datetime.now(UTC),
        )
        if updated is None:
            raise NotFoundError(f"order '{order.order_id}' not found")
        return updated
