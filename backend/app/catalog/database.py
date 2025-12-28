"""
SQLite database utilities for the catalog.

This module intentionally uses the standard library `sqlite3` (sync) and runs
heavy operations via `asyncio.to_thread` at the call site when needed.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from app.config import settings
from app.core.logging import get_module_logger

logger = get_module_logger("catalog.db")

SCHEMA_VERSION = 1

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS catalog_state (
    scope TEXT PRIMARY KEY,
    version INTEGER NOT NULL,
    last_imported_at TEXT,
    last_published_at TEXT,
    drive_catalog_file_id TEXT,
    drive_catalog_etag TEXT,
    drive_catalog_revision TEXT
);

CREATE TABLE IF NOT EXISTS videos (
    video_uid TEXT PRIMARY KEY,
    location TEXT NOT NULL,
    source TEXT NOT NULL,
    title TEXT,
    channel TEXT,
    duration_seconds INTEGER,
    created_at TEXT,
    modified_at TEXT,
    status TEXT NOT NULL,
    extra_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_videos_location_modified ON videos(location, modified_at DESC);
CREATE INDEX IF NOT EXISTS idx_videos_location_title ON videos(location, title);
CREATE INDEX IF NOT EXISTS idx_videos_channel ON videos(channel);

CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_uid TEXT NOT NULL,
    location TEXT NOT NULL,
    kind TEXT NOT NULL,
    local_path TEXT,
    drive_file_id TEXT,
    mime_type TEXT,
    size_bytes INTEGER,
    hash TEXT,
    extra_json TEXT,
    FOREIGN KEY (video_uid) REFERENCES videos(video_uid) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_assets_video_kind ON assets(video_uid, kind);
CREATE INDEX IF NOT EXISTS idx_assets_location_kind ON assets(location, kind);
CREATE UNIQUE INDEX IF NOT EXISTS idx_assets_drive_file_id ON assets(drive_file_id);

PRAGMA user_version = 1;
"""


def _ensure_parent_dir(db_path: str) -> None:
    if db_path == ":memory:":
        return
    Path(db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


class CatalogDatabase:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or settings.catalog_db_path
        self._initialized = False
        self._memory_con: Optional[sqlite3.Connection] = None

    def initialize(self) -> None:
        if self._initialized:
            return

        if self.db_path != ":memory:":
            _ensure_parent_dir(self.db_path)

        con = sqlite3.connect(self.db_path, check_same_thread=False)
        try:
            con.execute("PRAGMA journal_mode=WAL")
            con.execute("PRAGMA foreign_keys=ON")
            con.executescript(SCHEMA_SQL)
            con.commit()
        finally:
            if self.db_path == ":memory:":
                self._memory_con = con
            else:
                con.close()

        self._initialized = True
        logger.info(f"Catalog database initialized: {self.db_path}")

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        if not self._initialized:
            self.initialize()

        if self.db_path == ":memory:":
            assert self._memory_con is not None
            con = self._memory_con
            con.row_factory = sqlite3.Row
            con.execute("PRAGMA foreign_keys=ON")
            yield con
            return

        con = sqlite3.connect(self.db_path, check_same_thread=False)
        try:
            con.row_factory = sqlite3.Row
            con.execute("PRAGMA foreign_keys=ON")
            yield con
        finally:
            con.close()


_db: Optional[CatalogDatabase] = None


def get_catalog_db() -> CatalogDatabase:
    global _db
    if _db is None:
        _db = CatalogDatabase()
    return _db
