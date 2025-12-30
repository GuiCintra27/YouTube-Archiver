"""
Integration tests for catalog status endpoint.
"""
import httpx
import pytest


@pytest.mark.asyncio
async def test_catalog_status_returns_fields(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/catalog/status")
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data
    assert "counts" in data
    assert "state" in data
