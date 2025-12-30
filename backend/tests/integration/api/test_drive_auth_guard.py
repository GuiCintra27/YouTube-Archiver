"""
Integration tests for Drive auth guards.
"""
import httpx
import pytest

from app.drive.manager import drive_manager


@pytest.mark.asyncio
async def test_drive_download_requires_auth(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(drive_manager, "is_authenticated", lambda: False)
    response = await client.post(
        "/api/drive/download",
        params={"path": "Channel/video.mp4"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error_code"] == "DRIVE_NOT_AUTHENTICATED"
