"""
Catalog router - endpoints to manage the persistent catalog.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from fastapi import APIRouter, Request

from app.core.rate_limit import limiter, RateLimits
from app.core.blocking import run_drive_blocking
from app.catalog.service import (
    bootstrap_local_catalog,
    get_catalog_status,
    import_drive_snapshot_bytes,
    publish_drive_snapshot,
    rebuild_drive_catalog_from_drive,
)
from app.catalog.schemas import (
    CatalogStatusResponse,
    CatalogBootstrapResponse,
    CatalogDriveImportResponse,
    CatalogDrivePublishResponse,
    CatalogJobResponse,
)
from app.core.drive import require_drive_auth
from app.drive.manager import drive_manager
from app.core.responses import job_response
import io
from googleapiclient.http import MediaIoBaseDownload
import app.jobs.store as store
from app.jobs.store import JobType

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


@router.get("/status", response_model=CatalogStatusResponse)
@limiter.limit(RateLimits.GET_STATUS)
async def catalog_status(request: Request):
    return await get_catalog_status()


@router.post("/bootstrap-local", response_model=CatalogBootstrapResponse)
@limiter.limit(RateLimits.DOWNLOAD_BATCH)
async def bootstrap_local(request: Request, base_dir: str = "./downloads"):
    return await bootstrap_local_catalog(base_dir=base_dir)


@router.post("/drive/import", response_model=CatalogDriveImportResponse)
@limiter.limit(RateLimits.DOWNLOAD_BATCH)
async def import_drive_catalog(request: Request):
    """
    Import the Drive catalog snapshot into the local SQLite catalog.

    This endpoint downloads a single snapshot file (`catalog-drive.json.gz`) from:
    `YouTube Archiver/.catalog/`.
    """
    require_drive_auth(request)

    def _download_snapshot() -> tuple[str, bytes]:
        service = drive_manager.get_service()
        root_id = drive_manager.get_or_create_root_folder()
        catalog_folder_id = drive_manager.ensure_folder(".catalog", root_id)

        query = (
            "name='catalog-drive.json.gz' "
            f"and '{catalog_folder_id}' in parents "
            "and trashed=false"
        )
        results = service.files().list(q=query, fields="files(id, name, modifiedTime, size)").execute()
        files = results.get("files", [])
        if not files:
            return "", b""

        file_id = files[0]["id"]
        download_request = service.files().get_media(fileId=file_id)
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, download_request, chunksize=8 * 1024 * 1024)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        return file_id, buf.getvalue()

    file_id, snapshot_bytes = await run_drive_blocking(
        _download_snapshot,
        label="catalog.import_drive",
    )
    if not file_id:
        return {"status": "error", "message": "Drive catalog snapshot not found"}
    result = await import_drive_snapshot_bytes(snapshot_bytes=snapshot_bytes)
    return {"status": "success", "file_id": file_id, **result}


@router.post("/drive/publish", response_model=CatalogDrivePublishResponse)
@limiter.limit(RateLimits.DOWNLOAD_BATCH)
async def publish_drive_catalog(request: Request, force: bool = False):
    """Publish the current Drive catalog snapshot to Google Drive."""
    return await publish_drive_snapshot(force=force)


async def _run_drive_rebuild_job(job_id: str) -> None:
    try:
        job = store.get_job(job_id) or {}
        job["status"] = "running"
        job["progress"] = {"status": "scanning_drive", "percent": 5}
        store.set_job(job_id, job)

        result = await rebuild_drive_catalog_from_drive(publish=True, force_publish=True)

        job["status"] = "completed"
        job["progress"] = {"status": "completed", "percent": 100}
        job["result"] = result
        job["completed_at"] = datetime.now().isoformat()
        store.set_job(job_id, job)
    except asyncio.CancelledError:
        job = store.get_job(job_id) or {}
        job["status"] = "cancelled"
        job["error"] = "Rebuild cancelado"
        job["completed_at"] = datetime.now().isoformat()
        store.set_job(job_id, job)
        raise
    except Exception as e:
        job = store.get_job(job_id) or {}
        job["status"] = "error"
        job["error"] = str(e)
        job["completed_at"] = datetime.now().isoformat()
        store.set_job(job_id, job)


@router.post("/drive/rebuild", response_model=CatalogJobResponse)
@limiter.limit(RateLimits.DOWNLOAD_BATCH)
async def rebuild_drive_catalog(request: Request):
    """
    One-off: scan Drive to build the initial catalog snapshot.

    Use this when the Drive already has videos but `catalog-drive.json.gz` does not exist yet.
    """
    require_drive_auth(request)

    job_id = str(uuid.uuid4())
    store.set_job(
        job_id,
        {
            "job_id": job_id,
            "type": JobType.CATALOG_DRIVE_REBUILD.value,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "progress": {"status": "queued", "percent": 0},
            "result": None,
            "error": None,
        },
    )
    task = asyncio.create_task(_run_drive_rebuild_job(job_id))
    store.set_task(job_id, task)

    return job_response(job_id, "Rebuild do catálogo do Drive iniciado")
