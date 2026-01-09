"""
Input validation utilities for the application.

Provides URL validation, filename sanitization, and other input validation functions.
"""
import re
from typing import Optional, Sequence, Tuple
from urllib.parse import urlparse

from app.core.logging import get_module_logger
from app.core.exceptions import InvalidRequestException

logger = get_module_logger("validators")


# Allowed YouTube domains
YOUTUBE_DOMAINS = {
    'youtube.com',
    'www.youtube.com',
    'youtu.be',
    'm.youtube.com',
    'music.youtube.com',
}

# Characters not allowed in filenames (Windows + Unix restrictions)
UNSAFE_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

# Path traversal patterns
PATH_TRAVERSAL_PATTERNS = re.compile(r'(^|[/\\])\.\.([/\\]|$)')


class URLValidationError(ValueError):
    """Raised when URL validation fails."""
    pass


class FilenameValidationError(ValueError):
    """Raised when filename validation fails."""
    pass


def validate_url(url: str) -> str:
    """
    Validate that a URL is properly formatted.

    Args:
        url: The URL to validate

    Returns:
        The validated URL (stripped of whitespace)

    Raises:
        URLValidationError: If the URL is invalid
    """
    if not url or not url.strip():
        raise URLValidationError("URL cannot be empty")

    url = url.strip()

    try:
        parsed = urlparse(url)

        if not parsed.scheme:
            raise URLValidationError("URL must include a scheme (http:// or https://)")

        if parsed.scheme not in ('http', 'https'):
            raise URLValidationError(f"Invalid URL scheme: {parsed.scheme}")

        if not parsed.netloc:
            raise URLValidationError("URL must include a domain")

        return url

    except Exception as e:
        if isinstance(e, URLValidationError):
            raise
        raise URLValidationError(f"Invalid URL format: {e}")


def validate_youtube_url(url: str) -> str:
    """
    Validate that a URL is a valid YouTube URL.

    Args:
        url: The URL to validate

    Returns:
        The validated URL

    Raises:
        URLValidationError: If the URL is not a valid YouTube URL
    """
    url = validate_url(url)
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # Remove www. prefix for comparison
    domain_clean = domain.lstrip('www.')

    if domain not in YOUTUBE_DOMAINS and domain_clean not in YOUTUBE_DOMAINS:
        raise URLValidationError(
            f"URL must be from YouTube. Got: {domain}"
        )

    return url


def detect_url_type(url: str) -> str:
    """
    Detect whether a URL is a video, playlist, or channel.

    Args:
        url: The URL to analyze

    Returns:
        One of: 'video', 'playlist', 'channel', 'unknown'
    """
    try:
        parsed = urlparse(url)
        path = parsed.path.lower()
        query = parsed.query.lower()

        # Playlist detection
        if 'list=' in query and 'v=' not in query:
            return 'playlist'

        # Video detection
        if 'v=' in query or '/watch' in path:
            return 'video'

        # youtu.be short URLs are videos
        if 'youtu.be' in parsed.netloc:
            return 'video'

        # Channel detection
        if '/channel/' in path or '/c/' in path or '/@' in path:
            return 'channel'

        return 'unknown'

    except Exception:
        return 'unknown'


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """
    Sanitize a filename by removing or replacing unsafe characters.

    Args:
        filename: The filename to sanitize
        replacement: Character to replace unsafe chars with

    Returns:
        The sanitized filename

    Raises:
        FilenameValidationError: If filename is empty after sanitization
    """
    if not filename:
        raise FilenameValidationError("Filename cannot be empty")

    # Remove path traversal attempts
    filename = filename.replace('..', '')
    filename = filename.replace('/', replacement)
    filename = filename.replace('\\', replacement)

    # Replace unsafe characters
    filename = UNSAFE_FILENAME_CHARS.sub(replacement, filename)

    # Remove leading/trailing whitespace and dots
    filename = filename.strip(' .')

    # Collapse multiple replacements
    while replacement + replacement in filename:
        filename = filename.replace(replacement + replacement, replacement)

    if not filename:
        raise FilenameValidationError("Filename is empty after sanitization")

    return filename


def validate_path_safe(path: str) -> str:
    """
    Validate that a path doesn't contain path traversal attempts.

    Args:
        path: The path to validate

    Returns:
        The validated path

    Raises:
        ValueError: If path contains traversal attempts
    """
    if not path:
        return ""

    if PATH_TRAVERSAL_PATTERNS.search(path):
        logger.warning(f"Path traversal attempt detected: {path}")
        raise ValueError("Path traversal not allowed")

    # Check for absolute paths
    if path.startswith('/') or (len(path) > 1 and path[1] == ':'):
        raise ValueError("Absolute paths not allowed")

    return path


def validate_batch_items(
    items: Sequence[object],
    *,
    list_label: str,
    item_label: str,
    max_items: int = 100,
) -> None:
    if not items:
        raise InvalidRequestException(f"{list_label} list cannot be empty")
    if len(items) > max_items:
        raise InvalidRequestException(
            f"Cannot delete more than {max_items} {item_label} at once"
        )


def validate_pagination(page: int, limit: int) -> None:
    if page < 1 or limit < 1:
        raise InvalidRequestException("page and limit must be positive integers")


def validate_page(page: int) -> None:
    if page < 1:
        raise InvalidRequestException("page must be a positive integer")


def validate_page_limit(limit: int) -> None:
    if limit < 1:
        raise InvalidRequestException("limit must be a positive integer")


def validate_resolution(resolution: Optional[int]) -> Optional[int]:
    """
    Validate video resolution.

    Args:
        resolution: The resolution value (height in pixels)

    Returns:
        The validated resolution or None

    Raises:
        ValueError: If resolution is invalid
    """
    if resolution is None:
        return None

    valid_resolutions = {144, 240, 360, 480, 720, 1080, 1440, 2160, 4320}

    if resolution not in valid_resolutions:
        # Allow any positive integer up to 8K
        if resolution < 1 or resolution > 4320:
            raise ValueError(
                f"Invalid resolution: {resolution}. Must be between 1 and 4320."
            )

    return resolution


def validate_delay(delay: int, max_delay: int = 300) -> int:
    """
    Validate a delay value in seconds.

    Args:
        delay: The delay in seconds
        max_delay: Maximum allowed delay

    Returns:
        The validated delay

    Raises:
        ValueError: If delay is invalid
    """
    if delay < 0:
        raise ValueError("Delay cannot be negative")

    if delay > max_delay:
        raise ValueError(f"Delay cannot exceed {max_delay} seconds")

    return delay


def validate_batch_size(batch_size: Optional[int]) -> Optional[int]:
    """
    Validate batch size for downloads.

    Args:
        batch_size: Number of videos per batch

    Returns:
        The validated batch size or None

    Raises:
        ValueError: If batch size is invalid
    """
    if batch_size is None:
        return None

    if batch_size < 1:
        raise ValueError("Batch size must be at least 1")

    if batch_size > 100:
        raise ValueError("Batch size cannot exceed 100")

    return batch_size
