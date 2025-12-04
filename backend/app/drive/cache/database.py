"""
Database connection and schema management for Drive cache.

Handles SQLite connection, table creation, and migrations.
Uses WAL mode for better concurrent access.
"""

import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiosqlite

from app.config import settings
from app.core.logging import get_module_logger

logger = get_module_logger("drive.cache.db")

# Current schema version - increment when schema changes
SCHEMA_VERSION = 1

# SQL schema definition
SCHEMA_SQL = """
-- Sync metadata tracking (singleton row)
CREATE TABLE IF NOT EXISTS sync_metadata (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    last_full_sync_at TEXT,
    last_incremental_sync_at TEXT,
    drive_root_folder_id TEXT,
    sync_in_progress INTEGER DEFAULT 0,
    total_videos INTEGER DEFAULT 0,
    total_size_bytes INTEGER DEFAULT 0,
    schema_version INTEGER DEFAULT 1
);

-- Initialize singleton row if not exists
INSERT OR IGNORE INTO sync_metadata (id, schema_version) VALUES (1, 1);

-- Folders cache (for efficient path resolution)
CREATE TABLE IF NOT EXISTS folders (
    drive_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    parent_id TEXT,
    full_path TEXT NOT NULL,
    created_at TEXT,
    modified_at TEXT,
    cached_at TEXT NOT NULL
);

-- Videos cache (main table)
CREATE TABLE IF NOT EXISTS videos (
    drive_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    folder_id TEXT,
    size INTEGER DEFAULT 0,
    mime_type TEXT,
    created_at TEXT,
    modified_at TEXT,
    thumbnail_link TEXT,
    custom_thumbnail_id TEXT,
    cached_at TEXT NOT NULL,
    is_deleted INTEGER DEFAULT 0
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_videos_path ON videos(path);
CREATE INDEX IF NOT EXISTS idx_videos_modified_at ON videos(modified_at);
CREATE INDEX IF NOT EXISTS idx_videos_folder_id ON videos(folder_id);
CREATE INDEX IF NOT EXISTS idx_videos_is_deleted ON videos(is_deleted);
CREATE INDEX IF NOT EXISTS idx_folders_parent_id ON folders(parent_id);
CREATE INDEX IF NOT EXISTS idx_folders_full_path ON folders(full_path);
"""


class DatabaseManager:
    """
    Manages SQLite database lifecycle, connections, and migrations.

    Uses WAL mode for better concurrent read/write access.
    Handles automatic schema creation and migration.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file. Defaults to settings.
        """
        self.db_path = db_path or settings.DRIVE_CACHE_DB_PATH
        self._initialized = False

    async def initialize(self) -> None:
        """
        Initialize database, creating tables if needed.

        Should be called once on application startup.
        Handles first-run setup and migrations.
        """
        if self._initialized:
            return

        db_exists = Path(self.db_path).exists()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Enable WAL mode for better concurrency
                await db.execute("PRAGMA journal_mode=WAL")
                await db.execute("PRAGMA foreign_keys=ON")

                if not db_exists:
                    logger.info(f"Creating new cache database: {self.db_path}")
                    await self._create_tables(db)
                else:
                    await self._check_and_migrate(db)

                await db.commit()
                self._initialized = True
                logger.info("Drive cache database initialized successfully")

        except Exception as e:
            logger.error(f"Database initialization failed: {e}", exc_info=True)
            await self._handle_corruption()

    async def _create_tables(self, db: aiosqlite.Connection) -> None:
        """Create all tables from schema."""
        await db.executescript(SCHEMA_SQL)
        logger.info("Database tables created successfully")

    async def _check_and_migrate(self, db: aiosqlite.Connection) -> None:
        """Check schema version and apply migrations if needed."""
        try:
            cursor = await db.execute(
                "SELECT schema_version FROM sync_metadata WHERE id = 1"
            )
            row = await cursor.fetchone()

            if row is None:
                # No metadata row, need to recreate
                logger.warning("No sync_metadata found, recreating tables")
                await self._create_tables(db)
                return

            current_version = row[0]

            if current_version < SCHEMA_VERSION:
                logger.info(
                    f"Migrating database from v{current_version} to v{SCHEMA_VERSION}"
                )
                await self._apply_migrations(db, current_version)

        except sqlite3.OperationalError as e:
            # Table doesn't exist or other schema issue
            logger.warning(f"Schema check failed: {e}, recreating tables")
            await self._create_tables(db)

    async def _apply_migrations(
        self, db: aiosqlite.Connection, from_version: int
    ) -> None:
        """
        Apply sequential migrations from current version to latest.

        Add new migrations here as schema evolves.
        """
        # Example migration structure:
        # if from_version < 2:
        #     await db.execute("ALTER TABLE videos ADD COLUMN duration TEXT")
        #     await db.execute("UPDATE sync_metadata SET schema_version = 2")

        # Update to latest version
        await db.execute(
            "UPDATE sync_metadata SET schema_version = ?", (SCHEMA_VERSION,)
        )
        logger.info(f"Database migrated to version {SCHEMA_VERSION}")

    async def _handle_corruption(self) -> None:
        """Handle database corruption by backing up and recreating."""
        logger.warning("Database appears corrupted, recreating...")

        corrupted_path = Path(self.db_path)
        if corrupted_path.exists():
            # Backup corrupted file with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = corrupted_path.with_suffix(f".db.corrupted_{timestamp}")
            try:
                corrupted_path.rename(backup_path)
                logger.info(f"Corrupted database backed up to: {backup_path}")
            except Exception as e:
                logger.error(f"Failed to backup corrupted database: {e}")
                corrupted_path.unlink(missing_ok=True)

        # Recreate fresh database
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            await self._create_tables(db)
            await db.commit()

        self._initialized = True
        logger.info("Database recreated successfully")

    @asynccontextmanager
    async def connection(self):
        """
        Get an async database connection context manager.

        Usage:
            async with db_manager.connection() as db:
                await db.execute(...)
        """
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            await db.execute("PRAGMA foreign_keys=ON")
            yield db

    async def close(self) -> None:
        """Close any resources. Currently a no-op since connections are context-managed."""
        self._initialized = False
        logger.debug("Database manager closed")

    async def get_stats(self) -> dict:
        """Get database statistics."""
        async with self.connection() as db:
            # Get sync metadata
            cursor = await db.execute(
                """
                SELECT
                    last_full_sync_at,
                    last_incremental_sync_at,
                    sync_in_progress,
                    total_videos,
                    total_size_bytes
                FROM sync_metadata WHERE id = 1
                """
            )
            meta = await cursor.fetchone()

            # Get actual counts
            cursor = await db.execute(
                "SELECT COUNT(*) FROM videos WHERE is_deleted = 0"
            )
            video_count = (await cursor.fetchone())[0]

            cursor = await db.execute("SELECT COUNT(*) FROM folders")
            folder_count = (await cursor.fetchone())[0]

            # Get database file size
            db_size = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0

            return {
                "database_path": self.db_path,
                "database_size_bytes": db_size,
                "video_count": video_count,
                "folder_count": folder_count,
                "last_full_sync_at": meta["last_full_sync_at"] if meta else None,
                "last_incremental_sync_at": meta["last_incremental_sync_at"] if meta else None,
                "sync_in_progress": bool(meta["sync_in_progress"]) if meta else False,
                "schema_version": SCHEMA_VERSION,
            }

    async def clear(self) -> None:
        """Clear all cached data (keeps schema)."""
        async with self.connection() as db:
            await db.execute("DELETE FROM videos")
            await db.execute("DELETE FROM folders")
            await db.execute(
                """
                UPDATE sync_metadata SET
                    last_full_sync_at = NULL,
                    last_incremental_sync_at = NULL,
                    total_videos = 0,
                    total_size_bytes = 0,
                    sync_in_progress = 0
                WHERE id = 1
                """
            )
            await db.commit()
        logger.info("Cache cleared successfully")


# Singleton instance
_db_manager: Optional[DatabaseManager] = None


def get_database() -> DatabaseManager:
    """Get the singleton database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def init_database() -> None:
    """Initialize the database on application startup."""
    db = get_database()
    await db.initialize()
