"""
Tests for health check endpoint.
"""
import pytest
import httpx


async def test_root_endpoint(client: httpx.AsyncClient):
    """Test the root health check endpoint."""
    response = await client.get("/")

    assert response.status_code == 200
    assert response.headers.get("x-request-id")
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "YT-Archiver" in data["message"]


async def test_root_returns_version(client: httpx.AsyncClient):
    """Test that root endpoint returns version info."""
    response = await client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "2.0.0"


async def test_request_id_is_preserved(client: httpx.AsyncClient):
    """Test that X-Request-Id is echoed back when provided."""
    response = await client.get("/", headers={"X-Request-Id": "test-req-123"})
    assert response.status_code == 200
    assert response.headers.get("x-request-id") == "test-req-123"
