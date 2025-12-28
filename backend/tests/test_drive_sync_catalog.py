"""
Catalog-backed sync-status/items tests (no Drive list/scan).
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from app.catalog.drive_snapshot import build_drive_snapshot, encode_drive_snapshot
from app.catalog.service import import_drive_snapshot_bytes
from app.config import settings
from app.drive.manager import drive_manager


@pytest.mark.asyncio
async def test_sync_status_and_items_are_catalog_backed(
    client: httpx.AsyncClient, downloads_dir: Path, sample_video_file: Path, monkeypatch
):
    # Local catalog bootstrap
    response = await client.post(
        "/api/catalog/bootstrap-local",
        params={"base_dir": str(downloads_dir)},
    )
    assert response.status_code == 200

    # Drive catalog import (no network)
    payload = build_drive_snapshot(
        videos=[
            {
                "video_uid": "drive:abc",
                "path": "Other/drive.mp4",
                "created_at": "2025-01-01T00:00:00Z",
                "modified_at": "2025-01-02T00:00:00Z",
                "assets": [
                    {"kind": "video", "drive_file_id": "1vid", "mime_type": "video/mp4", "size_bytes": 123},
                ],
            }
        ]
    )
    await import_drive_snapshot_bytes(snapshot_bytes=encode_drive_snapshot(payload))

    monkeypatch.setattr(settings, "CATALOG_ENABLED", True)
    monkeypatch.setattr(drive_manager, "is_authenticated", lambda: True)

    # Ensure we don't fall back to legacy scanning
    monkeypatch.setattr(drive_manager, "get_sync_state", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("legacy sync called")))
    monkeypatch.setattr(drive_manager, "list_videos", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("legacy list called")))

    status_resp = await client.get("/api/drive/sync-status")
    assert status_resp.status_code == 200
    status = status_resp.json()
    assert status["total_local"] == 1
    assert status["total_drive"] == 1
    assert status["local_only_count"] == 1
    assert status["drive_only_count"] == 1

    items_resp = await client.get(
        "/api/drive/sync-items",
        params={"kind": "drive_only", "page": 1, "limit": 50},
    )
    assert items_resp.status_code == 200
    items = items_resp.json()
    assert items["kind"] == "drive_only"
    assert items["total"] == 1
    assert items["items"][0]["path"] == "Other/drive.mp4"
    assert items["items"][0]["file_id"] == "1vid"

