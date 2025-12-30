"""
Unit tests for error helpers.
"""
import json

import pytest
from fastapi import HTTPException, status
from starlette.requests import Request

from app.core.errors import (
    ErrorCode,
    AppException,
    create_error_response,
    raise_error,
    http_exception_handler,
)


def _make_request() -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [],
        "client": ("10.0.0.1", 1234),
        "server": ("testserver", 80),
        "scheme": "http",
    }
    return Request(scope)


def test_create_error_response_sets_request_id_header() -> None:
    response = create_error_response(
        status_code=400,
        error_code=ErrorCode.INVALID_REQUEST,
        message="bad",
        request_id="req-1",
    )
    payload = json.loads(response.body.decode("utf-8"))
    assert payload["request_id"] == "req-1"
    assert response.headers.get("X-Request-Id") == "req-1"


def test_raise_error_raises_app_exception() -> None:
    with pytest.raises(AppException) as exc:
        raise_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=ErrorCode.INVALID_REQUEST,
            message="bad",
        )
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc.value.error_code == ErrorCode.INVALID_REQUEST


@pytest.mark.asyncio
async def test_http_exception_handler_maps_code() -> None:
    request = _make_request()
    exc = HTTPException(status_code=404, detail="missing")
    response = await http_exception_handler(request, exc)
    payload = json.loads(response.body.decode("utf-8"))
    assert payload["error_code"] == ErrorCode.NOT_FOUND
