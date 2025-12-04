"""
Synchronization logic for Drive cache.

Handles full sync (rebuild), incremental sync (updates), and real-time sync.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Set

from app.config import settings
from app.core.logging import get_module_logger
from .database import get_database
from .repository import get_repository

logger = get_module_logger("drive.cache.sync")


@dataclass
class SyncResult:
    """Result of a sync operation."""

    success: bool
    added: int = 0
    updated: int = 0
    deleted: int = 0
    errors: int = 0
    duration_seconds: float = 0.0
    message: str = ""

    @property
    def changes_detected(self) -> bool:
        """Check if any changes were made."""
        return self.added > 0 or self.updated > 0 or self.deleted > 0


async def full_sync() -> SyncResult:
    """
    Perform a full synchronization from Drive to cache.

    Clears existing cache and rebuilds from Drive API.
    Should be used for:
    - First-time sync
    - Manual rebuild
    - Recovery from corruption

    Returns:
        SyncResult with statistics
    """
    start_time = datetime.utcnow()
    repo = get_repository()

    # Check if sync already in progress
    if await repo.is_sync_in_progress():
        logger.warning("Full sync requested but sync already in progress")
        return SyncResult(
            success=False,
            message="Sync already in progress",
        )

    try:
        # Set sync in progress
        await repo.set_sync_in_progress(True)
        logger.info("Starting full cache sync from Drive")

        # Import manager here to avoid circular imports
        from app.drive.manager import drive_manager

        if not drive_manager.is_authenticated():
            return SyncResult(
                success=False,
                message="Drive not authenticated",
            )

        # Get videos from Drive API
        logger.debug("Fetching videos from Drive API...")
        drive_videos = drive_manager.list_videos()

        if not drive_videos:
            logger.info("No videos found in Drive")
            # Clear cache since Drive is empty
            db = get_database()
            await db.clear()
            await repo.update_sync_metadata(
                last_full_sync_at=datetime.utcnow().isoformat(),
                total_videos=0,
                total_size_bytes=0,
            )
            return SyncResult(
                success=True,
                deleted=await repo.get_video_count(),
                message="Drive is empty, cache cleared",
            )

        # Clear existing videos (will be replaced)
        db = get_database()
        await db.clear()

        # Add all videos to cache
        added_count = await repo.add_videos_batch(drive_videos)

        # Calculate total size
        total_size = sum(v.get("size", 0) for v in drive_videos)

        # Update sync metadata
        await repo.update_sync_metadata(
            last_full_sync_at=datetime.utcnow().isoformat(),
            total_videos=added_count,
            total_size_bytes=total_size,
        )

        duration = (datetime.utcnow() - start_time).total_seconds()

        logger.info(
            f"Full sync completed: {added_count} videos cached in {duration:.2f}s"
        )

        return SyncResult(
            success=True,
            added=added_count,
            duration_seconds=duration,
            message=f"Full sync completed: {added_count} videos",
        )

    except Exception as e:
        logger.error(f"Full sync failed: {e}", exc_info=True)
        return SyncResult(
            success=False,
            errors=1,
            message=f"Sync failed: {str(e)}",
        )

    finally:
        # Clear sync in progress flag
        await repo.set_sync_in_progress(False)


async def incremental_sync() -> SyncResult:
    """
    Perform an incremental sync - only fetch changes since last sync.

    Uses modifiedTime to detect changes.
    More efficient than full sync for regular updates.

    Returns:
        SyncResult with statistics
    """
    start_time = datetime.utcnow()
    repo = get_repository()

    # Check if sync already in progress
    if await repo.is_sync_in_progress():
        logger.debug("Incremental sync skipped: sync already in progress")
        return SyncResult(
            success=False,
            message="Sync already in progress",
        )

    try:
        await repo.set_sync_in_progress(True)

        # Import manager here to avoid circular imports
        from app.drive.manager import drive_manager

        if not drive_manager.is_authenticated():
            return SyncResult(
                success=False,
                message="Drive not authenticated",
            )

        # Get last sync time
        metadata = await repo.get_sync_metadata()
        last_sync = metadata.get("last_incremental_sync_at") or metadata.get(
            "last_full_sync_at"
        )

        # If no previous sync, do a full sync instead
        if not last_sync:
            logger.info("No previous sync found, performing full sync")
            await repo.set_sync_in_progress(False)
            return await full_sync()

        logger.debug(f"Starting incremental sync since {last_sync}")

        # Get current videos from Drive
        drive_videos = drive_manager.list_videos()

        if not drive_videos:
            # Drive is empty - mark all cached as deleted
            cached_ids = await repo.get_all_drive_ids()
            if cached_ids:
                deleted_count = await repo.mark_videos_deleted_batch(cached_ids)
                await repo.update_sync_metadata(
                    last_incremental_sync_at=datetime.utcnow().isoformat(),
                    total_videos=0,
                )
                return SyncResult(
                    success=True,
                    deleted=deleted_count,
                    message="All videos removed from Drive",
                )
            return SyncResult(
                success=True,
                message="No changes detected",
            )

        # Get cached video IDs for comparison
        cached_ids: Set[str] = set(await repo.get_all_drive_ids())
        drive_ids: Set[str] = {v.get("id") for v in drive_videos}

        added = 0
        updated = 0
        deleted = 0

        # Find videos to add/update
        videos_to_upsert = []
        for video in drive_videos:
            video_id = video.get("id")
            video_modified = video.get("modified_at", "")

            if video_id not in cached_ids:
                # New video
                videos_to_upsert.append(video)
                added += 1
            else:
                # Check if modified
                cached_video = await repo.get_video(video_id)
                if cached_video:
                    cached_modified = cached_video.get("modified_at", "")
                    if video_modified > cached_modified:
                        videos_to_upsert.append(video)
                        updated += 1

        # Add/update videos in batch
        if videos_to_upsert:
            await repo.add_videos_batch(videos_to_upsert)

        # Find videos to mark as deleted (in cache but not in Drive)
        deleted_ids = cached_ids - drive_ids
        if deleted_ids:
            deleted = await repo.mark_videos_deleted_batch(list(deleted_ids))

        # Update metadata
        total_videos = len(drive_ids)
        total_size = sum(v.get("size", 0) for v in drive_videos)

        await repo.update_sync_metadata(
            last_incremental_sync_at=datetime.utcnow().isoformat(),
            total_videos=total_videos,
            total_size_bytes=total_size,
        )

        duration = (datetime.utcnow() - start_time).total_seconds()

        if added or updated or deleted:
            logger.info(
                f"Incremental sync: +{added} ~{updated} -{deleted} in {duration:.2f}s"
            )
        else:
            logger.debug(f"Incremental sync: no changes ({duration:.2f}s)")

        return SyncResult(
            success=True,
            added=added,
            updated=updated,
            deleted=deleted,
            duration_seconds=duration,
            message=f"Sync: +{added} ~{updated} -{deleted}",
        )

    except Exception as e:
        logger.error(f"Incremental sync failed: {e}", exc_info=True)
        return SyncResult(
            success=False,
            errors=1,
            message=f"Sync failed: {str(e)}",
        )

    finally:
        await repo.set_sync_in_progress(False)


# ==================== REAL-TIME SYNC FUNCTIONS ====================
# These are called after individual operations in manager.py


async def sync_video_added(
    drive_id: str,
    name: str,
    path: str,
    size: int = 0,
    created_at: Optional[str] = None,
    modified_at: Optional[str] = None,
    thumbnail_link: Optional[str] = None,
    custom_thumbnail_id: Optional[str] = None,
) -> bool:
    """
    Add a single video to cache after upload.

    Called from manager.py after successful upload.

    Returns:
        True if successful
    """
    if not settings.DRIVE_CACHE_ENABLED:
        return True

    try:
        repo = get_repository()
        await repo.add_video(
            drive_id=drive_id,
            name=name,
            path=path,
            size=size,
            created_at=created_at,
            modified_at=modified_at,
            thumbnail_link=thumbnail_link,
            custom_thumbnail_id=custom_thumbnail_id,
        )
        logger.debug(f"Real-time sync: added video {name}")
        return True
    except Exception as e:
        logger.error(f"Failed to sync video addition: {e}")
        return False


async def sync_video_deleted(drive_id: str) -> bool:
    """
    Mark a video as deleted in cache.

    Called from manager.py after successful deletion.

    Returns:
        True if successful
    """
    if not settings.DRIVE_CACHE_ENABLED:
        return True

    try:
        repo = get_repository()
        await repo.mark_video_deleted(drive_id)
        logger.debug(f"Real-time sync: marked video deleted {drive_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to sync video deletion: {e}")
        return False


async def sync_video_renamed(
    drive_id: str, new_name: str, new_path: str
) -> bool:
    """
    Update video name in cache after rename.

    Called from manager.py after successful rename.

    Returns:
        True if successful
    """
    if not settings.DRIVE_CACHE_ENABLED:
        return True

    try:
        repo = get_repository()
        await repo.update_video_name(drive_id, new_name, new_path)
        logger.debug(f"Real-time sync: renamed video to {new_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to sync video rename: {e}")
        return False


async def sync_thumbnail_updated(
    drive_id: str, custom_thumbnail_id: str
) -> bool:
    """
    Update video thumbnail ID in cache.

    Called from manager.py after thumbnail update.

    Returns:
        True if successful
    """
    if not settings.DRIVE_CACHE_ENABLED:
        return True

    try:
        repo = get_repository()
        await repo.update_video_thumbnail(drive_id, custom_thumbnail_id)
        logger.debug(f"Real-time sync: updated thumbnail for {drive_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to sync thumbnail update: {e}")
        return False


async def ensure_cache_initialized() -> bool:
    """
    Ensure cache is initialized with data.

    If cache is empty and Drive is authenticated, triggers full sync.
    Called on first video list request.

    Returns:
        True if cache has data or sync was triggered
    """
    if not settings.DRIVE_CACHE_ENABLED:
        return False

    try:
        repo = get_repository()

        # Check if we have cached data
        if await repo.has_cached_videos():
            return True

        # No cached data - check if we should sync
        from app.drive.manager import drive_manager

        if not drive_manager.is_authenticated():
            return False

        logger.info("Cache empty, triggering initial full sync")
        result = await full_sync()
        return result.success

    except Exception as e:
        logger.error(f"Failed to ensure cache initialized: {e}")
        return False
