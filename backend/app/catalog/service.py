"""
Catalog service (business logic).
"""

from __future__ import annotations

import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional

from app.catalog.repository import CatalogRepository
from app.config import settings
from app.core.blocking import (
    run_blocking,
    get_catalog_semaphore,
    get_fs_semaphore,
    get_drive_semaphore,
)
from app.core.logging import get_module_logger
from app.library.service import scan_videos_directory, format_duration
from datetime import datetime
from pathlib import Path

logger = get_module_logger("catalog.service")


def _local_video_uid(relative_path: str) -> str:
    return f"local:{relative_path}"

def _drive_video_uid(video_file_id: str) -> str:
    return f"drive:{video_file_id}"

def _iso_now() -> str:
    return datetime.utcnow().isoformat()


async def get_catalog_status(repo: Optional[CatalogRepository] = None) -> Dict[str, Any]:
    repo = repo or CatalogRepository()

    def _read() -> Dict[str, Any]:
        counts = repo.get_counts()
        return {
            "enabled": settings.CATALOG_ENABLED,
            "db_path": settings.catalog_db_path,
            "counts": counts,
            "state": {
                "local": repo.get_state("local"),
                "drive": repo.get_state("drive"),
            },
        }

    return await run_blocking(
        _read,
        semaphore=get_catalog_semaphore(),
        label="catalog.status",
    )


async def bootstrap_local_catalog(
    base_dir: str = "./downloads",
    repo: Optional[CatalogRepository] = None,
) -> Dict[str, Any]:
    """
    One-off scan to populate the local catalog.

    Note: this is intentionally explicit (triggered by endpoint) to avoid
    expensive work on every startup.
    """
    repo = repo or CatalogRepository()

    videos = await run_blocking(
        scan_videos_directory,
        base_dir=base_dir,
        use_cache=False,
        semaphore=get_fs_semaphore(),
        label="catalog.bootstrap.scan",
    )

    def _write() -> Dict[str, Any]:
        deleted = repo.clear_location("local")
        inserted = 0
        for v in videos:
            rel_path = v.get("path")
            if not rel_path:
                continue

            video_uid = _local_video_uid(rel_path)

            duration_seconds = v.get("duration_seconds")
            if duration_seconds is not None:
                try:
                    duration_seconds_int = int(float(duration_seconds))
                except Exception:
                    duration_seconds_int = None
            else:
                duration_seconds_int = None

            repo.upsert_video(
                video_uid=video_uid,
                location="local",
                source="custom",
                title=v.get("title"),
                channel=v.get("channel"),
                duration_seconds=duration_seconds_int,
                created_at=v.get("created_at"),
                modified_at=v.get("modified_at"),
                status="available",
            )

            assets = [
                {
                    "kind": "video",
                    "local_path": v.get("path"),
                    "mime_type": None,
                    "size_bytes": v.get("size"),
                }
            ]
            if v.get("thumbnail"):
                assets.append(
                    {
                        "kind": "thumbnail",
                        "local_path": v.get("thumbnail"),
                        "mime_type": None,
                        "size_bytes": None,
                    }
                )

            repo.replace_assets(video_uid=video_uid, location="local", assets=assets)
            inserted += 1

        repo.touch_state(scope="local", field="last_imported_at")
        return {"deleted": deleted, "inserted": inserted}

    result = await run_blocking(
        _write,
        semaphore=get_catalog_semaphore(),
        label="catalog.bootstrap.write",
    )
    logger.info(f"Local catalog bootstrapped: {result}")
    return result


async def list_local_videos_paginated(
    *, page: int, limit: int, repo: Optional[CatalogRepository] = None
) -> Dict[str, Any]:
    repo = repo or CatalogRepository()

    result = await run_blocking(
        repo.get_videos_paginated,
        location="local",
        page=page,
        limit=limit,
        semaphore=get_catalog_semaphore(),
        label="catalog.list_local",
    )
    # Match existing library response shape
    videos = []
    for v in result["videos"]:
        duration_seconds = v.get("duration_seconds")
        videos.append(
            {
                "id": v.get("path"),
                "title": v.get("title"),
                "channel": v.get("channel") or "Sem categoria",
                "path": v.get("path"),
                "thumbnail": v.get("thumbnail"),
                "size": v.get("size") or 0,
                "duration_seconds": duration_seconds,
                "duration": format_duration(duration_seconds) if duration_seconds else None,
                "created_at": v.get("created_at"),
                "modified_at": v.get("modified_at"),
            }
        )
    return {
        "total": result["total"],
        "page": result["page"],
        "limit": result["limit"],
        "videos": videos,
    }


def _stat_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts).isoformat()


async def delete_local_video_from_catalog(
    *, video_path: str, repo: Optional[CatalogRepository] = None
) -> None:
    if not settings.CATALOG_ENABLED:
        return
    repo = repo or CatalogRepository()
    await run_blocking(
        repo.delete_video,
        _local_video_uid(video_path),
        semaphore=get_catalog_semaphore(),
        label="catalog.delete_local",
    )


async def upsert_local_video_from_fs(
    *, video_path: str, base_dir: str, thumbnail_path: Optional[str] = None, repo: Optional[CatalogRepository] = None
) -> None:
    """
    Upsert a single local video record from the filesystem.
    """
    if not settings.CATALOG_ENABLED:
        return

    repo = repo or CatalogRepository()

    def _run() -> None:
        full_path = Path(base_dir) / video_path
        stat = full_path.stat()

        title = full_path.stem
        parts = Path(video_path).parts
        channel = parts[0] if len(parts) > 1 else "Sem categoria"

        video_uid = _local_video_uid(video_path)

        existing = repo.get_video(video_uid)
        duration_seconds = existing.get("duration_seconds") if existing else None

        repo.upsert_video(
            video_uid=video_uid,
            location="local",
            source=existing.get("source", "custom") if existing else "custom",
            title=title,
            channel=channel,
            duration_seconds=duration_seconds,
            created_at=existing.get("created_at") if existing else _stat_iso(stat.st_ctime),
            modified_at=_stat_iso(stat.st_mtime),
            status="available",
        )

        assets = [
            {
                "kind": "video",
                "local_path": video_path,
                "mime_type": None,
                "size_bytes": stat.st_size,
            }
        ]
        if thumbnail_path:
            assets.append({"kind": "thumbnail", "local_path": thumbnail_path})

        repo.replace_assets(video_uid=video_uid, location="local", assets=assets)

    await run_blocking(
        _run,
        semaphore=get_catalog_semaphore(),
        label="catalog.upsert_local",
    )


async def rename_local_video_in_catalog(
    *,
    old_video_path: str,
    new_video_path: str,
    base_dir: str,
    new_thumbnail_path: Optional[str] = None,
    repo: Optional[CatalogRepository] = None,
) -> None:
    if not settings.CATALOG_ENABLED:
        return

    repo = repo or CatalogRepository()

    old_uid = _local_video_uid(old_video_path)
    # Remove old record (uid changes in our current local scheme)
    await run_blocking(
        repo.delete_video,
        old_uid,
        semaphore=get_catalog_semaphore(),
        label="catalog.rename.delete",
    )

    await upsert_local_video_from_fs(
        video_path=new_video_path,
        base_dir=base_dir,
        thumbnail_path=new_thumbnail_path,
        repo=repo,
    )

def _asset_kind_for_name(file_name: str) -> Optional[str]:
    name = file_name.lower()
    if any(name.endswith(ext) for ext in settings.VIDEO_EXTENSIONS):
        return "video"
    if any(name.endswith(ext) for ext in settings.THUMBNAIL_EXTENSIONS):
        return "thumbnail"
    if name.endswith(".info.json"):
        return "info_json"
    if name.endswith(".description"):
        return "other"
    if any(name.endswith(ext) for ext in (".vtt", ".srt", ".ass")):
        return "subtitles"
    if name.endswith(".txt"):
        return "transcript"
    return None


async def upsert_drive_video_from_upload(
    *,
    video_file_id: str,
    drive_path: str,
    size_bytes: Optional[int] = None,
    related_files: Optional[list[dict]] = None,
    repo: Optional[CatalogRepository] = None,
) -> None:
    """
    Upsert a Drive video entry after an upload action (write-through).

    This avoids needing Drive list/search calls for subsequent listing.
    """
    if not settings.CATALOG_ENABLED:
        return

    repo = repo or CatalogRepository()

    def _run() -> None:
        path = drive_path or ""
        title = Path(path).stem if path else None
        parts = Path(path).parts if path else ()
        channel = parts[0] if len(parts) > 1 else "Sem categoria"

        video_uid = _drive_video_uid(video_file_id)
        existing = repo.get_video(video_uid)
        created_at = existing.get("created_at") if existing else _iso_now()

        repo.upsert_video(
            video_uid=video_uid,
            location="drive",
            source=existing.get("source", "custom") if existing else "custom",
            title=title,
            channel=channel,
            duration_seconds=existing.get("duration_seconds") if existing else None,
            created_at=created_at,
            modified_at=_iso_now(),
            status="available",
            extra={"drive_path": drive_path} if drive_path else None,
        )

        assets = [
            {
                "kind": "video",
                "local_path": drive_path,
                "drive_file_id": video_file_id,
                "size_bytes": size_bytes,
            }
        ]

        for item in related_files or []:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            file_id = item.get("file_id")
            if not name or not file_id:
                continue
            kind = _asset_kind_for_name(str(name))
            if not kind or kind == "video":
                continue
            assets.append({"kind": kind, "drive_file_id": str(file_id)})

        repo.replace_assets(video_uid=video_uid, location="drive", assets=assets)

    await run_blocking(
        _run,
        semaphore=get_catalog_semaphore(),
        label="catalog.upsert_drive_upload",
    )


async def delete_drive_video_from_catalog(
    *, video_file_id: str, repo: Optional[CatalogRepository] = None
) -> bool:
    if not settings.CATALOG_ENABLED:
        return False
    repo = repo or CatalogRepository()
    return await run_blocking(
        repo.delete_drive_video_by_file_id,
        video_file_id,
        semaphore=get_catalog_semaphore(),
        label="catalog.delete_drive",
    )


async def rename_drive_video_in_catalog(
    *,
    video_file_id: str,
    new_file_name: str,
    repo: Optional[CatalogRepository] = None,
) -> bool:
    """
    Update the Drive path/title in the catalog after a rename.
    """
    if not settings.CATALOG_ENABLED:
        return False
    repo = repo or CatalogRepository()

    def _run() -> bool:
        video_uid = repo.find_drive_video_uid_by_file_id(video_file_id)
        if not video_uid:
            return False

        row = repo.get_video(video_uid)
        extra = {}
        if row.get("extra_json"):
            try:
                extra = json.loads(row["extra_json"])
            except Exception:
                extra = {}

        old_path = extra.get("drive_path")
        if isinstance(old_path, str) and old_path:
            parent = str(Path(old_path).parent)
            if parent == ".":
                drive_path = new_file_name
            else:
                drive_path = str(Path(parent) / new_file_name)
        else:
            drive_path = new_file_name

        parts = Path(drive_path).parts
        channel = parts[0] if len(parts) > 1 else row.get("channel") or "Sem categoria"

        repo.upsert_video(
            video_uid=video_uid,
            location="drive",
            source=row.get("source") or "custom",
            title=Path(new_file_name).stem,
            channel=channel,
            duration_seconds=row.get("duration_seconds"),
            created_at=row.get("created_at"),
            modified_at=_iso_now(),
            status=row.get("status") or "available",
            extra={"drive_path": drive_path},
        )
        return True

    return await run_blocking(
        _run,
        semaphore=get_catalog_semaphore(),
        label="catalog.rename_drive",
    )


async def set_drive_thumbnail_in_catalog(
    *,
    video_file_id: str,
    thumbnail_file_id: str,
    repo: Optional[CatalogRepository] = None,
) -> bool:
    if not settings.CATALOG_ENABLED:
        return False
    repo = repo or CatalogRepository()

    def _run() -> bool:
        video_uid = repo.find_drive_video_uid_by_file_id(video_file_id)
        if not video_uid:
            return False

        assets = repo.get_assets(video_uid=video_uid, location="drive")
        filtered = [a for a in assets if a.get("kind") != "thumbnail"]
        filtered.append({"kind": "thumbnail", "drive_file_id": thumbnail_file_id})
        repo.replace_assets(video_uid=video_uid, location="drive", assets=filtered)

        row = repo.get_video(video_uid)
        extra = None
        if row.get("extra_json"):
            try:
                extra = json.loads(row["extra_json"])
            except Exception:
                extra = None
        repo.upsert_video(
            video_uid=video_uid,
            location="drive",
            source=row.get("source") or "custom",
            title=row.get("title"),
            channel=row.get("channel"),
            duration_seconds=row.get("duration_seconds"),
            created_at=row.get("created_at"),
            modified_at=_iso_now(),
            status=row.get("status") or "available",
            extra=extra,
        )
        return True

    return await run_blocking(
        _run,
        semaphore=get_catalog_semaphore(),
        label="catalog.set_drive_thumbnail",
    )


async def set_drive_share_metadata_in_catalog(
    *,
    video_file_id: str,
    share_link: str,
    permission_id: str,
    repo: Optional[CatalogRepository] = None,
) -> bool:
    if not settings.CATALOG_ENABLED:
        return False
    repo = repo or CatalogRepository()

    def _run() -> bool:
        video_uid = repo.find_drive_video_uid_by_file_id(video_file_id)
        if not video_uid:
            return False

        row = repo.get_video(video_uid)
        extra = {}
        if row.get("extra_json"):
            try:
                extra = json.loads(row["extra_json"])
            except Exception:
                extra = {}

        extra["share_link"] = share_link
        extra["share_permission_id"] = permission_id

        repo.upsert_video(
            video_uid=video_uid,
            location="drive",
            source=row.get("source") or "custom",
            title=row.get("title"),
            channel=row.get("channel"),
            duration_seconds=row.get("duration_seconds"),
            created_at=row.get("created_at"),
            modified_at=_iso_now(),
            status=row.get("status") or "available",
            extra=extra,
        )
        return True

    return await run_blocking(
        _run,
        semaphore=get_catalog_semaphore(),
        label="catalog.set_drive_share",
    )


async def clear_drive_share_metadata_in_catalog(
    *,
    video_file_id: str,
    repo: Optional[CatalogRepository] = None,
) -> bool:
    if not settings.CATALOG_ENABLED:
        return False
    repo = repo or CatalogRepository()

    def _run() -> bool:
        video_uid = repo.find_drive_video_uid_by_file_id(video_file_id)
        if not video_uid:
            return False

        row = repo.get_video(video_uid)
        extra = {}
        if row.get("extra_json"):
            try:
                extra = json.loads(row["extra_json"])
            except Exception:
                extra = {}

        extra.pop("share_link", None)
        extra.pop("share_permission_id", None)

        repo.upsert_video(
            video_uid=video_uid,
            location="drive",
            source=row.get("source") or "custom",
            title=row.get("title"),
            channel=row.get("channel"),
            duration_seconds=row.get("duration_seconds"),
            created_at=row.get("created_at"),
            modified_at=_iso_now(),
            status=row.get("status") or "available",
            extra=extra,
        )
        return True

    return await run_blocking(
        _run,
        semaphore=get_catalog_semaphore(),
        label="catalog.clear_drive_share",
    )


async def import_drive_snapshot_bytes(
    *, snapshot_bytes: bytes, repo: Optional[CatalogRepository] = None
) -> Dict[str, Any]:
    """
    Import a Drive snapshot (gzipped JSON bytes) into the local catalog (location=drive).
    """
    from app.catalog.drive_snapshot import decode_drive_snapshot

    repo = repo or CatalogRepository()

    def _run() -> Dict[str, Any]:
        payload = decode_drive_snapshot(snapshot_bytes)

        deleted = repo.clear_location("drive")
        inserted = 0

        for item in payload.get("videos", []):
            if not isinstance(item, dict):
                continue
            video_uid = item.get("video_uid")
            if not video_uid or not isinstance(video_uid, str):
                continue

            repo.upsert_video(
                video_uid=video_uid,
                location="drive",
                source=item.get("source") or "youtube",
                title=item.get("title"),
                channel=item.get("channel"),
                duration_seconds=item.get("duration_seconds"),
                created_at=item.get("created_at"),
                modified_at=item.get("modified_at"),
                status="available",
                extra={
                    "drive_path": item.get("path"),
                }
                if item.get("path")
                else None,
            )

            drive_path = item.get("path") if isinstance(item.get("path"), str) else None
            assets = []
            for asset in item.get("assets", []) or []:
                if not isinstance(asset, dict):
                    continue
                kind = asset.get("kind")
                drive_file_id = asset.get("drive_file_id")
                if not kind or not drive_file_id:
                    continue
                local_path = None
                if kind == "video" and drive_path:
                    local_path = drive_path
                assets.append(
                    {
                        "kind": kind,
                        "local_path": local_path,
                        "drive_file_id": drive_file_id,
                        "mime_type": asset.get("mime_type"),
                        "size_bytes": asset.get("size_bytes"),
                    }
                )

            if assets:
                repo.replace_assets(video_uid=video_uid, location="drive", assets=assets)

            inserted += 1

        repo.touch_state(scope="drive", field="last_imported_at")
        return {"deleted": deleted, "inserted": inserted, "generated_at": payload.get("generated_at")}

    return await run_blocking(
        _run,
        semaphore=get_catalog_semaphore(),
        label="catalog.import_drive",
    )


async def list_drive_videos_paginated(
    *, page: int, limit: int, repo: Optional[CatalogRepository] = None
) -> Dict[str, Any]:
    """
    List Drive videos from the local catalog (location=drive).

    Response shape matches existing `/api/drive/videos` items used by the UI.
    """
    repo = repo or CatalogRepository()
    result = await run_blocking(
        repo.get_videos_paginated,
        location="drive",
        page=page,
        limit=limit,
        semaphore=get_catalog_semaphore(),
        label="catalog.list_drive",
    )

    videos = []
    for v in result["videos"]:
        drive_id = v.get("drive_id")
        if not drive_id:
            continue

        extra = {}
        if v.get("extra_json"):
            try:
                extra = json.loads(v["extra_json"])
            except Exception:
                extra = {}

        drive_path = extra.get("drive_path")
        name = None
        if isinstance(drive_path, str):
            name = Path(drive_path).name

        videos.append(
            {
                "id": drive_id,
                "name": name,
                "path": drive_path,
                "size": v.get("size") or 0,
                "created_at": v.get("created_at"),
                "modified_at": v.get("modified_at"),
                "thumbnail": None,
                "custom_thumbnail_id": v.get("thumbnail_drive_id"),
            }
        )

    return {
        "total": result["total"],
        "page": result["page"],
        "limit": result["limit"],
        "videos": videos,
    }


async def publish_drive_snapshot(
    *,
    repo: Optional[CatalogRepository] = None,
    require_import_before_publish: Optional[bool] = None,
    force: bool = False,
) -> Dict[str, Any]:
    """
    Publish the Drive snapshot file (`catalog-drive.json.gz`) to Google Drive.

    Requires OAuth authentication.
    """
    from app.catalog.drive_snapshot import build_drive_snapshot, encode_drive_snapshot
    from app.drive.manager import drive_manager
    from app.core.exceptions import DriveNotAuthenticatedException
    from googleapiclient.http import MediaIoBaseUpload
    import io

    repo = repo or CatalogRepository()
    if require_import_before_publish is None:
        require_import_before_publish = settings.CATALOG_DRIVE_REQUIRE_IMPORT_BEFORE_PUBLISH
    def _publish() -> Dict[str, Any]:
        if not drive_manager.is_authenticated():
            raise DriveNotAuthenticatedException()

        items = repo.export_drive_snapshot_items()

        payload = build_drive_snapshot(videos=items)
        blob = encode_drive_snapshot(payload)

        service = drive_manager.get_service()
        root_id = drive_manager.get_or_create_root_folder()
        catalog_folder_id = drive_manager.ensure_folder(".catalog", root_id)

        file_name = "catalog-drive.json.gz"
        query = f"name='{file_name}' and '{catalog_folder_id}' in parents and trashed=false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        existing = results.get("files", [])

        if existing and require_import_before_publish and not force:
            state = repo.get_state("drive")
            if not state.get("last_imported_at"):
                from app.core.exceptions import InvalidRequestException

                raise InvalidRequestException(
                    "Catálogo do Drive já existe: rode /api/catalog/drive/import antes de publicar (ou use force=true)."
                )

        media = MediaIoBaseUpload(io.BytesIO(blob), mimetype="application/gzip", resumable=False)

        if existing:
            file_id = existing[0]["id"]
            response = (
                service.files()
                .update(
                    fileId=file_id,
                    media_body=media,
                    fields="id, name, modifiedTime, size",
                )
                .execute()
            )
        else:
            metadata = {"name": file_name, "parents": [catalog_folder_id]}
            response = (
                service.files()
                .create(
                    body=metadata,
                    media_body=media,
                    fields="id, name, modifiedTime, size",
                )
                .execute()
            )

        repo.set_drive_catalog_metadata(file_id=response.get("id"))
        repo.touch_state(scope="drive", field="last_published_at")

        return {
            "status": "success",
            "file_id": response.get("id"),
            "name": response.get("name"),
            "size": response.get("size"),
            "generated_at": payload.get("generated_at"),
            "videos": len(items),
        }

    return await run_blocking(
        _publish,
        semaphore=get_drive_semaphore(),
        label="catalog.publish_drive",
    )


async def maybe_publish_drive_snapshot(
    *, reason: str, repo: Optional[CatalogRepository] = None
) -> Optional[Dict[str, Any]]:
    """
    Publish the Drive snapshot if catalog + auto-publish are enabled.

    This is a best-effort helper: failures are logged and swallowed to avoid
    breaking the original Drive action.
    """
    if not settings.CATALOG_ENABLED or not settings.CATALOG_DRIVE_AUTO_PUBLISH:
        return None

    repo = repo or CatalogRepository()
    try:
        return await publish_drive_snapshot(repo=repo)
    except Exception as e:
        logger.warning(f"Auto-publish skipped ({reason}): {e}")
        return None


async def rebuild_drive_catalog_from_drive(
    *, repo: Optional[CatalogRepository] = None, publish: bool = True, force_publish: bool = False
) -> Dict[str, Any]:
    """
    One-off rebuild of the Drive catalog by scanning Google Drive.

    This is intended only for the initial migration (when no snapshot exists yet)
    or for manual recovery/admin maintenance.
    """
    from app.drive.manager import drive_manager
    from app.core.exceptions import DriveNotAuthenticatedException

    if not drive_manager.is_authenticated():
        raise DriveNotAuthenticatedException()

    repo = repo or CatalogRepository()

    # Heavy network operation: run outside event loop thread.
    # Use a dedicated executor to avoid leaking the loop default executor across test loops.
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=1) as executor:
        drive_videos = await loop.run_in_executor(executor, drive_manager.list_videos)
    def _write() -> Dict[str, Any]:
        deleted = repo.clear_location("drive")
        inserted = 0

        for v in drive_videos:
            file_id = v.get("id")
            drive_path = v.get("path")
            if not file_id or not drive_path:
                continue

            video_uid = _drive_video_uid(str(file_id))
            parts = Path(str(drive_path)).parts
            channel = parts[0] if len(parts) > 1 else "Sem categoria"
            title = Path(str(drive_path)).stem

            repo.upsert_video(
                video_uid=video_uid,
                location="drive",
                source="custom",
                title=title,
                channel=channel,
                duration_seconds=None,
                created_at=v.get("created_at"),
                modified_at=v.get("modified_at") or _iso_now(),
                status="available",
                extra={"drive_path": str(drive_path)},
            )

            assets = [
                {
                    "kind": "video",
                    "local_path": str(drive_path),
                    "drive_file_id": str(file_id),
                    "size_bytes": int(v.get("size") or 0),
                }
            ]

            custom_thumb_id = v.get("custom_thumbnail_id")
            if custom_thumb_id:
                assets.append({"kind": "thumbnail", "drive_file_id": str(custom_thumb_id)})

            repo.replace_assets(video_uid=video_uid, location="drive", assets=assets)
            inserted += 1

        repo.touch_state(scope="drive", field="last_imported_at")
        return {"deleted": deleted, "inserted": inserted}

    result = await run_blocking(
        _write,
        semaphore=get_catalog_semaphore(),
        label="catalog.rebuild.write",
    )

    deleted = int(result.get("deleted", 0))
    inserted = int(result.get("inserted", 0))

    published = None
    if publish:
        published = await publish_drive_snapshot(repo=repo, force=force_publish)

    return {
        "deleted": deleted,
        "inserted": inserted,
        "published": published,
    }
