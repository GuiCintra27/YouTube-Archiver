"""
Catalog repository (data access).
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.logging import get_module_logger
from .database import CatalogDatabase, get_catalog_db

logger = get_module_logger("catalog.repository")


class CatalogRepository:
    def __init__(self, db: Optional[CatalogDatabase] = None) -> None:
        self.db = db or get_catalog_db()

    def get_counts(self) -> Dict[str, int]:
        with self.db.connection() as con:
            cursor = con.execute(
                "SELECT location, COUNT(*) AS cnt FROM videos GROUP BY location"
            )
            rows = cursor.fetchall()
        counts = {"local": 0, "drive": 0}
        for row in rows:
            counts[row["location"]] = int(row["cnt"])
        return counts

    def list_video_asset_paths(self, *, location: str) -> List[str]:
        """
        Return `assets.local_path` for video assets.

        For `location='local'`, this is the local relative path (e.g. Channel/video.mp4).
        For `location='drive'`, this is the Drive relative path (e.g. Channel/video.mp4) when populated.
        """
        with self.db.connection() as con:
            rows = con.execute(
                """
                SELECT local_path
                FROM assets
                WHERE location = ? AND kind = 'video' AND local_path IS NOT NULL
                """,
                (location,),
            ).fetchall()
        return [str(r["local_path"]) for r in rows if r["local_path"]]

    def list_drive_video_assets(self) -> List[Dict[str, str]]:
        """
        Return a list of Drive video assets containing both `path` and `file_id`.
        """
        with self.db.connection() as con:
            rows = con.execute(
                """
                SELECT local_path, drive_file_id
                FROM assets
                WHERE location = 'drive' AND kind = 'video'
                    AND local_path IS NOT NULL
                    AND drive_file_id IS NOT NULL
                """,
            ).fetchall()
        items = [
            {"path": str(r["local_path"]), "file_id": str(r["drive_file_id"])}
            for r in rows
            if r["local_path"] and r["drive_file_id"]
        ]

        # Backward-compat: older drive catalog rows stored `drive_path` only in videos.extra_json.
        if items:
            return items

        with self.db.connection() as con:
            rows2 = con.execute(
                """
                SELECT v.extra_json, a.drive_file_id
                FROM videos v
                JOIN assets a ON a.video_uid = v.video_uid AND a.location = v.location AND a.kind = 'video'
                WHERE v.location = 'drive' AND a.drive_file_id IS NOT NULL
                """,
            ).fetchall()

            recovered: List[Dict[str, str]] = []
            for r in rows2:
                try:
                    extra = json.loads(r["extra_json"]) if r["extra_json"] else {}
                except Exception:
                    extra = {}
                drive_path = extra.get("drive_path")
                drive_file_id = r["drive_file_id"]
                if not drive_path or not drive_file_id:
                    continue
                recovered.append({"path": str(drive_path), "file_id": str(drive_file_id)})

                # Best-effort backfill for future queries
                try:
                    con.execute(
                        """
                        UPDATE assets
                        SET local_path = ?
                        WHERE location = 'drive' AND kind = 'video' AND drive_file_id = ?
                        """,
                        (str(drive_path), str(drive_file_id)),
                    )
                except Exception:
                    pass
            con.commit()

        return recovered

    def find_drive_file_id_by_path(self, path: str) -> Optional[str]:
        with self.db.connection() as con:
            row = con.execute(
                """
                SELECT drive_file_id
                FROM assets
                WHERE location = 'drive' AND kind = 'video' AND local_path = ?
                LIMIT 1
                """,
                (path,),
            ).fetchone()
        return str(row["drive_file_id"]) if row and row["drive_file_id"] else None

    def get_video(self, video_uid: str) -> Dict[str, Any]:
        with self.db.connection() as con:
            row = con.execute(
                "SELECT * FROM videos WHERE video_uid = ?",
                (video_uid,),
            ).fetchone()
        return dict(row) if row else {}

    def find_drive_video_uid_by_file_id(self, file_id: str) -> Optional[str]:
        """
        Resolve a Drive video_uid by the Drive video file_id.

        We store the Drive video file_id in the assets table (kind='video').
        """
        with self.db.connection() as con:
            row = con.execute(
                """
                SELECT video_uid FROM assets
                WHERE location = 'drive' AND kind = 'video' AND drive_file_id = ?
                LIMIT 1
                """,
                (file_id,),
            ).fetchone()
        return str(row["video_uid"]) if row else None

    def get_assets(self, *, video_uid: str, location: str) -> List[Dict[str, Any]]:
        with self.db.connection() as con:
            rows = con.execute(
                """
                SELECT * FROM assets
                WHERE video_uid = ? AND location = ?
                ORDER BY id ASC
                """,
                (video_uid, location),
            ).fetchall()
        return [dict(r) for r in rows]

    def delete_drive_video_by_file_id(self, file_id: str) -> bool:
        video_uid = self.find_drive_video_uid_by_file_id(file_id)
        if not video_uid:
            return False
        return self.delete_video(video_uid)

    def delete_video(self, video_uid: str) -> bool:
        with self.db.connection() as con:
            cursor = con.execute("DELETE FROM videos WHERE video_uid = ?", (video_uid,))
            con.commit()
            return cursor.rowcount > 0

    def clear_location(self, location: str) -> int:
        with self.db.connection() as con:
            cursor = con.execute("DELETE FROM videos WHERE location = ?", (location,))
            con.commit()
            return cursor.rowcount

    def upsert_video(
        self,
        *,
        video_uid: str,
        location: str,
        source: str,
        title: Optional[str],
        channel: Optional[str],
        duration_seconds: Optional[int],
        created_at: Optional[str],
        modified_at: Optional[str],
        status: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        extra_json = json.dumps(extra) if extra else None
        with self.db.connection() as con:
            con.execute(
                """
                INSERT INTO videos (
                    video_uid, location, source, title, channel, duration_seconds,
                    created_at, modified_at, status, extra_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(video_uid) DO UPDATE SET
                    location=excluded.location,
                    source=excluded.source,
                    title=excluded.title,
                    channel=excluded.channel,
                    duration_seconds=excluded.duration_seconds,
                    created_at=excluded.created_at,
                    modified_at=excluded.modified_at,
                    status=excluded.status,
                    extra_json=excluded.extra_json
                """,
                (
                    video_uid,
                    location,
                    source,
                    title,
                    channel,
                    duration_seconds,
                    created_at,
                    modified_at,
                    status,
                    extra_json,
                ),
            )
            con.commit()

    def replace_assets(
        self, *, video_uid: str, location: str, assets: List[Dict[str, Any]]
    ) -> None:
        with self.db.connection() as con:
            con.execute(
                "DELETE FROM assets WHERE video_uid = ? AND location = ?",
                (video_uid, location),
            )
            for asset in assets:
                con.execute(
                    """
                    INSERT INTO assets (
                        video_uid, location, kind, local_path, drive_file_id,
                        mime_type, size_bytes, hash, extra_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        video_uid,
                        location,
                        asset.get("kind"),
                        asset.get("local_path"),
                        asset.get("drive_file_id"),
                        asset.get("mime_type"),
                        asset.get("size_bytes"),
                        asset.get("hash"),
                        json.dumps(asset.get("extra")) if asset.get("extra") else None,
                    ),
                )
            con.commit()

    def set_thumbnail_asset(
        self, *, video_uid: str, location: str, thumbnail_path: Optional[str]
    ) -> None:
        """
        Upsert the thumbnail asset for a video, preserving other assets.
        """
        assets = self.get_assets(video_uid=video_uid, location=location)
        filtered = [a for a in assets if a.get("kind") != "thumbnail"]

        if thumbnail_path:
            filtered.append(
                {
                    "kind": "thumbnail",
                    "local_path": thumbnail_path,
                    "drive_file_id": None,
                    "mime_type": None,
                    "size_bytes": None,
                    "hash": None,
                    "extra": None,
                }
            )

        self.replace_assets(video_uid=video_uid, location=location, assets=filtered)

    def get_videos_paginated(
        self, *, location: str, page: int, limit: int
    ) -> Dict[str, Any]:
        offset = (page - 1) * limit

        with self.db.connection() as con:
            total = con.execute(
                "SELECT COUNT(*) FROM videos WHERE location = ?",
                (location,),
            ).fetchone()[0]

            rows = con.execute(
                """
                SELECT
                    v.video_uid,
                    v.title,
                    v.channel,
                    v.duration_seconds,
                    v.created_at,
                    v.modified_at,
                    v.extra_json,
                    av.local_path AS video_path,
                    av.size_bytes AS video_size_bytes,
                    av.drive_file_id AS video_drive_id,
                    at.local_path AS thumbnail_path,
                    at.drive_file_id AS thumbnail_drive_id
                FROM videos v
                LEFT JOIN assets av
                    ON av.video_uid = v.video_uid AND av.location = v.location AND av.kind = 'video'
                LEFT JOIN assets at
                    ON at.video_uid = v.video_uid AND at.location = v.location AND at.kind = 'thumbnail'
                WHERE v.location = ?
                ORDER BY v.modified_at DESC
                LIMIT ? OFFSET ?
                """,
                (location, limit, offset),
            ).fetchall()

        videos: List[Dict[str, Any]] = []
        for row in rows:
            videos.append(
                {
                    "video_uid": row["video_uid"],
                    "title": row["title"],
                    "channel": row["channel"],
                    "duration_seconds": row["duration_seconds"],
                    "created_at": row["created_at"],
                    "modified_at": row["modified_at"],
                    "extra_json": row["extra_json"],
                    "path": row["video_path"],
                    "thumbnail": row["thumbnail_path"],
                    "size": row["video_size_bytes"],
                    "drive_id": row["video_drive_id"],
                    "thumbnail_drive_id": row["thumbnail_drive_id"],
                }
            )

        return {"total": int(total), "page": page, "limit": limit, "videos": videos}

    def touch_state(self, *, scope: str, field: str) -> None:
        """
        Update a timestamp field in catalog_state.

        field must be one of: last_imported_at, last_published_at.
        """
        if field not in {"last_imported_at", "last_published_at"}:
            raise ValueError("Invalid field")

        now = datetime.utcnow().isoformat()
        with self.db.connection() as con:
            con.execute(
                """
                INSERT INTO catalog_state (scope, version, {field})
                VALUES (?, 1, ?)
                ON CONFLICT(scope) DO UPDATE SET {field} = excluded.{field}
                """.format(field=field),
                (scope, now),
            )
            con.commit()

    def get_state(self, scope: str) -> Dict[str, Any]:
        with self.db.connection() as con:
            row = con.execute(
                "SELECT * FROM catalog_state WHERE scope = ?",
                (scope,),
            ).fetchone()
        return dict(row) if row else {}

    def set_drive_catalog_metadata(
        self,
        *,
        file_id: Optional[str] = None,
        etag: Optional[str] = None,
        revision: Optional[str] = None,
    ) -> None:
        with self.db.connection() as con:
            con.execute(
                """
                INSERT INTO catalog_state (scope, version, drive_catalog_file_id, drive_catalog_etag, drive_catalog_revision)
                VALUES ('drive', 1, ?, ?, ?)
                ON CONFLICT(scope) DO UPDATE SET
                    drive_catalog_file_id = COALESCE(excluded.drive_catalog_file_id, drive_catalog_file_id),
                    drive_catalog_etag = COALESCE(excluded.drive_catalog_etag, drive_catalog_etag),
                    drive_catalog_revision = COALESCE(excluded.drive_catalog_revision, drive_catalog_revision)
                """,
                (file_id, etag, revision),
            )
            con.commit()

    def export_drive_snapshot_items(self) -> List[Dict[str, Any]]:
        """
        Export drive items from SQLite into a snapshot-friendly list.

        Returns one item per video with an `assets` list.
        """
        with self.db.connection() as con:
            rows = con.execute(
                """
                SELECT
                    v.video_uid,
                    v.title,
                    v.channel,
                    v.duration_seconds,
                    v.created_at,
                    v.modified_at,
                    v.extra_json,
                    a.kind,
                    a.drive_file_id,
                    a.mime_type,
                    a.size_bytes
                FROM videos v
                LEFT JOIN assets a
                    ON a.video_uid = v.video_uid AND a.location = v.location
                WHERE v.location = 'drive'
                ORDER BY v.modified_at DESC
                """
            ).fetchall()

        by_uid: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            uid = row["video_uid"]
            item = by_uid.get(uid)
            if item is None:
                extra = {}
                if row["extra_json"]:
                    try:
                        extra = json.loads(row["extra_json"])
                    except Exception:
                        extra = {}

                item = {
                    "video_uid": uid,
                    "title": row["title"],
                    "channel": row["channel"],
                    "duration_seconds": row["duration_seconds"],
                    "created_at": row["created_at"],
                    "modified_at": row["modified_at"],
                    "path": extra.get("drive_path"),
                    "assets": [],
                }
                by_uid[uid] = item

            if row["kind"] and row["drive_file_id"]:
                item["assets"].append(
                    {
                        "kind": row["kind"],
                        "drive_file_id": row["drive_file_id"],
                        "mime_type": row["mime_type"],
                        "size_bytes": row["size_bytes"],
                    }
                )

        return list(by_uid.values())
