"""
Initial Drive catalog bootstrap tests (no network).
"""

from __future__ import annotations

import asyncio
from datetime import datetime

import httpx
import pytest

from app.catalog.repository import CatalogRepository
from app.config import settings
from app.drive.manager import drive_manager


@pytest.mark.asyncio
async def test_drive_list_does_not_fallback_when_catalog_enabled_and_empty(
    client: httpx.AsyncClient, monkeypatch
):
    repo = CatalogRepository()
    repo.clear_location("drive")

    monkeypatch.setattr(settings, "CATALOG_ENABLED", True)
    monkeypatch.setattr(settings, "CATALOG_DRIVE_ALLOW_LEGACY_LISTING_FALLBACK", False)
    monkeypatch.setattr(drive_manager, "is_authenticated", lambda: True)

    # If this gets called, we'd reintroduce the slow Drive listing.
    monkeypatch.setattr(drive_manager, "list_videos", lambda: (_ for _ in ()).throw(AssertionError("legacy listing called")))

    resp = await client.get("/api/drive/videos", params={"page": 1, "limit": 10})
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["total"] == 0
    assert payload["videos"] == []
    assert "warning" in payload


@pytest.mark.asyncio
async def test_drive_rebuild_job_populates_catalog_and_enables_fast_list(
    client: httpx.AsyncClient, monkeypatch
):
    repo = CatalogRepository()
    repo.clear_location("drive")

    monkeypatch.setattr(settings, "CATALOG_ENABLED", True)
    monkeypatch.setattr(settings, "CATALOG_DRIVE_ALLOW_LEGACY_LISTING_FALLBACK", False)
    monkeypatch.setattr(drive_manager, "is_authenticated", lambda: True)

    fake_videos = [
        {
            "id": "vid1",
            "name": "Video 1.mp4",
            "path": "Channel/Video 1.mp4",
            "size": 123,
            "created_at": datetime.utcnow().isoformat(),
            "modified_at": datetime.utcnow().isoformat(),
            "thumbnail": None,
            "custom_thumbnail_id": "thumb1",
        }
    ]
    monkeypatch.setattr(drive_manager, "list_videos", lambda: fake_videos)

    async def fake_publish(*args, **kwargs):
        return {"status": "success", "file_id": "catalog123"}

    monkeypatch.setattr("app.catalog.service.publish_drive_snapshot", fake_publish)

    resp = await client.post("/api/catalog/drive/rebuild")
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]

    # Wait for completion
    for _ in range(50):
        job = (await client.get(f"/api/jobs/{job_id}")).json()
        if job["status"] in {"completed", "error"}:
            break
        await asyncio.sleep(0.05)

    job = (await client.get(f"/api/jobs/{job_id}")).json()
    assert job["status"] == "completed"

    # Listing should now come from the catalog (fast), with 1 item.
    resp2 = await client.get("/api/drive/videos", params={"page": 1, "limit": 10})
    assert resp2.status_code == 200
    payload = resp2.json()
    assert payload["total"] == 1
    assert len(payload["videos"]) == 1
    assert payload["videos"][0]["id"] == "vid1"
    assert payload["videos"][0]["custom_thumbnail_id"] == "thumb1"

