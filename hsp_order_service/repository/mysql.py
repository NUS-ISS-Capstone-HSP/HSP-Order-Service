from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from hsp_order_service.domain.models import (
    EchoRecord,
    Order,
    OrderStatus,
    ServiceType,
    SourceType,
)
from hsp_order_service.infrastructure.orm import EchoRecordORM, OrderORM
from hsp_order_service.repository.interfaces import EchoRepository, OrderRepository


class SQLAlchemyEchoRepository(EchoRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(self, message: str, source: SourceType) -> EchoRecord:
        row = EchoRecordORM(
            id=str(uuid4()),
            message=message,
            source=source.value,
        )
        async with self._session_factory() as session:
            session.add(row)
            await session.commit()
            await session.refresh(row)
        return _echo_to_domain(row)

    async def get_by_id(self, record_id: str) -> EchoRecord | None:
        async with self._session_factory() as session:
            stmt = select(EchoRecordORM).where(EchoRecordORM.id == record_id)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
        if row is None:
            return None
        return _echo_to_domain(row)


class SQLAlchemyOrderRepository(OrderRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(self, order: Order) -> Order:
        row = OrderORM(
            order_id=order.order_id,
            customer_name=order.customer_name,
            phone=order.phone,
            service_address=order.service_address,
            service_type=order.service_type.value,
            appointment_time=order.appointment_time,
            estimated_duration_minutes=order.estimated_duration_minutes,
            status=order.status.value,
            assigned_worker_id=order.assigned_worker_id or None,
            status_updated_at=order.status_updated_at,
        )
        async with self._session_factory() as session:
            session.add(row)
            await session.commit()
            await session.refresh(row)
        return _order_to_domain(row)

    async def get_by_id(self, order_id: str) -> Order | None:
        async with self._session_factory() as session:
            stmt = select(OrderORM).where(OrderORM.order_id == order_id)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
        if row is None:
            return None
        return _order_to_domain(row)

    async def list_orders(
        self,
        customer_name: str = "",
        service_type: ServiceType | None = None,
        status: OrderStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Order], int]:
        async with self._session_factory() as session:
            q = select(OrderORM)
            count_q = select(func.count(OrderORM.order_id))

            if customer_name:
                q = q.where(OrderORM.customer_name.contains(customer_name))
                count_q = count_q.where(OrderORM.customer_name.contains(customer_name))
            if service_type:
                q = q.where(OrderORM.service_type == service_type.value)
                count_q = count_q.where(OrderORM.service_type == service_type.value)
            if status:
                q = q.where(OrderORM.status == status.value)
                count_q = count_q.where(OrderORM.status == status.value)

            total_result = await session.execute(count_q)
            total = total_result.scalar() or 0

            q = q.order_by(OrderORM.created_at.desc())
            q = q.offset((page - 1) * page_size).limit(page_size)
            result = await session.execute(q)
            rows = result.scalars().all()
            return [_order_to_domain(r) for r in rows], total

    async def update(self, order: Order) -> Order:
        async with self._session_factory() as session:
            stmt = select(OrderORM).where(OrderORM.order_id == order.order_id)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if row is None:
                # fallback: insert if not found
                return await self.create(order)
            row.customer_name = order.customer_name
            row.phone = order.phone
            row.service_address = order.service_address
            row.service_type = order.service_type.value
            row.appointment_time = order.appointment_time
            row.estimated_duration_minutes = order.estimated_duration_minutes
            row.status = order.status.value
            row.assigned_worker_id = order.assigned_worker_id or None
            row.status_updated_at = order.status_updated_at
            row.updated_at = datetime.now(UTC)
            await session.commit()
            await session.refresh(row)
        return _order_to_domain(row)


def _echo_to_domain(row: EchoRecordORM) -> EchoRecord:
    created_at = row.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    return EchoRecord(
        id=row.id,
        message=row.message,
        source=SourceType(row.source),
        created_at=created_at,
    )


def _order_to_domain(row: OrderORM) -> Order:
    created_at = row.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    updated_at = row.updated_at
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=UTC)
    status_updated_at = row.status_updated_at
    if status_updated_at and status_updated_at.tzinfo is None:
        status_updated_at = status_updated_at.replace(tzinfo=UTC)
    return Order(
        order_id=row.order_id,
        customer_name=row.customer_name,
        phone=row.phone,
        service_address=row.service_address,
        service_type=ServiceType(row.service_type),
        appointment_time=row.appointment_time,
        estimated_duration_minutes=row.estimated_duration_minutes,
        status=OrderStatus(row.status),
        assigned_worker_id=row.assigned_worker_id or "",
        status_updated_at=status_updated_at,
        created_at=created_at,
        updated_at=updated_at,
    )
