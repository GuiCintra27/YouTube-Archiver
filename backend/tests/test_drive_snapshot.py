"""
Unit tests for Drive catalog snapshot encoding/decoding.
"""

import pytest

from app.catalog.drive_snapshot import build_drive_snapshot, decode_drive_snapshot, encode_drive_snapshot


def test_encode_decode_roundtrip():
    payload = build_drive_snapshot(
        videos=[
            {
                "video_uid": "drive:abc",
                "title": "Video",
                "channel": "Ch",
                "duration_seconds": 10,
                "modified_at": "2025-01-01T00:00:00Z",
                "assets": [
                    {"kind": "video", "drive_file_id": "1vid", "mime_type": "video/mp4"},
                    {"kind": "thumbnail", "drive_file_id": "1thumb", "mime_type": "image/jpeg"},
                ],
            }
        ]
    )

    data = encode_drive_snapshot(payload)
    decoded = decode_drive_snapshot(data)
    assert decoded["schema_version"] == payload["schema_version"]
    assert decoded["videos"][0]["video_uid"] == "drive:abc"


def test_decode_rejects_wrong_schema_version():
    bad = b'{"schema_version":999,"videos":[]}'
    with pytest.raises(ValueError):
        decode_drive_snapshot(bad)

