"""
Integration tests for catalog publish endpoint.
"""
import pytest
import httpx


@pytest.mark.asyncio
async def test_catalog_drive_publish_returns_payload(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_publish(*args, **kwargs):
        return {
            "status": "success",
            "file_id": "file-1",
            "name": "catalog-drive.json.gz",
            "size": 10,
            "generated_at": "2025-01-01T00:00:00Z",
            "videos": 0,
        }

    monkeypatch.setattr("app.catalog.router.publish_drive_snapshot", fake_publish)

    response = await client.post("/api/catalog/drive/publish")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["file_id"] == "file-1"
