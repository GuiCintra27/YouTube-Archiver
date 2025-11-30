"""
Type definitions and type aliases for the YT-Archiver application.

This module provides:
- Type aliases for common types
- TypedDicts for structured dictionaries
- Protocols for duck-typing interfaces
- Generic types for better type inference
"""
from typing import (
    TypedDict,
    Optional,
    Any,
    Dict,
    List,
    Callable,
    Awaitable,
    Union,
    Literal,
)
from datetime import datetime
from pathlib import Path


# =============================================================================
# Type Aliases
# =============================================================================

# Path types
PathLike = Union[str, Path]

# Callback types
ProgressCallback = Callable[[Dict[str, Any]], None]
AsyncProgressCallback = Callable[[Dict[str, Any]], Awaitable[None]]

# JSON types
JSONValue = Union[str, int, float, bool, None, List["JSONValue"], Dict[str, "JSONValue"]]
JSONDict = Dict[str, JSONValue]

# Status literals
JobStatusLiteral = Literal["pending", "downloading", "completed", "error", "cancelled"]
DownloadTypeLiteral = Literal["video", "playlist", "channel"]


# =============================================================================
# TypedDicts for Structured Data
# =============================================================================

class VideoInfo(TypedDict, total=False):
    """Type definition for video metadata."""

    id: str
    title: str
    channel: str
    path: str
    thumbnail: Optional[str]
    size: int
    created_at: str
    modified_at: str
    duration: Optional[int]
    view_count: Optional[int]
    uploader: Optional[str]


class JobProgress(TypedDict, total=False):
    """Type definition for job progress information."""

    status: str
    percent: float
    speed: Optional[str]
    eta: Optional[str]
    filename: Optional[str]
    downloaded_bytes: Optional[int]
    total_bytes: Optional[int]


class JobData(TypedDict, total=False):
    """Type definition for job data."""

    job_id: str
    status: JobStatusLiteral
    created_at: str
    completed_at: Optional[str]
    url: str
    request: Dict[str, Any]
    progress: JobProgress
    result: Optional[Dict[str, Any]]
    error: Optional[str]


class DownloadResult(TypedDict, total=False):
    """Type definition for download results."""

    status: str
    downloaded: int
    skipped: int
    errors: int
    files: List[str]
    error: Optional[str]


class PaginatedResponse(TypedDict):
    """Type definition for paginated API responses."""

    total: int
    page: int
    limit: Optional[int]
    videos: List[VideoInfo]


class DeleteResult(TypedDict):
    """Type definition for delete operation results."""

    status: str
    message: str
    deleted_files: List[str]
    removed_from_archive: bool


class SyncStatus(TypedDict):
    """Type definition for Drive sync status."""

    local_only: List[str]
    drive_only: List[str]
    synced: List[str]
    total_local: int
    total_drive: int


class DriveVideo(TypedDict, total=False):
    """Type definition for Google Drive video metadata."""

    id: str
    name: str
    mimeType: str
    size: Optional[int]
    createdTime: Optional[str]
    modifiedTime: Optional[str]
    thumbnailLink: Optional[str]
    webContentLink: Optional[str]
    parents: Optional[List[str]]


# =============================================================================
# Error Response Types
# =============================================================================

class ErrorDetail(TypedDict, total=False):
    """Type definition for error details."""

    error_code: str
    message: str
    details: Optional[Any]


# =============================================================================
# Cache Types
# =============================================================================

class CacheStats(TypedDict):
    """Type definition for cache statistics."""

    hits: int
    misses: int
    hit_rate: str
    cached_dirs: int
    ttl_seconds: float


# =============================================================================
# Configuration Types
# =============================================================================

class DownloadSettings(TypedDict, total=False):
    """Type definition for download settings."""

    out_dir: str
    archive_file: str
    fmt: str
    max_res: Optional[int]
    subs: bool
    auto_subs: bool
    sub_langs: str
    thumbnails: bool
    audio_only: bool
    limit: Optional[int]
    cookies_file: Optional[str]
    referer: Optional[str]
    origin: Optional[str]
    user_agent: str
    concurrent_fragments: int
    custom_path: Optional[str]
    file_name: Optional[str]
    archive_id: Optional[str]
    delay_between_downloads: int
    batch_size: Optional[int]
    batch_delay: int
    randomize_delay: bool
