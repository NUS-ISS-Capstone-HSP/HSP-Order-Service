import pytest

from hsp_order_service.domain.errors import NotFoundError, TransitionError, ValidationError
from hsp_order_service.domain.models import OrderStatus, ServiceType
from hsp_order_service.repository.in_memory import InMemoryOrderRepository
from hsp_order_service.service.order_service import OrderService


def build_service() -> OrderService:
    return OrderService(InMemoryOrderRepository())


@pytest.mark.asyncio
async def test_create_order_success() -> None:
    svc = build_service()
    order = await svc.create_order(
        customer_name="张三",
        phone="13800000000",
        service_address="上海市",
        service_type=ServiceType.CLEANING,
        appointment_time="2026-04-08T10:00:00+08:00",
        estimated_duration_minutes=120,
    )

    assert order.order_id
    assert order.customer_name == "张三"
    assert order.service_type == ServiceType.CLEANING
    assert order.status == OrderStatus.CREATED


@pytest.mark.asyncio
async def test_create_order_empty_name_raises() -> None:
    svc = build_service()
    with pytest.raises(ValidationError):
        await svc.create_order("  ", "138", "addr", ServiceType.OTHER, "time", 60)


@pytest.mark.asyncio
async def test_create_order_invalid_duration_raises() -> None:
    svc = build_service()
    with pytest.raises(ValidationError):
        await svc.create_order("name", "138", "addr", ServiceType.OTHER, "time", 0)


@pytest.mark.asyncio
async def test_get_order_success() -> None:
    svc = build_service()
    created = await svc.create_order("name", "138", "addr", ServiceType.REPAIR, "t", 30)
    fetched = await svc.get_order(created.order_id)
    assert fetched.order_id == created.order_id


@pytest.mark.asyncio
async def test_get_order_not_found_raises() -> None:
    svc = build_service()
    with pytest.raises(NotFoundError):
        await svc.get_order("nonexistent")


@pytest.mark.asyncio
async def test_list_orders_with_filters() -> None:
    svc = build_service()
    await svc.create_order("Alice", "1", "a", ServiceType.CLEANING, "t", 30)
    await svc.create_order("Bob", "2", "b", ServiceType.REPAIR, "t", 30)

    items, total = await svc.list_orders(service_type=ServiceType.CLEANING)
    assert total == 1
    assert items[0].customer_name == "Alice"

    items, total = await svc.list_orders(customer_name="Bob")
    assert total == 1
    assert items[0].phone == "2"


@pytest.mark.asyncio
async def test_list_orders_pagination() -> None:
    svc = build_service()
    await svc.create_order("a", "1", "a", ServiceType.OTHER, "t", 30)
    await svc.create_order("b", "2", "b", ServiceType.OTHER, "t", 30)
    await svc.create_order("c", "3", "c", ServiceType.OTHER, "t", 30)

    items, total = await svc.list_orders(page=1, page_size=2)
    assert total == 3
    assert len(items) == 2


@pytest.mark.asyncio
async def test_update_order_status_success() -> None:
    svc = build_service()
    created = await svc.create_order("name", "138", "addr", ServiceType.OTHER, "t", 30)

    # CREATED -> PENDING
    updated = await svc.update_order_status(created.order_id, OrderStatus.PENDING)
    assert updated.status == OrderStatus.PENDING

    # PENDING -> ACCEPT
    updated = await svc.update_order_status(created.order_id, OrderStatus.ACCEPT, "w1")
    assert updated.status == OrderStatus.ACCEPT
    assert updated.assigned_worker_id == "w1"


@pytest.mark.asyncio
async def test_update_order_status_invalid_transition_raises() -> None:
    svc = build_service()
    created = await svc.create_order("name", "138", "addr", ServiceType.OTHER, "t", 30)

    with pytest.raises(TransitionError):
        await svc.update_order_status(created.order_id, OrderStatus.COMPLETE)
