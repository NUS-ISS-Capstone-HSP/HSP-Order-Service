from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from hsp_order_service.domain.models import Order, OrderListFilters, OrderStatus, ServiceType
from hsp_order_service.infrastructure.orm import OrderORM
from hsp_order_service.repository.interfaces import OrderRepository


class SQLAlchemyOrderRepository(OrderRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

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
        row = OrderORM(
            order_id=str(uuid4()),
            customer_name=customer_name,
            phone=phone,
            service_address=service_address,
            service_type=service_type.value,
            appointment_time=appointment_time,
            estimated_duration_minutes=estimated_duration_minutes,
            status=OrderStatus.CREATED.value,
            assigned_worker_id=None,
            status_updated_at=now,
            created_at=now,
            updated_at=now,
        )
        async with self._session_factory() as session:
            session.add(row)
            await session.commit()
            await session.refresh(row)
        return _to_domain(row)

    async def get_by_id(self, order_id: str) -> Order | None:
        async with self._session_factory() as session:
            stmt = select(OrderORM).where(OrderORM.order_id == order_id)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
        if row is None:
            return None
        return _to_domain(row)

    async def list(
        self,
        *,
        filters: OrderListFilters,
        page: int,
        page_size: int,
    ) -> tuple[list[Order], int]:
        offset = (page - 1) * page_size

        async with self._session_factory() as session:
            stmt = select(OrderORM)
            stmt = _apply_filters(stmt, filters)
            stmt = stmt.order_by(OrderORM.created_at.desc()).offset(offset).limit(page_size)

            result = await session.execute(stmt)
            rows = result.scalars().all()

            count_stmt = select(func.count()).select_from(OrderORM)
            count_stmt = _apply_filters(count_stmt, filters)
            count_result = await session.execute(count_stmt)
            total = int(count_result.scalar_one())

        return [_to_domain(row) for row in rows], total

    async def update_status(
        self,
        *,
        order_id: str,
        target_status: OrderStatus,
        assigned_worker_id: str | None,
        status_updated_at: datetime,
    ) -> Order | None:
        async with self._session_factory() as session:
            stmt = select(OrderORM).where(OrderORM.order_id == order_id)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if row is None:
                return None

            row.status = target_status.value
            row.assigned_worker_id = assigned_worker_id
            row.status_updated_at = status_updated_at
            row.updated_at = status_updated_at

            await session.commit()
            await session.refresh(row)
            return _to_domain(row)


def _apply_filters(stmt, filters: OrderListFilters):
    if filters.customer_name:
        stmt = stmt.where(OrderORM.customer_name.like(f"%{filters.customer_name}%"))
    if filters.service_type:
        stmt = stmt.where(OrderORM.service_type == filters.service_type.value)
    if filters.status:
        stmt = stmt.where(OrderORM.status == filters.status.value)
    return stmt


def _to_domain(row: OrderORM) -> Order:
    return Order(
        order_id=row.order_id,
        customer_name=row.customer_name,
        phone=row.phone,
        service_address=row.service_address,
        service_type=ServiceType(row.service_type),
        appointment_time=_ensure_tz(row.appointment_time),
        estimated_duration_minutes=row.estimated_duration_minutes,
        status=OrderStatus(row.status),
        assigned_worker_id=row.assigned_worker_id,
        status_updated_at=_ensure_tz(row.status_updated_at),
        created_at=_ensure_tz(row.created_at),
        updated_at=_ensure_tz(row.updated_at),
    )


def _ensure_tz(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value
