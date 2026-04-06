from datetime import UTC, datetime

import pytest

from hsp_order_service.domain.errors import ConflictError, ValidationError
from hsp_order_service.domain.models import OrderStatus, ServiceType
from hsp_order_service.repository.order_in_memory import InMemoryOrderRepository
from hsp_order_service.service.order_service import OrderService


@pytest.mark.asyncio
async def test_create_order_success() -> None:
    service = OrderService(InMemoryOrderRepository())

    created = await service.create_order(
        customer_name="Alice",
        phone="+8613812345678",
        service_address="Shanghai Road 100",
        service_type=ServiceType.CLEANING,
        appointment_time=datetime(2026, 4, 10, 9, 0, tzinfo=UTC),
        estimated_duration_minutes=90,
    )

    assert created.order_id
    assert created.status is OrderStatus.CREATED
    assert created.service_type is ServiceType.CLEANING


@pytest.mark.asyncio
async def test_create_order_invalid_phone() -> None:
    service = OrderService(InMemoryOrderRepository())

    with pytest.raises(ValidationError):
        await service.create_order(
            customer_name="Alice",
            phone="abc",
            service_address="Shanghai Road 100",
            service_type=ServiceType.CLEANING,
            appointment_time=datetime(2026, 4, 10, 9, 0, tzinfo=UTC),
            estimated_duration_minutes=90,
        )


@pytest.mark.asyncio
async def test_update_order_status_happy_path() -> None:
    service = OrderService(InMemoryOrderRepository())

    created = await service.create_order(
        customer_name="Alice",
        phone="13812345678",
        service_address="Shanghai Road 100",
        service_type=ServiceType.REPAIR,
        appointment_time=datetime(2026, 4, 10, 9, 0, tzinfo=UTC),
        estimated_duration_minutes=60,
    )

    pending = await service.update_order_status(
        order_id=created.order_id,
        target_status=OrderStatus.PENDING,
        assigned_worker_id="worker-001",
    )
    accepted = await service.update_order_status(
        order_id=created.order_id,
        target_status=OrderStatus.ACCEPT,
        assigned_worker_id=None,
    )

    assert pending.status is OrderStatus.PENDING
    assert pending.assigned_worker_id == "worker-001"
    assert accepted.status is OrderStatus.ACCEPT


@pytest.mark.asyncio
async def test_update_order_status_reject_illegal_transition() -> None:
    service = OrderService(InMemoryOrderRepository())

    created = await service.create_order(
        customer_name="Alice",
        phone="13812345678",
        service_address="Shanghai Road 100",
        service_type=ServiceType.REPAIR,
        appointment_time=datetime(2026, 4, 10, 9, 0, tzinfo=UTC),
        estimated_duration_minutes=60,
    )

    with pytest.raises(ConflictError):
        await service.update_order_status(
            order_id=created.order_id,
            target_status=OrderStatus.COMPLETE,
            assigned_worker_id=None,
        )


@pytest.mark.asyncio
async def test_update_order_status_pending_requires_worker() -> None:
    service = OrderService(InMemoryOrderRepository())

    created = await service.create_order(
        customer_name="Alice",
        phone="13812345678",
        service_address="Shanghai Road 100",
        service_type=ServiceType.REPAIR,
        appointment_time=datetime(2026, 4, 10, 9, 0, tzinfo=UTC),
        estimated_duration_minutes=60,
    )

    with pytest.raises(ValidationError):
        await service.update_order_status(
            order_id=created.order_id,
            target_status=OrderStatus.PENDING,
            assigned_worker_id="  ",
        )
