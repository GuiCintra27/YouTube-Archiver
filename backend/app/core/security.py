"""
Security utilities for path validation and sanitization
"""
from pathlib import Path
from urllib.parse import unquote, quote

from .exceptions import AccessDeniedException, VideoNotFoundException


def validate_path_within_base(file_path: Path, base_dir: Path) -> None:
    """
    Validates that a file path is within the base directory.
    Raises AccessDeniedException if not.
    """
    try:
        resolved_path = file_path.resolve()
        resolved_base = base_dir.resolve()

        if not str(resolved_path).startswith(str(resolved_base)):
            raise AccessDeniedException()
    except Exception as e:
        if isinstance(e, AccessDeniedException):
            raise
        raise AccessDeniedException(f"Invalid path: {e}")


def validate_file_exists(file_path: Path) -> None:
    """
    Validates that a file exists.
    Raises VideoNotFoundException if not.
    """
    if not file_path.exists() or not file_path.is_file():
        raise VideoNotFoundException()


def sanitize_path(path: str) -> str:
    """
    Sanitizes a URL-encoded path.
    """
    return unquote(path)


def encode_filename_for_header(filename: str) -> str:
    """
    Encodes a filename for use in HTTP headers (RFC 5987).
    """
    return quote(filename)


def get_safe_relative_path(target_path: str) -> Path:
    """
    Returns a safe relative path, validating it's not absolute.
    """
    path = Path(target_path) if target_path else Path()

    if path.is_absolute():
        raise AccessDeniedException("O caminho de destino deve ser relativo")

    return path
