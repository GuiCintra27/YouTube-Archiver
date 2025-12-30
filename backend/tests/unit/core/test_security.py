"""
Unit tests for security compatibility wrappers.
"""
from pathlib import Path

import pytest

from app.core.exceptions import AccessDeniedException, VideoNotFoundException
from app.core.security import (
    validate_path_within_base,
    validate_file_exists,
    sanitize_path,
    encode_filename_for_header,
    get_safe_relative_path,
)


def test_validate_path_within_base_allows_inside(tmp_path: Path) -> None:
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    file_path = base_dir / "file.txt"
    file_path.write_text("ok", encoding="utf-8")
    validate_path_within_base(file_path, base_dir)


def test_validate_path_within_base_rejects_outside(tmp_path: Path) -> None:
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("no", encoding="utf-8")
    with pytest.raises(AccessDeniedException):
        validate_path_within_base(outside, base_dir)


def test_validate_file_exists_rejects_missing(tmp_path: Path) -> None:
    with pytest.raises(VideoNotFoundException):
        validate_file_exists(tmp_path / "missing.mp4")


def test_sanitize_path_decodes_url() -> None:
    assert sanitize_path("Channel%2Fvideo%20title.mp4") == "Channel/video title.mp4"


def test_encode_filename_for_header_encodes_spaces() -> None:
    assert encode_filename_for_header("video name.mp4") == "video%20name.mp4"


def test_get_safe_relative_path_rejects_absolute() -> None:
    with pytest.raises(AccessDeniedException):
        get_safe_relative_path("/tmp/file.txt")
