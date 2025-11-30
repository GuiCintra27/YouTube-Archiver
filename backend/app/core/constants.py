"""
Centralized constants for the YT-Archiver application.

This module contains all static constants used across the application,
organized by category for easy maintenance and reference.
"""
from enum import Enum
from typing import Dict, Set, List, FrozenSet


# =============================================================================
# File Extensions
# =============================================================================

class FileExtensions:
    """File extension constants grouped by type."""

    VIDEO: FrozenSet[str] = frozenset({
        '.mp4', '.mkv', '.webm', '.avi', '.mov', '.flv', '.wmv', '.m4v'
    })

    AUDIO: FrozenSet[str] = frozenset({
        '.mp3', '.m4a', '.wav', '.flac', '.opus', '.ogg', '.aac'
    })

    IMAGE: FrozenSet[str] = frozenset({
        '.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'
    })

    SUBTITLE: FrozenSet[str] = frozenset({
        '.srt', '.vtt', '.ass', '.sub', '.ssa'
    })

    METADATA: FrozenSet[str] = frozenset({
        '.json', '.info.json', '.description', '.txt'
    })

    THUMBNAIL: List[str] = ['.jpg', '.jpeg', '.png', '.webp']

    # All supported media extensions
    ALL_MEDIA: FrozenSet[str] = VIDEO | AUDIO | IMAGE


# =============================================================================
# MIME Types
# =============================================================================

class MimeTypes:
    """MIME type mappings for different file types."""

    VIDEO: Dict[str, str] = {
        '.mp4': 'video/mp4',
        '.webm': 'video/webm',
        '.mkv': 'video/x-matroska',
        '.avi': 'video/x-msvideo',
        '.mov': 'video/quicktime',
        '.flv': 'video/x-flv',
        '.wmv': 'video/x-ms-wmv',
        '.m4v': 'video/x-m4v',
    }

    AUDIO: Dict[str, str] = {
        '.mp3': 'audio/mpeg',
        '.m4a': 'audio/mp4',
        '.wav': 'audio/wav',
        '.flac': 'audio/flac',
        '.opus': 'audio/opus',
        '.ogg': 'audio/ogg',
        '.aac': 'audio/aac',
    }

    IMAGE: Dict[str, str] = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.webp': 'image/webp',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
    }

    @classmethod
    def get(cls, extension: str, default: str = 'application/octet-stream') -> str:
        """Get MIME type for any supported extension."""
        ext = extension.lower()
        return (
            cls.VIDEO.get(ext) or
            cls.AUDIO.get(ext) or
            cls.IMAGE.get(ext) or
            default
        )


# =============================================================================
# Job Status
# =============================================================================

class JobStatus(str, Enum):
    """Possible status values for download jobs."""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"

    @classmethod
    def is_active(cls, status: str) -> bool:
        """Check if job is still active (can be cancelled)."""
        return status in {cls.PENDING.value, cls.DOWNLOADING.value}

    @classmethod
    def is_finished(cls, status: str) -> bool:
        """Check if job has finished (any final state)."""
        return status in {cls.COMPLETED.value, cls.ERROR.value, cls.CANCELLED.value}


# =============================================================================
# Streaming Constants
# =============================================================================

class StreamingConfig:
    """Constants for video/audio streaming."""

    # Chunk sizes in bytes
    STREAM_CHUNK_SIZE: int = 8 * 1024         # 8 KB for streaming responses
    UPLOAD_CHUNK_SIZE: int = 8 * 1024 * 1024  # 8 MB for uploads
    READ_BUFFER_SIZE: int = 64 * 1024         # 64 KB for file reading

    # Range request defaults
    DEFAULT_RANGE_SIZE: int = 1024 * 1024     # 1 MB default range


# =============================================================================
# Download Constants
# =============================================================================

class DownloadDefaults:
    """Default values for download operations."""

    # Quality/Format
    FORMAT: str = "bv*+ba/b"
    MAX_RESOLUTION: int = 1080

    # Subtitles
    SUBTITLE_LANGUAGES: str = "pt,en"

    # Performance
    CONCURRENT_FRAGMENTS: int = 10
    MAX_CONCURRENT_FRAGMENTS: int = 50

    # Anti-ban delays (seconds)
    MIN_DELAY: int = 0
    MAX_DELAY: int = 300
    MAX_BATCH_SIZE: int = 100
    MAX_BATCH_DELAY: int = 300


# =============================================================================
# Related File Patterns
# =============================================================================

class RelatedFilePatterns:
    """Patterns for finding related files (thumbnails, subtitles, etc)."""

    # File suffixes to look for when deleting a video
    SUFFIXES: List[str] = [
        '.info.json',
        '.description',
        '.jpg',
        '.jpeg',
        '.png',
        '.webp',
        '.srt',
        '.vtt',
        '.ass',
        '.en.srt',
        '.pt.srt',
        '.en.vtt',
        '.pt.vtt',
    ]


# =============================================================================
# Google Drive Constants
# =============================================================================

class DriveConfig:
    """Constants for Google Drive integration."""

    # OAuth Scopes
    SCOPES: List[str] = ['https://www.googleapis.com/auth/drive.file']

    # Folder MIME type
    FOLDER_MIME_TYPE: str = 'application/vnd.google-apps.folder'

    # API settings
    BATCH_SIZE: int = 100


# =============================================================================
# HTTP Headers
# =============================================================================

class HTTPHeaders:
    """Common HTTP header values."""

    # Cache control
    NO_CACHE: str = "no-cache"
    CACHE_1_DAY: str = "public, max-age=86400"
    CACHE_1_WEEK: str = "public, max-age=604800"

    # Connection
    KEEP_ALIVE: str = "keep-alive"


# =============================================================================
# Validation Constants
# =============================================================================

class ValidationLimits:
    """Limits for input validation."""

    # Resolution
    MIN_RESOLUTION: int = 1
    MAX_RESOLUTION: int = 4320  # 8K

    # Pagination
    MIN_PAGE: int = 1
    MIN_LIMIT: int = 1
    DEFAULT_PAGE_SIZE: int = 24

    # Path length
    MAX_FILENAME_LENGTH: int = 255
    MAX_PATH_LENGTH: int = 4096


# =============================================================================
# Backward Compatibility Exports
# =============================================================================

# These are exported for backward compatibility with existing code
VIDEO_EXTENSIONS = FileExtensions.VIDEO
AUDIO_EXTENSIONS = FileExtensions.AUDIO
IMAGE_EXTENSIONS = FileExtensions.IMAGE
SUBTITLE_EXTENSIONS = FileExtensions.SUBTITLE
THUMBNAIL_EXTENSIONS = FileExtensions.THUMBNAIL

VIDEO_MIME_TYPES = MimeTypes.VIDEO
AUDIO_MIME_TYPES = MimeTypes.AUDIO
IMAGE_MIME_TYPES = MimeTypes.IMAGE

STREAM_CHUNK_SIZE = StreamingConfig.STREAM_CHUNK_SIZE
UPLOAD_CHUNK_SIZE = StreamingConfig.UPLOAD_CHUNK_SIZE
