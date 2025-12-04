"""
Drive Cache Module

SQLite-based cache for Google Drive video metadata.
Provides fast local lookups instead of API calls.
"""

from .database import DatabaseManager, get_database, init_database
from .repository import DriveRepository, get_repository
from .sync import (
    SyncResult,
    full_sync,
    incremental_sync,
    sync_video_added,
    sync_video_deleted,
    sync_video_renamed,
    sync_thumbnail_updated,
    ensure_cache_initialized,
)
from .background import (
    run_cache_sync_loop,
    initialize_cache_on_startup,
    trigger_initial_sync_if_authenticated,
    shutdown_cache,
)

__all__ = [
    # Database
    "DatabaseManager",
    "get_database",
    "init_database",
    # Repository
    "DriveRepository",
    "get_repository",
    # Sync
    "SyncResult",
    "full_sync",
    "incremental_sync",
    "sync_video_added",
    "sync_video_deleted",
    "sync_video_renamed",
    "sync_thumbnail_updated",
    "ensure_cache_initialized",
    # Background
    "run_cache_sync_loop",
    "initialize_cache_on_startup",
    "trigger_initial_sync_if_authenticated",
    "shutdown_cache",
]
