from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from hsp_order_service.domain.models import Order, OrderStatus, ServiceType, SourceType
from hsp_order_service.infrastructure.db import (
    create_engine,
    create_session_factory,
    init_db,
)
from hsp_order_service.repository.mysql import SQLAlchemyEchoRepository, SQLAlchemyOrderRepository


async def build_order_repository(tmp_path: Path) -> tuple[SQLAlchemyOrderRepository, AsyncEngine]:
    db_file = tmp_path / "orders.db"
    engine = create_engine(f"sqlite+aiosqlite:///{db_file}")
    await init_db(engine)
    return SQLAlchemyOrderRepository(create_session_factory(engine)), engine


def build_order(order_id: str, customer_name: str = "Alice") -> Order:
    return Order(
        order_id=order_id,
        customer_name=customer_name,
        phone="13800000000",
        service_address="Shanghai",
        service_type=ServiceType.CLEANING,
        appointment_time="2026-04-08T10:00:00+08:00",
        estimated_duration_minutes=60,
    )


@pytest.mark.asyncio
async def test_sqlalchemy_repository_create_and_get(tmp_path: Path) -> None:
    db_file = tmp_path / "echo.db"
    engine = create_engine(f"sqlite+aiosqlite:///{db_file}")
    await init_db(engine)

    repository = SQLAlchemyEchoRepository(create_session_factory(engine))

    created = await repository.create("repo-message", SourceType.GRPC)
    fetched = await repository.get_by_id(created.id)

    assert created.message == "repo-message"
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.source == SourceType.GRPC

    await engine.dispose()


@pytest.mark.asyncio
async def test_sqlalchemy_repository_get_missing_returns_none(tmp_path: Path) -> None:
    db_file = tmp_path / "echo.db"
    engine = create_engine(f"sqlite+aiosqlite:///{db_file}")
    await init_db(engine)

    repository = SQLAlchemyEchoRepository(create_session_factory(engine))

    fetched = await repository.get_by_id("missing-id")
    assert fetched is None

    await engine.dispose()


@pytest.mark.asyncio
async def test_sqlalchemy_order_repository_create_and_get(tmp_path: Path) -> None:
    repository, engine = await build_order_repository(tmp_path)

    created = await repository.create(build_order("order-1"))
    fetched = await repository.get_by_id("order-1")

    assert created.order_id == "order-1"
    assert fetched is not None
    assert fetched.customer_name == "Alice"
    assert fetched.service_type == ServiceType.CLEANING
    assert fetched.status == OrderStatus.CREATED
    assert fetched.assigned_worker_id == ""

    await engine.dispose()


@pytest.mark.asyncio
async def test_sqlalchemy_order_repository_list_filters_and_paginates(tmp_path: Path) -> None:
    repository, engine = await build_order_repository(tmp_path)
    first = build_order("order-1", customer_name="Alice")
    second = build_order("order-2", customer_name="Bob")
    second.service_type = ServiceType.REPAIR
    second.status = OrderStatus.PENDING

    await repository.create(first)
    await repository.create(second)

    items, total = await repository.list_orders(service_type=ServiceType.REPAIR)
    assert total == 1
    assert items[0].order_id == "order-2"

    items, total = await repository.list_orders(customer_name="Ali", page=1, page_size=1)
    assert total == 1
    assert len(items) == 1
    assert items[0].order_id == "order-1"

    items, total = await repository.list_orders(status=OrderStatus.PENDING)
    assert total == 1
    assert items[0].status == OrderStatus.PENDING

    await engine.dispose()


@pytest.mark.asyncio
async def test_sqlalchemy_order_repository_update_existing_order(tmp_path: Path) -> None:
    repository, engine = await build_order_repository(tmp_path)
    order = await repository.create(build_order("order-1"))

    order.status = OrderStatus.PENDING
    order.assigned_worker_id = "worker-1"
    updated = await repository.update(order)
    fetched = await repository.get_by_id("order-1")

    assert updated.status == OrderStatus.PENDING
    assert updated.assigned_worker_id == "worker-1"
    assert fetched is not None
    assert fetched.status == OrderStatus.PENDING

    await engine.dispose()


@pytest.mark.asyncio
async def test_sqlalchemy_order_repository_get_missing_returns_none(tmp_path: Path) -> None:
    repository, engine = await build_order_repository(tmp_path)

    fetched = await repository.get_by_id("missing-id")

    assert fetched is None

    await engine.dispose()
