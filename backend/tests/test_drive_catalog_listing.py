"""
Tests for Drive listing via the local catalog (no Drive API calls).
"""

import httpx
import pytest

from app.catalog.drive_snapshot import build_drive_snapshot, encode_drive_snapshot
from app.catalog.service import import_drive_snapshot_bytes
from app.config import settings
from app.drive.manager import drive_manager


@pytest.mark.asyncio
async def test_drive_videos_endpoint_reads_from_catalog(client: httpx.AsyncClient, monkeypatch):
    # Populate drive catalog from a snapshot (no network)
    payload = build_drive_snapshot(
        videos=[
            {
                "video_uid": "drive:abc",
                "path": "Ch/video.mp4",
                "created_at": "2025-01-01T00:00:00Z",
                "modified_at": "2025-01-02T00:00:00Z",
                "assets": [
                    {"kind": "video", "drive_file_id": "1vid", "mime_type": "video/mp4", "size_bytes": 123},
                    {"kind": "thumbnail", "drive_file_id": "1thumb", "mime_type": "image/jpeg"},
                ],
            }
        ]
    )
    await import_drive_snapshot_bytes(snapshot_bytes=encode_drive_snapshot(payload))

    monkeypatch.setattr(settings, "CATALOG_ENABLED", True)
    monkeypatch.setattr(drive_manager, "is_authenticated", lambda: True)

    response = await client.get("/api/drive/videos", params={"page": 1, "limit": 24})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["videos"][0]["id"] == "1vid"
    assert data["videos"][0]["path"] == "Ch/video.mp4"
    assert data["videos"][0]["custom_thumbnail_id"] == "1thumb"

