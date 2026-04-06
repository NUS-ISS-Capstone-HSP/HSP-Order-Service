from fastapi.testclient import TestClient

from hsp_order_service.repository.in_memory import InMemoryEchoRepository
from hsp_order_service.repository.order_in_memory import InMemoryOrderRepository
from hsp_order_service.service.echo_service import EchoService
from hsp_order_service.service.order_service import OrderService
from hsp_order_service.transport.http.app import create_http_app


def build_client() -> TestClient:
    app = create_http_app(
        EchoService(InMemoryEchoRepository()),
        OrderService(InMemoryOrderRepository()),
    )
    return TestClient(app)


def _build_create_payload(customer_name: str = "Alice") -> dict[str, object]:
    return {
        "customer_name": customer_name,
        "phone": "13812345678",
        "service_address": "Shanghai Road 100",
        "service_type": "cleaning",
        "appointment_time": "2026-04-10T09:00:00+08:00",
        "estimated_duration_minutes": 90,
    }


def test_create_order_success() -> None:
    client = build_client()

    response = client.post("/api/orders/v1/orders", json=_build_create_payload())

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "created"
    assert payload["service_type"] == "cleaning"
    assert payload["order_id"]


def test_create_order_missing_required_field() -> None:
    client = build_client()

    payload = _build_create_payload()
    del payload["customer_name"]

    response = client.post("/api/orders/v1/orders", json=payload)

    assert response.status_code == 422


def test_list_orders_filter_by_customer_name() -> None:
    client = build_client()

    client.post("/api/orders/v1/orders", json=_build_create_payload("Alice"))
    client.post("/api/orders/v1/orders", json=_build_create_payload("Bob"))

    response = client.get("/api/orders/v1/orders", params={"customer_name": "Alice"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["customer_name"] == "Alice"


def test_update_order_status_reject_illegal_transition() -> None:
    client = build_client()

    created = client.post("/api/orders/v1/orders", json=_build_create_payload()).json()

    response = client.patch(
        f"/api/orders/v1/orders/{created['order_id']}/status",
        json={"target_status": "complete"},
    )

    assert response.status_code == 409


def test_update_order_status_success() -> None:
    client = build_client()

    created = client.post("/api/orders/v1/orders", json=_build_create_payload()).json()

    response = client.patch(
        f"/api/orders/v1/orders/{created['order_id']}/status",
        json={"target_status": "pending", "assigned_worker_id": "worker-001"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "pending"
    assert payload["assigned_worker_id"] == "worker-001"
