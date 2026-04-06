from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from hsp_order_service.domain.models import OrderListFilters, OrderStatus, ServiceType
from hsp_order_service.infrastructure.db import (
    create_engine,
    create_session_factory,
    init_db,
)
from hsp_order_service.repository.order_mysql import SQLAlchemyOrderRepository


@pytest.mark.asyncio
async def test_order_repository_create_get_and_update(tmp_path: Path) -> None:
    db_file = tmp_path / "order.db"
    engine = create_engine(f"sqlite+aiosqlite:///{db_file}")
    await init_db(engine)

    repository = SQLAlchemyOrderRepository(create_session_factory(engine))

    created = await repository.create(
        customer_name="Alice",
        phone="13812345678",
        service_address="Shanghai Road 100",
        service_type=ServiceType.CLEANING,
        appointment_time=datetime(2026, 4, 10, 9, 0, tzinfo=UTC),
        estimated_duration_minutes=80,
    )
    fetched = await repository.get_by_id(created.order_id)

    assert fetched is not None
    assert fetched.order_id == created.order_id
    assert fetched.status is OrderStatus.CREATED

    updated = await repository.update_status(
        order_id=created.order_id,
        target_status=OrderStatus.PENDING,
        assigned_worker_id="worker-001",
        status_updated_at=datetime.now(UTC),
    )
    assert updated is not None
    assert updated.status is OrderStatus.PENDING
    assert updated.assigned_worker_id == "worker-001"

    await engine.dispose()


@pytest.mark.asyncio
async def test_order_repository_list_with_filters_and_pagination(tmp_path: Path) -> None:
    db_file = tmp_path / "order_list.db"
    engine = create_engine(f"sqlite+aiosqlite:///{db_file}")
    await init_db(engine)

    repository = SQLAlchemyOrderRepository(create_session_factory(engine))

    await repository.create(
        customer_name="Alice",
        phone="13812345678",
        service_address="Addr 1",
        service_type=ServiceType.CLEANING,
        appointment_time=datetime(2026, 4, 10, 9, 0, tzinfo=UTC),
        estimated_duration_minutes=80,
    )
    second = await repository.create(
        customer_name="Bob",
        phone="13812345679",
        service_address="Addr 2",
        service_type=ServiceType.REPAIR,
        appointment_time=datetime(2026, 4, 11, 9, 0, tzinfo=UTC),
        estimated_duration_minutes=90,
    )

    await repository.update_status(
        order_id=second.order_id,
        target_status=OrderStatus.PENDING,
        assigned_worker_id="worker-002",
        status_updated_at=datetime.now(UTC) + timedelta(minutes=1),
    )

    filtered, total = await repository.list(
        filters=OrderListFilters(status=OrderStatus.PENDING),
        page=1,
        page_size=20,
    )
    page_one, page_one_total = await repository.list(
        filters=OrderListFilters(),
        page=1,
        page_size=1,
    )

    assert total == 1
    assert filtered[0].order_id == second.order_id
    assert page_one_total == 2
    assert len(page_one) == 1
    assert page_one[0].order_id == second.order_id

    await engine.dispose()
