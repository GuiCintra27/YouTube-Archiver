"""
Tests for standardized error handling.
"""

import httpx
import pytest
from fastapi import FastAPI

from app.core.errors import register_exception_handlers
from app.core.middleware.request_id import RequestIdMiddleware


@pytest.mark.asyncio
async def test_generic_exception_handler_returns_standard_error():
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)

    @app.get("/boom")
    async def boom():
        raise RuntimeError("boom")

    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as client:
            response = await client.get("/boom", headers={"X-Request-Id": "req-1"})

    assert response.status_code == 500
    assert response.headers.get("x-request-id") == "req-1"
    data = response.json()
    assert data["error_code"] == "INTERNAL_ERROR"
    assert data["request_id"] == "req-1"

