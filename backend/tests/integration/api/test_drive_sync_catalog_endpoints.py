"""
Integration tests for drive sync endpoints backed by catalog.
"""
import httpx
import pytest

from app.catalog.repository import CatalogRepository
from app.config import settings
from app.drive.manager import drive_manager


def _seed_catalog(repo: CatalogRepository) -> None:
    repo.clear_location("local")
    repo.clear_location("drive")

    repo.upsert_video(
        video_uid="local:Channel/a.mp4",
        location="local",
        source="custom",
        title="a",
        channel="Channel",
        duration_seconds=None,
        created_at="2025-01-01T00:00:00",
        modified_at="2025-01-01T00:00:00",
        status="available",
    )
    repo.replace_assets(
        video_uid="local:Channel/a.mp4",
        location="local",
        assets=[{"kind": "video", "local_path": "Channel/a.mp4"}],
    )

    repo.upsert_video(
        video_uid="local:Channel/b.mp4",
        location="local",
        source="custom",
        title="b",
        channel="Channel",
        duration_seconds=None,
        created_at="2025-01-01T00:00:00",
        modified_at="2025-01-01T00:00:00",
        status="available",
    )
    repo.replace_assets(
        video_uid="local:Channel/b.mp4",
        location="local",
        assets=[{"kind": "video", "local_path": "Channel/b.mp4"}],
    )

    repo.upsert_video(
        video_uid="drive:file-1",
        location="drive",
        source="custom",
        title="a",
        channel="Channel",
        duration_seconds=None,
        created_at="2025-01-01T00:00:00",
        modified_at="2025-01-01T00:00:00",
        status="available",
        extra={"drive_path": "Channel/a.mp4"},
    )
    repo.replace_assets(
        video_uid="drive:file-1",
        location="drive",
        assets=[{"kind": "video", "local_path": "Channel/a.mp4", "drive_file_id": "file-1"}],
    )

    repo.upsert_video(
        video_uid="drive:file-2",
        location="drive",
        source="custom",
        title="c",
        channel="Channel",
        duration_seconds=None,
        created_at="2025-01-01T00:00:00",
        modified_at="2025-01-01T00:00:00",
        status="available",
        extra={"drive_path": "Channel/c.mp4"},
    )
    repo.replace_assets(
        video_uid="drive:file-2",
        location="drive",
        assets=[{"kind": "video", "local_path": "Channel/c.mp4", "drive_file_id": "file-2"}],
    )


@pytest.mark.asyncio
async def test_sync_status_counts(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = CatalogRepository()
    _seed_catalog(repo)

    monkeypatch.setattr(settings, "CATALOG_ENABLED", True)
    monkeypatch.setattr(drive_manager, "is_authenticated", lambda: True)

    response = await client.get("/api/drive/sync-status")
    assert response.status_code == 200
    data = response.json()
    assert data["local_only_count"] == 1
    assert data["drive_only_count"] == 1
    assert data["synced_count"] == 1


@pytest.mark.asyncio
async def test_sync_items_drive_only(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = CatalogRepository()
    _seed_catalog(repo)

    monkeypatch.setattr(settings, "CATALOG_ENABLED", True)
    monkeypatch.setattr(drive_manager, "is_authenticated", lambda: True)

    response = await client.get("/api/drive/sync-items", params={"kind": "drive_only", "page": 1, "limit": 10})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["path"] == "Channel/c.mp4"
    assert data["items"][0]["file_id"] == "file-2"


@pytest.mark.asyncio
async def test_sync_items_invalid_kind(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "CATALOG_ENABLED", True)
    monkeypatch.setattr(drive_manager, "is_authenticated", lambda: True)

    response = await client.get("/api/drive/sync-items", params={"kind": "invalid", "page": 1, "limit": 10})
    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "INVALID_REQUEST"
