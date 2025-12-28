"""
Download completion catalog write-through tests (no yt-dlp invocation).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.catalog.repository import CatalogRepository
from app.config import settings
from app.downloads.schemas import DownloadRequest
from app.jobs import service as jobs_service
from app.jobs.service import create_job


@pytest.mark.asyncio
async def test_download_completion_upserts_local_catalog(tmp_path: Path, monkeypatch):
    repo = CatalogRepository()
    repo.clear_location("local")

    monkeypatch.setattr(settings, "CATALOG_ENABLED", True)

    out_dir = tmp_path / "downloads"
    out_dir.mkdir(parents=True, exist_ok=True)

    video = out_dir / "Channel" / "video.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"fake video")
    thumb = video.with_suffix(".jpg")
    thumb.write_bytes(b"fake thumb")

    async def fake_execute_download(url, download_settings, progress_callback):
        progress_callback({"status": "finished", "filepath": str(video)})
        return {"status": "completed", "results": [{"status": "success"}], "total": 1}

    monkeypatch.setattr(jobs_service, "execute_download", fake_execute_download)

    request = DownloadRequest(
        url="https://www.youtube.com/watch?v=test123",
        out_dir=str(out_dir),
    )
    job_id = create_job(request.url, request)

    await jobs_service.run_download_job(job_id, request.url, request)

    assert repo.get_counts()["local"] == 1
    row = repo.get_video("local:Channel/video.mp4")
    assert row

