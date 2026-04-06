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


def test_healthz_success() -> None:
    client = build_client()

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_echo_success() -> None:
    client = build_client()

    response = client.post("/api/orders/v1/echo", json={"message": "hello http"})

    assert response.status_code == 201
    payload = response.json()
    assert payload["message"] == "hello http"
    assert payload["source"] == "HTTP"


def test_create_echo_validation_error() -> None:
    client = build_client()

    response = client.post("/api/orders/v1/echo", json={"message": ""})

    assert response.status_code == 422


def test_get_echo_not_found() -> None:
    client = build_client()

    response = client.get("/api/orders/v1/echo/not-exists")

    assert response.status_code == 404
