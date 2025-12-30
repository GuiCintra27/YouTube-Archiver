"""
Unit tests for core path utilities.
"""
from pathlib import Path

import pytest

from app.core.exceptions import AccessDeniedException, VideoNotFoundException
from app.core.paths import (
    decode_url_path,
    encode_filename_rfc5987,
    ensure_relative_path,
    ensure_within_base,
    ensure_file_exists,
)


def test_decode_url_path_decodes_percent_encoding() -> None:
    encoded = "Channel%2Fvideo%20title.mp4"
    assert decode_url_path(encoded) == "Channel/video title.mp4"


def test_decode_url_path_empty_string() -> None:
    assert decode_url_path("") == ""


def test_encode_filename_rfc5987_encodes_spaces() -> None:
    assert encode_filename_rfc5987("video name.mp4") == "video%20name.mp4"


def test_ensure_relative_path_allows_relative() -> None:
    path = ensure_relative_path("folder/file.txt")
    assert path == Path("folder/file.txt")


def test_ensure_relative_path_rejects_absolute() -> None:
    with pytest.raises(AccessDeniedException):
        ensure_relative_path("/tmp/file.txt")


def test_ensure_within_base_allows_inside(tmp_path: Path) -> None:
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    candidate = base_dir / "file.txt"
    candidate.write_text("ok", encoding="utf-8")
    ensure_within_base(candidate, base_dir)


def test_ensure_within_base_rejects_outside(tmp_path: Path) -> None:
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("nope", encoding="utf-8")
    with pytest.raises(AccessDeniedException):
        ensure_within_base(outside, base_dir)


def test_ensure_within_base_rejects_traversal(tmp_path: Path) -> None:
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    traversal = base_dir / "../outside.txt"
    traversal.write_text("nope", encoding="utf-8")
    with pytest.raises(AccessDeniedException):
        ensure_within_base(traversal, base_dir)


def test_ensure_file_exists_allows_file(tmp_path: Path) -> None:
    file_path = tmp_path / "file.txt"
    file_path.write_text("ok", encoding="utf-8")
    ensure_file_exists(file_path)


def test_ensure_file_exists_rejects_missing(tmp_path: Path) -> None:
    missing = tmp_path / "missing.txt"
    with pytest.raises(VideoNotFoundException):
        ensure_file_exists(missing)
