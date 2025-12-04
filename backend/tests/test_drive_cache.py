"""
Tests for the Drive cache system.

Tests cover database operations, repository CRUD, and sync functionality.
"""

import pytest
import pytest_asyncio
import os
import tempfile
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

# Override settings before importing cache modules
os.environ["DRIVE_CACHE_ENABLED"] = "true"
os.environ["DRIVE_CACHE_FALLBACK_TO_API"] = "true"


class TestDriveRepository:
    """Test cases for DriveRepository CRUD operations."""

    @pytest_asyncio.fixture
    async def temp_db(self, tmp_path):
        """Create a temporary database for testing."""
        db_path = str(tmp_path / "test_cache.db")

        with patch("app.config.settings") as mock_settings:
            mock_settings.DRIVE_CACHE_DB_PATH = db_path
            mock_settings.DRIVE_CACHE_ENABLED = True
            mock_settings.DRIVE_CACHE_FALLBACK_TO_API = True

            from app.drive.cache.database import DatabaseManager

            db = DatabaseManager(db_path)
            await db.initialize()
            yield db
            await db.close()

    @pytest_asyncio.fixture
    async def repository(self, temp_db):
        """Create a repository with the temp database."""
        from app.drive.cache.repository import DriveRepository

        repo = DriveRepository()
        repo.db = temp_db
        return repo

    @pytest.mark.asyncio
    async def test_add_and_get_video(self, repository):
        """Test adding and retrieving a video."""
        # Add video
        result = await repository.add_video(
            drive_id="test_id_123",
            name="test_video.mp4",
            path="Channel/test_video.mp4",
            folder_id="folder_123",
            size=1024000,
            mime_type="video/mp4",
            created_at="2024-01-01T00:00:00Z",
            modified_at="2024-01-02T00:00:00Z",
        )
        assert result is True

        # Get video
        video = await repository.get_video("test_id_123")
        assert video is not None
        assert video["id"] == "test_id_123"
        assert video["name"] == "test_video.mp4"
        assert video["path"] == "Channel/test_video.mp4"
        assert video["size"] == 1024000

    @pytest.mark.asyncio
    async def test_get_nonexistent_video(self, repository):
        """Test getting a video that doesn't exist."""
        video = await repository.get_video("nonexistent_id")
        assert video is None

    @pytest.mark.asyncio
    async def test_get_video_by_path(self, repository):
        """Test retrieving a video by path."""
        await repository.add_video(
            drive_id="path_test_id",
            name="path_video.mp4",
            path="TestChannel/path_video.mp4",
        )

        video = await repository.get_video_by_path("TestChannel/path_video.mp4")
        assert video is not None
        assert video["id"] == "path_test_id"

    @pytest.mark.asyncio
    async def test_add_videos_batch(self, repository):
        """Test batch adding videos."""
        videos = [
            {"id": "batch_1", "name": "video1.mp4", "path": "Ch/video1.mp4"},
            {"id": "batch_2", "name": "video2.mp4", "path": "Ch/video2.mp4"},
            {"id": "batch_3", "name": "video3.mp4", "path": "Ch/video3.mp4"},
        ]

        count = await repository.add_videos_batch(videos)
        assert count == 3

        # Verify all videos were added
        all_videos = await repository.get_all_videos()
        assert len(all_videos) == 3

    @pytest.mark.asyncio
    async def test_get_videos_paginated(self, repository):
        """Test paginated video listing."""
        # Add 5 videos
        videos = [
            {"id": f"page_{i}", "name": f"video{i}.mp4", "path": f"Ch/video{i}.mp4"}
            for i in range(5)
        ]
        await repository.add_videos_batch(videos)

        # Get first page (2 items)
        result = await repository.get_videos_paginated(page=1, limit=2)
        assert result["total"] == 5
        assert result["page"] == 1
        assert result["limit"] == 2
        assert len(result["videos"]) == 2

        # Get second page
        result2 = await repository.get_videos_paginated(page=2, limit=2)
        assert len(result2["videos"]) == 2

        # Get third page (only 1 item left)
        result3 = await repository.get_videos_paginated(page=3, limit=2)
        assert len(result3["videos"]) == 1

    @pytest.mark.asyncio
    async def test_update_video_name(self, repository):
        """Test updating video name and path."""
        await repository.add_video(
            drive_id="rename_test",
            name="old_name.mp4",
            path="Ch/old_name.mp4",
        )

        result = await repository.update_video_name(
            "rename_test", "new_name.mp4", "Ch/new_name.mp4"
        )
        assert result is True

        video = await repository.get_video("rename_test")
        assert video["name"] == "new_name.mp4"
        assert video["path"] == "Ch/new_name.mp4"

    @pytest.mark.asyncio
    async def test_mark_video_deleted(self, repository):
        """Test soft deleting a video."""
        await repository.add_video(
            drive_id="delete_test",
            name="to_delete.mp4",
            path="Ch/to_delete.mp4",
        )

        # Verify video exists
        video = await repository.get_video("delete_test")
        assert video is not None

        # Soft delete
        result = await repository.mark_video_deleted("delete_test")
        assert result is True

        # Verify video is no longer returned
        video = await repository.get_video("delete_test")
        assert video is None

    @pytest.mark.asyncio
    async def test_mark_videos_deleted_batch(self, repository):
        """Test batch soft deleting videos."""
        videos = [
            {"id": f"batch_del_{i}", "name": f"v{i}.mp4", "path": f"Ch/v{i}.mp4"}
            for i in range(3)
        ]
        await repository.add_videos_batch(videos)

        count = await repository.mark_videos_deleted_batch(
            ["batch_del_0", "batch_del_1"]
        )
        assert count == 2

        # Only one video should remain
        all_videos = await repository.get_all_videos()
        assert len(all_videos) == 1

    @pytest.mark.asyncio
    async def test_hard_delete_video(self, repository):
        """Test permanent video deletion."""
        await repository.add_video(
            drive_id="hard_del",
            name="permanent.mp4",
            path="Ch/permanent.mp4",
        )

        result = await repository.hard_delete_video("hard_del")
        assert result is True

        # Verify complete removal
        video = await repository.get_video("hard_del")
        assert video is None

    @pytest.mark.asyncio
    async def test_get_all_drive_ids(self, repository):
        """Test getting all cached video IDs."""
        videos = [
            {"id": f"id_{i}", "name": f"v{i}.mp4", "path": f"Ch/v{i}.mp4"}
            for i in range(3)
        ]
        await repository.add_videos_batch(videos)

        ids = await repository.get_all_drive_ids()
        assert len(ids) == 3
        assert "id_0" in ids
        assert "id_1" in ids
        assert "id_2" in ids


class TestFolderOperations:
    """Test cases for folder operations."""

    @pytest_asyncio.fixture
    async def temp_db(self, tmp_path):
        """Create a temporary database for testing."""
        db_path = str(tmp_path / "test_cache.db")

        with patch("app.config.settings") as mock_settings:
            mock_settings.DRIVE_CACHE_DB_PATH = db_path
            mock_settings.DRIVE_CACHE_ENABLED = True

            from app.drive.cache.database import DatabaseManager

            db = DatabaseManager(db_path)
            await db.initialize()
            yield db
            await db.close()

    @pytest_asyncio.fixture
    async def repository(self, temp_db):
        """Create a repository with the temp database."""
        from app.drive.cache.repository import DriveRepository

        repo = DriveRepository()
        repo.db = temp_db
        return repo

    @pytest.mark.asyncio
    async def test_add_and_get_folder(self, repository):
        """Test adding and retrieving a folder."""
        result = await repository.add_folder(
            drive_id="folder_123",
            name="TestChannel",
            full_path="TestChannel",
            parent_id=None,
        )
        assert result is True

        folder = await repository.get_folder("folder_123")
        assert folder is not None
        assert folder["name"] == "TestChannel"

    @pytest.mark.asyncio
    async def test_get_folder_by_path(self, repository):
        """Test getting folder by path."""
        await repository.add_folder(
            drive_id="path_folder",
            name="SubFolder",
            full_path="Parent/SubFolder",
        )

        folder = await repository.get_folder_by_path("Parent/SubFolder")
        assert folder is not None
        assert folder["drive_id"] == "path_folder"

    @pytest.mark.asyncio
    async def test_add_folders_batch(self, repository):
        """Test batch adding folders."""
        folders = [
            {"id": "f1", "name": "Folder1", "full_path": "Folder1"},
            {"id": "f2", "name": "Folder2", "full_path": "Folder2"},
        ]

        count = await repository.add_folders_batch(folders)
        assert count == 2


class TestSyncMetadata:
    """Test cases for sync metadata operations."""

    @pytest_asyncio.fixture
    async def temp_db(self, tmp_path):
        """Create a temporary database for testing."""
        db_path = str(tmp_path / "test_cache.db")

        with patch("app.config.settings") as mock_settings:
            mock_settings.DRIVE_CACHE_DB_PATH = db_path
            mock_settings.DRIVE_CACHE_ENABLED = True

            from app.drive.cache.database import DatabaseManager

            db = DatabaseManager(db_path)
            await db.initialize()
            yield db
            await db.close()

    @pytest_asyncio.fixture
    async def repository(self, temp_db):
        """Create a repository with the temp database."""
        from app.drive.cache.repository import DriveRepository

        repo = DriveRepository()
        repo.db = temp_db
        return repo

    @pytest.mark.asyncio
    async def test_get_sync_metadata(self, repository):
        """Test getting sync metadata."""
        meta = await repository.get_sync_metadata()
        assert isinstance(meta, dict)

    @pytest.mark.asyncio
    async def test_update_sync_metadata(self, repository):
        """Test updating sync metadata."""
        timestamp = datetime.utcnow().isoformat()

        await repository.update_sync_metadata(
            last_full_sync_at=timestamp,
            total_videos=100,
        )

        meta = await repository.get_sync_metadata()
        assert meta["last_full_sync_at"] == timestamp
        assert meta["total_videos"] == 100

    @pytest.mark.asyncio
    async def test_sync_in_progress_flag(self, repository):
        """Test sync in progress flag."""
        # Initially not in progress
        in_progress = await repository.is_sync_in_progress()
        assert in_progress is False

        # Set in progress
        await repository.set_sync_in_progress(True)
        in_progress = await repository.is_sync_in_progress()
        assert in_progress is True

        # Clear flag
        await repository.set_sync_in_progress(False)
        in_progress = await repository.is_sync_in_progress()
        assert in_progress is False


class TestCacheStats:
    """Test cases for cache statistics."""

    @pytest_asyncio.fixture
    async def temp_db(self, tmp_path):
        """Create a temporary database for testing."""
        db_path = str(tmp_path / "test_cache.db")

        with patch("app.config.settings") as mock_settings:
            mock_settings.DRIVE_CACHE_DB_PATH = db_path
            mock_settings.DRIVE_CACHE_ENABLED = True

            from app.drive.cache.database import DatabaseManager

            db = DatabaseManager(db_path)
            await db.initialize()
            yield db
            await db.close()

    @pytest_asyncio.fixture
    async def repository(self, temp_db):
        """Create a repository with the temp database."""
        from app.drive.cache.repository import DriveRepository

        repo = DriveRepository()
        repo.db = temp_db
        return repo

    @pytest.mark.asyncio
    async def test_get_stats_empty(self, repository):
        """Test stats with empty cache."""
        stats = await repository.get_stats()

        assert stats["video_count"] == 0
        assert stats["folder_count"] == 0
        assert stats["deleted_count"] == 0
        assert stats["total_size_bytes"] == 0

    @pytest.mark.asyncio
    async def test_get_stats_with_data(self, repository):
        """Test stats with data."""
        # Add videos
        await repository.add_video(
            drive_id="v1", name="v1.mp4", path="Ch/v1.mp4", size=1000
        )
        await repository.add_video(
            drive_id="v2", name="v2.mp4", path="Ch/v2.mp4", size=2000
        )

        # Add folder
        await repository.add_folder(
            drive_id="f1", name="Channel", full_path="Channel"
        )

        # Soft delete one video
        await repository.mark_video_deleted("v1")

        stats = await repository.get_stats()

        assert stats["video_count"] == 1  # Only non-deleted
        assert stats["folder_count"] == 1
        assert stats["deleted_count"] == 1
        assert stats["total_size_bytes"] == 2000  # Only non-deleted

    @pytest.mark.asyncio
    async def test_clear_all(self, repository):
        """Test clearing all cache data."""
        # Add some data
        await repository.add_video(
            drive_id="v1", name="v1.mp4", path="Ch/v1.mp4"
        )
        await repository.add_folder(
            drive_id="f1", name="Channel", full_path="Channel"
        )

        # Clear all
        await repository.clear_all()

        stats = await repository.get_stats()
        assert stats["video_count"] == 0
        assert stats["folder_count"] == 0


class TestDatabaseManager:
    """Test cases for DatabaseManager."""

    @pytest.mark.asyncio
    async def test_initialize_creates_tables(self, tmp_path):
        """Test that initialization creates required tables."""
        db_path = str(tmp_path / "test_init.db")

        from app.drive.cache.database import DatabaseManager

        db = DatabaseManager(db_path)
        await db.initialize()

        # Verify tables exist by querying them
        async with db.connection() as conn:
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in await cursor.fetchall()]

        assert "videos" in tables
        assert "folders" in tables
        assert "sync_metadata" in tables

        await db.close()

    @pytest.mark.asyncio
    async def test_wal_mode_enabled(self, tmp_path):
        """Test that WAL mode is enabled."""
        db_path = str(tmp_path / "test_wal.db")

        from app.drive.cache.database import DatabaseManager

        db = DatabaseManager(db_path)
        await db.initialize()

        async with db.connection() as conn:
            cursor = await conn.execute("PRAGMA journal_mode")
            mode = (await cursor.fetchone())[0]

        assert mode.lower() == "wal"

        await db.close()

    @pytest.mark.asyncio
    async def test_database_file_created(self, tmp_path):
        """Test that database file is created."""
        db_path = str(tmp_path / "test_create.db")

        from app.drive.cache.database import DatabaseManager

        db = DatabaseManager(db_path)
        await db.initialize()

        assert os.path.exists(db_path)

        await db.close()
