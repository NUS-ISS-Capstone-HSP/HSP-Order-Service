import secrets

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from hsp_order_service.domain.errors import (
    DomainError,
    NotFoundError,
    TransitionError,
    ValidationError,
)
from hsp_order_service.service.echo_service import EchoService
from hsp_order_service.service.order_service import OrderService
from hsp_order_service.transport.http.router import build_router

_SWAGGER_UI_VERSION = "5.27.1"
_SWAGGER_UI_BASE_URL = (
    f"https://cdn.jsdelivr.net/npm/swagger-ui-dist@{_SWAGGER_UI_VERSION}"
)
_SWAGGER_UI_CSS_INTEGRITY = (
    "sha384-++DMKo1369T5pxDNqojF1F91bYxYiT1N7b1M15a7oCzEodfljztKlApQoH6eQSKI"
)
_SWAGGER_UI_JS_INTEGRITY = (
    "sha384-5pEDYOWQic3ejKOvYt1kQ5QWoglLXBxyqM5/7vL8NrQW4YHiKCswfiHxxBp77KJN"
)
_OPENAPI_URL = "/openapi.json"
_DEFAULT_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"


def _swagger_ui_html(openapi_url: str, nonce: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>HSP Order Service - Swagger UI</title>
  <link rel="stylesheet" href="{_SWAGGER_UI_BASE_URL}/swagger-ui.css"
        integrity="{_SWAGGER_UI_CSS_INTEGRITY}" crossorigin="anonymous">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="{_SWAGGER_UI_BASE_URL}/swagger-ui-bundle.js"
          integrity="{_SWAGGER_UI_JS_INTEGRITY}" crossorigin="anonymous"></script>
  <script nonce="{nonce}">
    SwaggerUIBundle({{
      url: "{openapi_url}",
      dom_id: "#swagger-ui",
      deepLinking: true,
      presets: [SwaggerUIBundle.presets.apis],
      layout: "BaseLayout"
    }});
  </script>
</body>
</html>
"""


def create_http_app(echo_service: EchoService, order_service: OrderService) -> FastAPI:
    app = FastAPI(
        title="HSP Order Service",
        openapi_url=_OPENAPI_URL,
        docs_url=None,
        redoc_url=None,
        swagger_ui_oauth2_redirect_url=None,
    )
    app.include_router(build_router(echo_service, order_service))

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("Content-Security-Policy", _DEFAULT_CSP)
        response.headers.setdefault("X-Frame-Options", "DENY")
        return response

    @app.get("/docs", include_in_schema=False)
    async def swagger_ui() -> HTMLResponse:
        nonce = secrets.token_urlsafe(24)
        content_security_policy = (
            "default-src 'none'; "
            f"script-src https://cdn.jsdelivr.net 'nonce-{nonce}'; "
            "style-src https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'none'; "
            "form-action 'none'"
        )
        return HTMLResponse(
            _swagger_ui_html(_OPENAPI_URL, nonce),
            headers={"Content-Security-Policy": content_security_policy},
        )

    @app.get("/healthz", tags=["health"])
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.exception_handler(ValidationError)
    async def validation_handler(_: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(NotFoundError)
    async def not_found_handler(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(TransitionError)
    async def transition_handler(_: Request, exc: TransitionError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(DomainError)
    async def domain_handler(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": str(exc)})

    return app
