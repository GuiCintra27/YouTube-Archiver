"""
Unit tests for Drive snapshot codec edge cases.
"""
import json

import pytest

from app.catalog.drive_snapshot import build_drive_snapshot, decode_drive_snapshot


def test_decode_accepts_plain_json_bytes() -> None:
    payload = build_drive_snapshot(videos=[], library_id="lib1", generated_at="2025-01-01T00:00:00Z")
    raw = json.dumps(payload).encode("utf-8")
    decoded = decode_drive_snapshot(raw)
    assert decoded["library_id"] == "lib1"
    assert decoded["generated_at"] == "2025-01-01T00:00:00Z"


def test_decode_rejects_missing_videos_list() -> None:
    raw = b'{"schema_version":1,"videos":{}}'
    with pytest.raises(ValueError, match="videos"):
        decode_drive_snapshot(raw)


def test_build_drive_snapshot_preserves_generated_at() -> None:
    payload = build_drive_snapshot(
        videos=[],
        library_id="library-a",
        generated_at="2026-02-02T12:00:00Z",
    )
    assert payload["library_id"] == "library-a"
    assert payload["generated_at"] == "2026-02-02T12:00:00Z"
