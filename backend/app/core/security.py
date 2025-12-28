"""
Security utilities for path validation and sanitization
"""
from pathlib import Path

from app.core.paths import (
    decode_url_path,
    encode_filename_rfc5987,
    ensure_file_exists,
    ensure_relative_path,
    ensure_within_base,
)

# NOTE: This module is kept for backward compatibility.
# Prefer importing from `app.core.paths` for new code.

def validate_path_within_base(file_path: Path, base_dir: Path) -> None:
    """
    Validates that a file path is within the base directory.
    Raises AccessDeniedException if not.
    """
    ensure_within_base(file_path, base_dir)


def validate_file_exists(file_path: Path) -> None:
    """
    Validates that a file exists.
    Raises VideoNotFoundException if not.
    """
    ensure_file_exists(file_path)


def sanitize_path(path: str) -> str:
    """
    Sanitizes a URL-encoded path.
    """
    return decode_url_path(path)


def encode_filename_for_header(filename: str) -> str:
    """
    Encodes a filename for use in HTTP headers (RFC 5987).
    """
    return encode_filename_rfc5987(filename)


def get_safe_relative_path(target_path: str) -> Path:
    """
    Returns a safe relative path, validating it's not absolute.
    """
    return ensure_relative_path(target_path)
