import re

from fastapi.testclient import TestClient

from hsp_order_service.repository.in_memory import (
    InMemoryEchoRepository,
    InMemoryOrderRepository,
)
from hsp_order_service.service.echo_service import EchoService
from hsp_order_service.service.order_service import OrderService
from hsp_order_service.transport.http.app import create_http_app


def build_client() -> TestClient:
    app = create_http_app(
        EchoService(InMemoryEchoRepository()),
        OrderService(InMemoryOrderRepository()),
    )
    return TestClient(app)


def test_all_responses_have_security_headers() -> None:
    response = build_client().get("/healthz")

    assert response.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def test_docs_use_pinned_subresources_with_integrity() -> None:
    response = build_client().get("/docs")

    assert response.status_code == 200
    assert "swagger-ui-dist@5.27.1/swagger-ui.css" in response.text
    assert "swagger-ui-dist@5.27.1/swagger-ui-bundle.js" in response.text
    assert response.text.count('integrity="sha384-') == 2
    assert response.text.count('crossorigin="anonymous"') == 2


def test_docs_csp_allows_only_the_generated_inline_script_nonce() -> None:
    response = build_client().get("/docs")

    nonce_match = re.search(r'<script nonce="([A-Za-z0-9_-]+)">', response.text)
    assert nonce_match is not None
    csp = response.headers["content-security-policy"]
    assert f"'nonce-{nonce_match.group(1)}'" in csp
    assert "frame-ancestors 'none'" in csp
    assert response.headers["x-frame-options"] == "DENY"
