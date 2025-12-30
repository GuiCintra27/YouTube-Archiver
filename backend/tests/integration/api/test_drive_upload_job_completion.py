"""
Integration test for drive upload job completion.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
import pytest

from app.config import settings
from app.drive.manager import drive_manager


@pytest.mark.asyncio
async def test_drive_upload_job_completes(
    client: httpx.AsyncClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base_dir = tmp_path / "downloads"
    base_dir.mkdir()
    channel_dir = base_dir / "Channel"
    channel_dir.mkdir()
    video_path = channel_dir / "video.mp4"
    video_path.write_bytes(b"video")

    monkeypatch.setattr(settings, "CATALOG_ENABLED", False)
    monkeypatch.setattr(drive_manager, "is_authenticated", lambda: True)

    def fake_upload_video(full_path: str, relative_path: str):
        assert Path(full_path).exists()
        return {
            "status": "success",
            "file_id": "file-1",
            "size": 123,
            "related_files_detailed": [],
        }

    monkeypatch.setattr(drive_manager, "upload_video", fake_upload_video)

    response = await client.post(
        "/api/drive/upload/Channel/video.mp4",
        params={"base_dir": str(base_dir)},
    )
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    status = None
    for _ in range(40):
        poll = await client.get(f"/api/jobs/{job_id}")
        assert poll.status_code == 200
        payload = poll.json()
        status = payload["status"]
        if status in ("completed", "error", "cancelled"):
            break
        await asyncio.sleep(0.05)

    assert status == "completed"
