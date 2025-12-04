"""
Repository layer for Drive cache CRUD operations.

Provides data access methods for videos and folders tables.
All methods are async and use the DatabaseManager connection.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any

from app.core.logging import get_module_logger
from .database import get_database

logger = get_module_logger("drive.cache.repository")


class DriveRepository:
    """
    Repository for Drive cache database operations.

    Provides CRUD operations for videos and folders,
    plus specialized queries for pagination and sync.
    """

    def __init__(self):
        """Initialize repository with database manager."""
        self.db = get_database()

    # ==================== VIDEO OPERATIONS ====================

    async def add_video(
        self,
        drive_id: str,
        name: str,
        path: str,
        folder_id: Optional[str] = None,
        size: int = 0,
        mime_type: Optional[str] = None,
        created_at: Optional[str] = None,
        modified_at: Optional[str] = None,
        thumbnail_link: Optional[str] = None,
        custom_thumbnail_id: Optional[str] = None,
    ) -> bool:
        """
        Add or update a video in the cache.

        Uses INSERT OR REPLACE for upsert behavior.

        Returns:
            True if successful
        """
        cached_at = datetime.utcnow().isoformat()

        async with self.db.connection() as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO videos (
                    drive_id, name, path, folder_id, size, mime_type,
                    created_at, modified_at, thumbnail_link, custom_thumbnail_id,
                    cached_at, is_deleted
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    drive_id,
                    name,
                    path,
                    folder_id,
                    size,
                    mime_type,
                    created_at,
                    modified_at,
                    thumbnail_link,
                    custom_thumbnail_id,
                    cached_at,
                ),
            )
            await db.commit()

        logger.debug(f"Added/updated video in cache: {name}")
        return True

    async def add_videos_batch(self, videos: List[Dict[str, Any]]) -> int:
        """
        Add multiple videos in a single transaction.

        Args:
            videos: List of video dicts with keys matching add_video params

        Returns:
            Number of videos added
        """
        if not videos:
            return 0

        cached_at = datetime.utcnow().isoformat()

        async with self.db.connection() as db:
            for video in videos:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO videos (
                        drive_id, name, path, folder_id, size, mime_type,
                        created_at, modified_at, thumbnail_link, custom_thumbnail_id,
                        cached_at, is_deleted
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                    """,
                    (
                        video.get("drive_id") or video.get("id"),
                        video.get("name"),
                        video.get("path"),
                        video.get("folder_id"),
                        video.get("size", 0),
                        video.get("mime_type"),
                        video.get("created_at"),
                        video.get("modified_at"),
                        video.get("thumbnail_link") or video.get("thumbnail"),
                        video.get("custom_thumbnail_id"),
                        cached_at,
                    ),
                )
            await db.commit()

        logger.debug(f"Batch added {len(videos)} videos to cache")
        return len(videos)

    async def get_video(self, drive_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single video by Drive ID.

        Returns:
            Video dict or None if not found
        """
        async with self.db.connection() as db:
            cursor = await db.execute(
                """
                SELECT * FROM videos
                WHERE drive_id = ? AND is_deleted = 0
                """,
                (drive_id,),
            )
            row = await cursor.fetchone()

        if row:
            return self._row_to_video_dict(row)
        return None

    async def get_video_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Get a single video by path.

        Returns:
            Video dict or None if not found
        """
        async with self.db.connection() as db:
            cursor = await db.execute(
                """
                SELECT * FROM videos
                WHERE path = ? AND is_deleted = 0
                """,
                (path,),
            )
            row = await cursor.fetchone()

        if row:
            return self._row_to_video_dict(row)
        return None

    async def get_all_videos(self) -> List[Dict[str, Any]]:
        """
        Get all non-deleted videos.

        Returns:
            List of video dicts
        """
        async with self.db.connection() as db:
            cursor = await db.execute(
                """
                SELECT * FROM videos
                WHERE is_deleted = 0
                ORDER BY modified_at DESC
                """
            )
            rows = await cursor.fetchall()

        return [self._row_to_video_dict(row) for row in rows]

    async def get_videos_paginated(
        self, page: int = 1, limit: int = 24
    ) -> Dict[str, Any]:
        """
        Get paginated list of videos.

        Args:
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            Dict with total, page, limit, and videos list
        """
        offset = (page - 1) * limit

        async with self.db.connection() as db:
            # Get total count
            cursor = await db.execute(
                "SELECT COUNT(*) FROM videos WHERE is_deleted = 0"
            )
            total = (await cursor.fetchone())[0]

            # Get page of videos
            cursor = await db.execute(
                """
                SELECT * FROM videos
                WHERE is_deleted = 0
                ORDER BY modified_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
            rows = await cursor.fetchall()

        videos = [self._row_to_video_dict(row) for row in rows]

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "videos": videos,
        }

    async def update_video_name(self, drive_id: str, new_name: str, new_path: str) -> bool:
        """
        Update video name and path after rename.

        Returns:
            True if updated, False if not found
        """
        cached_at = datetime.utcnow().isoformat()

        async with self.db.connection() as db:
            cursor = await db.execute(
                """
                UPDATE videos
                SET name = ?, path = ?, cached_at = ?
                WHERE drive_id = ?
                """,
                (new_name, new_path, cached_at, drive_id),
            )
            await db.commit()

        return cursor.rowcount > 0

    async def update_video_thumbnail(
        self, drive_id: str, custom_thumbnail_id: str
    ) -> bool:
        """
        Update video's custom thumbnail ID.

        Returns:
            True if updated, False if not found
        """
        cached_at = datetime.utcnow().isoformat()

        async with self.db.connection() as db:
            cursor = await db.execute(
                """
                UPDATE videos
                SET custom_thumbnail_id = ?, cached_at = ?
                WHERE drive_id = ?
                """,
                (custom_thumbnail_id, cached_at, drive_id),
            )
            await db.commit()

        return cursor.rowcount > 0

    async def mark_video_deleted(self, drive_id: str) -> bool:
        """
        Mark a video as deleted (soft delete).

        Returns:
            True if marked, False if not found
        """
        async with self.db.connection() as db:
            cursor = await db.execute(
                """
                UPDATE videos
                SET is_deleted = 1, cached_at = ?
                WHERE drive_id = ?
                """,
                (datetime.utcnow().isoformat(), drive_id),
            )
            await db.commit()

        if cursor.rowcount > 0:
            logger.debug(f"Marked video as deleted: {drive_id}")
            return True
        return False

    async def mark_videos_deleted_batch(self, drive_ids: List[str]) -> int:
        """
        Mark multiple videos as deleted.

        Returns:
            Number of videos marked
        """
        if not drive_ids:
            return 0

        cached_at = datetime.utcnow().isoformat()

        async with self.db.connection() as db:
            # SQLite doesn't support array params, so we use placeholders
            placeholders = ",".join("?" * len(drive_ids))
            cursor = await db.execute(
                f"""
                UPDATE videos
                SET is_deleted = 1, cached_at = ?
                WHERE drive_id IN ({placeholders})
                """,
                [cached_at] + drive_ids,
            )
            await db.commit()

        logger.debug(f"Marked {cursor.rowcount} videos as deleted")
        return cursor.rowcount

    async def hard_delete_video(self, drive_id: str) -> bool:
        """
        Permanently remove a video from cache.

        Returns:
            True if deleted, False if not found
        """
        async with self.db.connection() as db:
            cursor = await db.execute(
                "DELETE FROM videos WHERE drive_id = ?", (drive_id,)
            )
            await db.commit()

        return cursor.rowcount > 0

    async def purge_deleted_videos(self) -> int:
        """
        Permanently remove all soft-deleted videos.

        Returns:
            Number of videos purged
        """
        async with self.db.connection() as db:
            cursor = await db.execute(
                "DELETE FROM videos WHERE is_deleted = 1"
            )
            await db.commit()

        logger.info(f"Purged {cursor.rowcount} deleted videos from cache")
        return cursor.rowcount

    async def get_all_drive_ids(self) -> List[str]:
        """
        Get list of all cached video Drive IDs.

        Useful for comparing with Drive API results during sync.

        Returns:
            List of drive_id strings
        """
        async with self.db.connection() as db:
            cursor = await db.execute(
                "SELECT drive_id FROM videos WHERE is_deleted = 0"
            )
            rows = await cursor.fetchall()

        return [row[0] for row in rows]

    # ==================== FOLDER OPERATIONS ====================

    async def add_folder(
        self,
        drive_id: str,
        name: str,
        full_path: str,
        parent_id: Optional[str] = None,
        created_at: Optional[str] = None,
        modified_at: Optional[str] = None,
    ) -> bool:
        """
        Add or update a folder in the cache.

        Returns:
            True if successful
        """
        cached_at = datetime.utcnow().isoformat()

        async with self.db.connection() as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO folders (
                    drive_id, name, parent_id, full_path,
                    created_at, modified_at, cached_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    drive_id,
                    name,
                    parent_id,
                    full_path,
                    created_at,
                    modified_at,
                    cached_at,
                ),
            )
            await db.commit()

        return True

    async def add_folders_batch(self, folders: List[Dict[str, Any]]) -> int:
        """
        Add multiple folders in a single transaction.

        Returns:
            Number of folders added
        """
        if not folders:
            return 0

        cached_at = datetime.utcnow().isoformat()

        async with self.db.connection() as db:
            for folder in folders:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO folders (
                        drive_id, name, parent_id, full_path,
                        created_at, modified_at, cached_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        folder.get("drive_id") or folder.get("id"),
                        folder.get("name"),
                        folder.get("parent_id"),
                        folder.get("full_path") or folder.get("path", ""),
                        folder.get("created_at"),
                        folder.get("modified_at"),
                        cached_at,
                    ),
                )
            await db.commit()

        return len(folders)

    async def get_folder(self, drive_id: str) -> Optional[Dict[str, Any]]:
        """Get a single folder by Drive ID."""
        async with self.db.connection() as db:
            cursor = await db.execute(
                "SELECT * FROM folders WHERE drive_id = ?", (drive_id,)
            )
            row = await cursor.fetchone()

        if row:
            return dict(row)
        return None

    async def get_folder_by_path(self, full_path: str) -> Optional[Dict[str, Any]]:
        """Get a folder by its full path."""
        async with self.db.connection() as db:
            cursor = await db.execute(
                "SELECT * FROM folders WHERE full_path = ?", (full_path,)
            )
            row = await cursor.fetchone()

        if row:
            return dict(row)
        return None

    async def delete_folder(self, drive_id: str) -> bool:
        """Delete a folder from cache."""
        async with self.db.connection() as db:
            cursor = await db.execute(
                "DELETE FROM folders WHERE drive_id = ?", (drive_id,)
            )
            await db.commit()

        return cursor.rowcount > 0

    # ==================== SYNC METADATA OPERATIONS ====================

    async def get_sync_metadata(self) -> Dict[str, Any]:
        """Get sync metadata."""
        async with self.db.connection() as db:
            cursor = await db.execute(
                "SELECT * FROM sync_metadata WHERE id = 1"
            )
            row = await cursor.fetchone()

        if row:
            return dict(row)
        return {}

    async def update_sync_metadata(
        self,
        last_full_sync_at: Optional[str] = None,
        last_incremental_sync_at: Optional[str] = None,
        drive_root_folder_id: Optional[str] = None,
        sync_in_progress: Optional[bool] = None,
        total_videos: Optional[int] = None,
        total_size_bytes: Optional[int] = None,
    ) -> None:
        """
        Update sync metadata fields.

        Only updates fields that are not None.
        """
        updates = []
        values = []

        if last_full_sync_at is not None:
            updates.append("last_full_sync_at = ?")
            values.append(last_full_sync_at)

        if last_incremental_sync_at is not None:
            updates.append("last_incremental_sync_at = ?")
            values.append(last_incremental_sync_at)

        if drive_root_folder_id is not None:
            updates.append("drive_root_folder_id = ?")
            values.append(drive_root_folder_id)

        if sync_in_progress is not None:
            updates.append("sync_in_progress = ?")
            values.append(1 if sync_in_progress else 0)

        if total_videos is not None:
            updates.append("total_videos = ?")
            values.append(total_videos)

        if total_size_bytes is not None:
            updates.append("total_size_bytes = ?")
            values.append(total_size_bytes)

        if not updates:
            return

        query = f"UPDATE sync_metadata SET {', '.join(updates)} WHERE id = 1"

        async with self.db.connection() as db:
            await db.execute(query, values)
            await db.commit()

    async def is_sync_in_progress(self) -> bool:
        """Check if a sync operation is currently in progress."""
        meta = await self.get_sync_metadata()
        return bool(meta.get("sync_in_progress", 0))

    async def set_sync_in_progress(self, in_progress: bool) -> None:
        """Set the sync in progress flag."""
        await self.update_sync_metadata(sync_in_progress=in_progress)

    # ==================== HELPER METHODS ====================

    def _row_to_video_dict(self, row) -> Dict[str, Any]:
        """
        Convert a database row to video dict matching DriveVideo schema.

        Maps database column names to API response format.
        """
        return {
            "id": row["drive_id"],
            "name": row["name"],
            "path": row["path"],
            "size": row["size"],
            "created_at": row["created_at"],
            "modified_at": row["modified_at"],
            "thumbnail": row["thumbnail_link"],
            "custom_thumbnail_id": row["custom_thumbnail_id"],
        }

    async def get_video_count(self) -> int:
        """Get count of non-deleted videos."""
        async with self.db.connection() as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM videos WHERE is_deleted = 0"
            )
            return (await cursor.fetchone())[0]

    async def has_cached_videos(self) -> bool:
        """Check if there are any cached videos."""
        count = await self.get_video_count()
        return count > 0

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats including video count, sync times, etc.
        """
        async with self.db.connection() as db:
            # Get video count
            cursor = await db.execute(
                "SELECT COUNT(*) FROM videos WHERE is_deleted = 0"
            )
            video_count = (await cursor.fetchone())[0]

            # Get folder count
            cursor = await db.execute("SELECT COUNT(*) FROM folders")
            folder_count = (await cursor.fetchone())[0]

            # Get deleted count
            cursor = await db.execute(
                "SELECT COUNT(*) FROM videos WHERE is_deleted = 1"
            )
            deleted_count = (await cursor.fetchone())[0]

            # Get total size
            cursor = await db.execute(
                "SELECT COALESCE(SUM(size), 0) FROM videos WHERE is_deleted = 0"
            )
            total_size = (await cursor.fetchone())[0]

            # Get sync metadata
            cursor = await db.execute(
                "SELECT * FROM sync_metadata WHERE id = 1"
            )
            meta_row = await cursor.fetchone()

        meta = dict(meta_row) if meta_row else {}

        return {
            "video_count": video_count,
            "folder_count": folder_count,
            "deleted_count": deleted_count,
            "total_size_bytes": total_size,
            "last_full_sync_at": meta.get("last_full_sync_at"),
            "last_incremental_sync_at": meta.get("last_incremental_sync_at"),
            "sync_in_progress": bool(meta.get("sync_in_progress", 0)),
        }

    async def clear_all(self) -> None:
        """
        Clear all cached data (videos and folders).

        Does not reset sync metadata.
        """
        async with self.db.connection() as db:
            await db.execute("DELETE FROM videos")
            await db.execute("DELETE FROM folders")
            await db.commit()

        logger.info("Cache cleared: all videos and folders removed")


# Singleton instance
_repository: Optional[DriveRepository] = None


def get_repository() -> DriveRepository:
    """Get the singleton repository instance."""
    global _repository
    if _repository is None:
        _repository = DriveRepository()
    return _repository
