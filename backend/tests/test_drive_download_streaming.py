from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterator, Optional, Tuple

import pytest

from app.drive.manager import DriveManager


class _FakeStreamingResponse:
    def __init__(self, *, status_code: int, chunks: list[bytes], text: str = ""):
        self.status_code = status_code
        self._chunks = chunks
        self.text = text

    def __enter__(self) -> "_FakeStreamingResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def iter_content(self, chunk_size: int = 1024 * 1024) -> Iterator[bytes]:
        _ = chunk_size
        for chunk in self._chunks:
            yield chunk


def test_download_file_does_not_use_google_service(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manager = DriveManager(credentials_path="missing.json", token_path=str(tmp_path / "token.json"))

    monkeypatch.setattr(manager, "get_service", lambda: (_ for _ in ()).throw(AssertionError("should not call get_service")))
    monkeypatch.setattr(
        manager,
        "_drive_api_get_json",
        lambda url, params: {"name": "video.mp4", "size": "6", "mimeType": "video/mp4", "parents": []},
    )

    called: Dict[str, object] = {}

    def _fake_download_to_path(
        *,
        file_id: str,
        dest_path: Path,
        expected_size: int = 0,
        progress_callback=None,
        file_name: Optional[str] = None,
    ) -> int:
        called["file_id"] = file_id
        called["dest_path"] = dest_path
        called["expected_size"] = expected_size
        called["file_name"] = file_name
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(b"abcdef")
        return 6

    monkeypatch.setattr(manager, "_drive_api_download_to_path", _fake_download_to_path)

    result = manager.download_file(
        file_id="file123",
        relative_path="Channel/video.mp4",
        local_base_dir=str(tmp_path),
        progress_callback=None,
    )

    assert result["status"] == "success"
    assert (tmp_path / "Channel" / "video.mp4").read_bytes() == b"abcdef"
    assert called["file_id"] == "file123"
    assert called["expected_size"] == 6


def test_drive_api_download_to_path_streams_and_renames(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manager = DriveManager(credentials_path="missing.json", token_path=str(tmp_path / "token.json"))
    monkeypatch.setattr(manager, "_get_access_token", lambda: "token")

    def _fake_requests_get(url: str, headers: Dict[str, str], params: Dict[str, str], stream: bool, timeout: Tuple[int, int]):
        assert url.endswith("/files/file123")
        assert headers.get("Authorization") == "Bearer token"
        assert params.get("alt") == "media"
        assert stream is True
        return _FakeStreamingResponse(status_code=200, chunks=[b"abc", b"def"])

    monkeypatch.setattr("requests.get", _fake_requests_get)

    dest = tmp_path / "out.mp4"
    written = manager._drive_api_download_to_path(file_id="file123", dest_path=dest, expected_size=6)
    assert written == 6
    assert dest.read_bytes() == b"abcdef"
    assert not (tmp_path / "out.mp4.part").exists()


def test_drive_api_download_to_path_incomplete_removes_part(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manager = DriveManager(credentials_path="missing.json", token_path=str(tmp_path / "token.json"))
    monkeypatch.setattr(manager, "_get_access_token", lambda: "token")

    def _fake_requests_get(url: str, headers: Dict[str, str], params: Dict[str, str], stream: bool, timeout: Tuple[int, int]):
        _ = (url, headers, params, stream, timeout)
        return _FakeStreamingResponse(status_code=200, chunks=[b"abc"])

    monkeypatch.setattr("requests.get", _fake_requests_get)

    dest = tmp_path / "out.mp4"
    with pytest.raises(Exception, match="Incomplete download"):
        manager._drive_api_download_to_path(file_id="file123", dest_path=dest, expected_size=6)
    assert not (tmp_path / "out.mp4.part").exists()

