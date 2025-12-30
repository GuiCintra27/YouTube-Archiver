"""
Unit tests for rate limit helpers.
"""
import json

from starlette.requests import Request
from slowapi.errors import RateLimitExceeded

from app.core.errors import ErrorCode
from app.core.rate_limit import get_client_ip, rate_limit_exceeded_handler


def _make_request(headers: dict[str, str] | None = None, client: tuple[str, int] | None = None) -> Request:
    headers = headers or {}
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(k.lower().encode("utf-8"), v.encode("utf-8")) for k, v in headers.items()],
        "client": client or ("10.0.0.1", 1234),
        "server": ("testserver", 80),
        "scheme": "http",
    }
    return Request(scope)


def test_get_client_ip_prefers_forwarded() -> None:
    request = _make_request(headers={"X-Forwarded-For": "1.2.3.4, 5.6.7.8"})
    assert get_client_ip(request) == "1.2.3.4"


def test_get_client_ip_fallbacks_to_real_ip() -> None:
    request = _make_request(headers={"X-Real-IP": "9.9.9.9"})
    assert get_client_ip(request) == "9.9.9.9"


def test_rate_limit_exceeded_handler_includes_request_id() -> None:
    request = _make_request()
    request.state.request_id = "req-123"

    class _DummyLimit:
        def __init__(self) -> None:
            self.error_message = None
            self.limit = "10/minute"

    exc = RateLimitExceeded(_DummyLimit())
    response = rate_limit_exceeded_handler(request, exc)

    payload = json.loads(response.body.decode("utf-8"))
    assert response.status_code == 429
    assert payload["error_code"] == ErrorCode.RATE_LIMIT_EXCEEDED
    assert payload["request_id"] == "req-123"
    assert response.headers.get("X-Request-Id") == "req-123"
