"""
Path and header encoding utilities (source of truth).

This module centralizes common path-related validations and RFC 5987 filename
encoding used across the backend.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote, unquote

from app.core.exceptions import AccessDeniedException, VideoNotFoundException


def decode_url_path(path: str) -> str:
    """Decode a URL-encoded path segment."""
    return unquote(path) if path else ""


def encode_filename_rfc5987(filename: str) -> str:
    """Encode a filename for use in HTTP headers (RFC 5987)."""
    return quote(filename)


def ensure_relative_path(target_path: str) -> Path:
    """
    Ensure a path is relative (not absolute).

    Raises:
        AccessDeniedException: if the path is absolute
    """
    path = Path(target_path) if target_path else Path()
    if path.is_absolute():
        raise AccessDeniedException("O caminho de destino deve ser relativo")
    return path


def ensure_within_base(file_path: Path, base_dir: Path) -> None:
    """
    Validate that file_path is contained within base_dir.

    Raises:
        AccessDeniedException: if the path escapes base_dir
    """
    try:
        resolved_path = file_path.resolve()
        resolved_base = base_dir.resolve()

        try:
            # Python 3.9+
            resolved_path.relative_to(resolved_base)
        except Exception:
            raise AccessDeniedException()
    except Exception as e:
        if isinstance(e, AccessDeniedException):
            raise
        raise AccessDeniedException(f"Invalid path: {e}")


def ensure_file_exists(file_path: Path) -> None:
    """
    Validate that file_path exists and is a file.

    Raises:
        VideoNotFoundException: if it doesn't exist
    """
    if not file_path.exists() or not file_path.is_file():
        raise VideoNotFoundException()

