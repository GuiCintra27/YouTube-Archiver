"""
Integration tests for catalog bootstrap + library list.
"""
from pathlib import Path

import httpx
import pytest

from app.config import settings


@pytest.mark.asyncio
async def test_bootstrap_local_populates_catalog_and_list(
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

    response = await client.post(
        "/api/catalog/bootstrap-local",
        params={"base_dir": str(base_dir)},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["inserted"] == 1

    monkeypatch.setattr(settings, "CATALOG_ENABLED", True)

    list_response = await client.get("/api/videos", params={"page": 1, "limit": 10})
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["total"] == 1
    assert payload["videos"][0]["path"] == "Channel/video.mp4"
