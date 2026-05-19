from fastapi.testclient import TestClient

from hsp_order_service.repository.in_memory import (
    InMemoryEchoRepository,
    InMemoryOrderRepository,
)
from hsp_order_service.service.echo_service import EchoService
from hsp_order_service.service.order_service import OrderService
from hsp_order_service.transport.http.app import create_http_app


def build_client() -> TestClient:
    echo_service = EchoService(InMemoryEchoRepository())
    order_service = OrderService(InMemoryOrderRepository())
    app = create_http_app(echo_service, order_service)
    return TestClient(app)


def test_create_order_http_success() -> None:
    client = build_client()
    response = client.post(
        "/api/orders/v1/orders",
        json={
            "customer_name": "李四",
            "phone": "13900000000",
            "service_address": "北京市",
            "service_type": "REPAIR",
            "appointment_time": "2026-04-10T14:00:00+08:00",
            "estimated_duration_minutes": 90,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["customer_name"] == "李四"
    assert data["service_type"] == "REPAIR"
    assert data["status"] == "CREATED"


def test_create_order_http_validation_error_returns_400() -> None:
    client = build_client()
    response = client.post(
        "/api/orders/v1/orders",
        json={
            "customer_name": "",
            "phone": "139",
            "service_address": "addr",
            "service_type": "OTHER",
            "appointment_time": "t",
            "estimated_duration_minutes": 0,
        },
    )

    assert response.status_code == 422


def test_get_order_http_success() -> None:
    client = build_client()
    created = client.post(
        "/api/orders/v1/orders",
        json={
            "customer_name": "test",
            "phone": "1",
            "service_address": "a",
            "service_type": "OTHER",
            "appointment_time": "t",
            "estimated_duration_minutes": 10,
        },
    ).json()

    response = client.get(f"/api/orders/v1/orders/{created['order_id']}")

    assert response.status_code == 200
    assert response.json()["order_id"] == created["order_id"]


def test_get_order_http_not_found_returns_404() -> None:
    client = build_client()
    response = client.get("/api/orders/v1/orders/nonexistent")
    assert response.status_code == 404


def test_list_orders_http_success() -> None:
    client = build_client()
    client.post(
        "/api/orders/v1/orders",
        json={
            "customer_name": "list-test",
            "phone": "1",
            "service_address": "a",
            "service_type": "CLEANING",
            "appointment_time": "t",
            "estimated_duration_minutes": 10,
        },
    )

    response = client.get("/api/orders/v1/orders?page=1&page_size=10")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


def test_update_order_status_http_success() -> None:
    client = build_client()
    created = client.post(
        "/api/orders/v1/orders",
        json={
            "customer_name": "status-test",
            "phone": "1",
            "service_address": "a",
            "service_type": "INSTALL",
            "appointment_time": "t",
            "estimated_duration_minutes": 10,
        },
    ).json()

    response = client.patch(
        f"/api/orders/v1/orders/{created['order_id']}/status",
        json={"target_status": "PENDING", "assigned_worker_id": ""},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "PENDING"
