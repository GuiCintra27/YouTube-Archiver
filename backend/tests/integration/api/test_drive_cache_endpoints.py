"""
Integration tests for Drive cache endpoints.
"""
import pytest
import httpx

from app.config import settings
from app.drive.manager import drive_manager


@pytest.mark.asyncio
async def test_cache_stats_disabled(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/drive/cache/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is False


@pytest.mark.asyncio
async def test_cache_sync_disabled_returns_error(client: httpx.AsyncClient) -> None:
    response = await client.post("/api/drive/cache/sync")
    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "INVALID_REQUEST"


@pytest.mark.asyncio
async def test_cache_sync_enabled_uses_incremental(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "DRIVE_CACHE_ENABLED", True)
    monkeypatch.setattr(drive_manager, "is_authenticated", lambda: True)

    class _SyncResult:
        success = True
        message = "ok"
        added = 1
        updated = 0
        deleted = 0
        changes_detected = 1

    async def fake_incremental_sync():
        return _SyncResult()

    import app.drive.cache as cache_module

    monkeypatch.setattr(cache_module, "incremental_sync", fake_incremental_sync)

    response = await client.post("/api/drive/cache/sync")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["sync_type"] == "incremental"
    assert data["added"] == 1
