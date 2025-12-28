"""
Drive catalog write-through tests (no network).
"""

from __future__ import annotations

import httpx
import pytest

from app.catalog.repository import CatalogRepository
from app.config import settings
from app.drive.manager import drive_manager


def _seed_drive_video(repo: CatalogRepository, *, file_id: str, drive_path: str, thumbnail_id: str = "thumb1") -> None:
    repo.clear_location("drive")
    repo.upsert_video(
        video_uid=f"drive:{file_id}",
        location="drive",
        source="custom",
        title="old",
        channel="Channel",
        duration_seconds=None,
        created_at="2025-01-01T00:00:00",
        modified_at="2025-01-01T00:00:00",
        status="available",
        extra={"drive_path": drive_path},
    )
    repo.replace_assets(
        video_uid=f"drive:{file_id}",
        location="drive",
        assets=[
            {"kind": "video", "drive_file_id": file_id, "size_bytes": 123},
            {"kind": "thumbnail", "drive_file_id": thumbnail_id},
        ],
    )


@pytest.mark.asyncio
async def test_drive_rename_updates_catalog_and_publishes(client: httpx.AsyncClient, monkeypatch):
    repo = CatalogRepository()
    monkeypatch.setattr(settings, "CATALOG_ENABLED", True)
    monkeypatch.setattr(settings, "CATALOG_DRIVE_AUTO_PUBLISH", True)
    monkeypatch.setattr(drive_manager, "is_authenticated", lambda: True)

    _seed_drive_video(repo, file_id="vid123", drive_path="Channel/old.mp4")

    published = {"called": 0}

    async def fake_publish(*args, **kwargs):
        published["called"] += 1
        return {"status": "success"}

    monkeypatch.setattr("app.catalog.service.publish_drive_snapshot", fake_publish)
    monkeypatch.setattr(
        drive_manager,
        "rename_file",
        lambda file_id, new_name: {
            "status": "success",
            "file_id": file_id,
            "new_name": "new.mp4",
            "renamed_related": [],
        },
    )

    resp = await client.patch("/api/drive/videos/vid123/rename", json={"new_name": "new"})
    assert resp.status_code == 200

    row = repo.get_video("drive:vid123")
    assert row
    assert "new" in (row.get("title") or "")
    assert published["called"] == 1


@pytest.mark.asyncio
async def test_drive_thumbnail_update_updates_catalog_and_publishes(client: httpx.AsyncClient, monkeypatch):
    repo = CatalogRepository()
    monkeypatch.setattr(settings, "CATALOG_ENABLED", True)
    monkeypatch.setattr(settings, "CATALOG_DRIVE_AUTO_PUBLISH", True)
    monkeypatch.setattr(drive_manager, "is_authenticated", lambda: True)

    _seed_drive_video(repo, file_id="vid123", drive_path="Channel/old.mp4")

    published = {"called": 0}

    async def fake_publish(*args, **kwargs):
        published["called"] += 1
        return {"status": "success"}

    monkeypatch.setattr("app.catalog.service.publish_drive_snapshot", fake_publish)
    monkeypatch.setattr(
        drive_manager,
        "update_thumbnail",
        lambda file_id, thumbnail_data, file_ext: {
            "status": "success",
            "thumbnail_id": "thumb2",
            "thumbnail_name": "old.jpg",
        },
    )

    resp = await client.post(
        "/api/drive/videos/vid123/thumbnail",
        files={"thumbnail": ("thumb.jpg", b"abc", "image/jpeg")},
    )
    assert resp.status_code == 200

    assets = repo.get_assets(video_uid="drive:vid123", location="drive")
    thumb = next((a for a in assets if a.get("kind") == "thumbnail"), None)
    assert thumb and thumb.get("drive_file_id") == "thumb2"
    assert published["called"] == 1


@pytest.mark.asyncio
async def test_drive_delete_removes_catalog_and_publishes(client: httpx.AsyncClient, monkeypatch):
    repo = CatalogRepository()
    monkeypatch.setattr(settings, "CATALOG_ENABLED", True)
    monkeypatch.setattr(settings, "CATALOG_DRIVE_AUTO_PUBLISH", True)
    monkeypatch.setattr(drive_manager, "is_authenticated", lambda: True)

    _seed_drive_video(repo, file_id="vid123", drive_path="Channel/old.mp4")

    published = {"called": 0}

    async def fake_publish(*args, **kwargs):
        published["called"] += 1
        return {"status": "success"}

    monkeypatch.setattr("app.catalog.service.publish_drive_snapshot", fake_publish)
    monkeypatch.setattr(drive_manager, "delete_video", lambda file_id: True)

    resp = await client.delete("/api/drive/videos/vid123")
    assert resp.status_code == 200
    assert repo.get_video("drive:vid123") == {}
    assert published["called"] == 1

