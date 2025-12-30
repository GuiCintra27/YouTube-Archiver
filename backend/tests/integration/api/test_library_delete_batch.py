"""
Integration tests for library batch delete endpoint.
"""
from pathlib import Path

import httpx
import pytest


@pytest.mark.asyncio
async def test_delete_batch_removes_files(
    client: httpx.AsyncClient, tmp_path: Path
) -> None:
    base_dir = tmp_path / "downloads"
    base_dir.mkdir()
    channel_dir = base_dir / "Channel"
    channel_dir.mkdir()
    video_path = channel_dir / "video.mp4"
    thumb_path = channel_dir / "video.jpg"
    video_path.write_bytes(b"video")
    thumb_path.write_bytes(b"thumb")

    response = await client.post(
        "/api/videos/delete-batch",
        params={"base_dir": str(base_dir)},
        json=["Channel/video.mp4"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_deleted"] == 1
    assert not video_path.exists()
    assert not thumb_path.exists()
