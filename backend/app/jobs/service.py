"""
Jobs service - business logic for async job management.

Provides functions for:
- Creating and managing download jobs
- Updating job progress and status
- Executing downloads in background tasks
"""
import os
import uuid
import asyncio
from datetime import datetime
from typing import TYPE_CHECKING, Optional, Dict, Any
from pathlib import Path

from . import store
from app.downloads.service import create_download_settings, execute_download
from app.catalog.service import upsert_local_video_from_fs
from app.config import settings
from app.core.logging import get_module_logger
from app.core.types import JobData, JobProgress, DownloadResult

if TYPE_CHECKING:
    from app.downloads.schemas import DownloadRequest

logger = get_module_logger("jobs.service")


def _resolve_video_path(candidate: Path) -> Optional[Path]:
    if candidate.exists() and candidate.suffix.lower() in settings.VIDEO_EXTENSIONS:
        return candidate

    stem = candidate.stem
    parent = candidate.parent
    for ext in settings.VIDEO_EXTENSIONS:
        alt = parent / f"{stem}{ext}"
        if alt.exists():
            return alt
    return None


def create_job(url: str, request: "DownloadRequest") -> str:
    """
    Create a new download job.

    Args:
        url: Video URL to download
        request: Download request parameters from API

    Returns:
        Unique job ID (UUID string)
    """
    job_id: str = str(uuid.uuid4())
    job_data: JobData = {
        "job_id": job_id,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "url": url,
        "request": request.model_dump(),
        "progress": {},
        "result": None,
        "error": None,
    }
    store.set_job(job_id, job_data)
    return job_id


def update_job_progress(job_id: str, progress: Dict[str, Any]) -> None:
    """
    Update the progress of a job.

    Args:
        job_id: Job identifier
        progress: Progress data from downloader (percent, speed, eta, etc.)
    """
    job: Optional[Dict[str, Any]] = store.get_job(job_id)
    if job:
        job["progress"] = progress
        if progress.get("status") == "downloading":
            job["status"] = "downloading"


def complete_job(job_id: str, result: Dict[str, Any]) -> None:
    """
    Mark a job as completed.

    Args:
        job_id: Job identifier
        result: Download result data
    """
    job: Optional[Dict[str, Any]] = store.get_job(job_id)
    if job:
        job["status"] = "completed"
        job["result"] = result
        job["progress"] = {"status": "completed", "percentage": 100}
        job["completed_at"] = datetime.now().isoformat()


def fail_job(job_id: str, error: str) -> None:
    """
    Mark a job as failed.

    Args:
        job_id: Job identifier
        error: Error message describing the failure
    """
    job: Optional[Dict[str, Any]] = store.get_job(job_id)
    if job:
        job["status"] = "error"
        job["error"] = error
        job["completed_at"] = datetime.now().isoformat()


def cancel_job(job_id: str) -> None:
    """
    Mark a job as cancelled.

    Args:
        job_id: Job identifier
    """
    job: Optional[Dict[str, Any]] = store.get_job(job_id)
    if job:
        job["status"] = "cancelled"
        job["error"] = "Download cancelado pelo usuário"
        job["completed_at"] = datetime.now().isoformat()


async def run_download_job(job_id: str, url: str, request: "DownloadRequest") -> None:
    """
    Execute download job in background.

    Args:
        job_id: Job ID
        url: Video URL
        request: Download request parameters
    """
    try:
        # Create settings from request
        download_settings = create_download_settings(
            out_dir=settings.DOWNLOADS_DIR,
            archive_file=request.archive_file,
            fmt=request.fmt,
            max_res=request.max_res,
            subs=request.subs,
            auto_subs=request.auto_subs,
            sub_langs=request.sub_langs,
            thumbnails=request.thumbnails,
            audio_only=request.audio_only,
            limit=request.limit,
            cookies_file=request.cookies_file,
            referer=request.referer,
            origin=request.origin,
            user_agent=request.user_agent,
            concurrent_fragments=request.concurrent_fragments,
            custom_path=request.path,
            file_name=request.file_name,
            archive_id=request.archive_id,
            delay_between_downloads=request.delay_between_downloads,
            batch_size=request.batch_size,
            batch_delay=request.batch_delay,
            randomize_delay=request.randomize_delay,
        )

        # Create output directory
        target_dir = os.path.join(settings.DOWNLOADS_DIR, request.path) if request.path else settings.DOWNLOADS_DIR
        os.makedirs(target_dir, exist_ok=True)

        finished_files: list[str] = []

        # Progress callback
        def progress_callback(progress: dict):
            if progress.get("status") == "finished":
                fp = progress.get("filepath")
                if isinstance(fp, str) and fp:
                    finished_files.append(fp)
            update_job_progress(job_id, progress)

        # Execute download
        result = await execute_download(url, download_settings, progress_callback)

        if result["status"] == "error":
            fail_job(job_id, result.get("error", "Unknown error"))
        else:
            file_candidates = set(finished_files)
            for item in result.get("results", []) or []:
                fp = item.get("filepath")
                if isinstance(fp, str) and fp:
                    file_candidates.add(fp)

            if settings.CATALOG_ENABLED and file_candidates:
                try:
                    out_dir = Path(settings.DOWNLOADS_DIR).resolve()
                    for fp in sorted(file_candidates):
                        try:
                            abs_path = Path(fp).resolve()
                            resolved = _resolve_video_path(abs_path)
                            if not resolved:
                                continue

                            rel_path = resolved.relative_to(out_dir).as_posix()
                            thumb_rel = None
                            for ext in settings.THUMBNAIL_EXTENSIONS:
                                candidate = resolved.with_suffix(ext)
                                if candidate.exists():
                                    thumb_rel = candidate.relative_to(out_dir).as_posix()
                                    break

                            await upsert_local_video_from_fs(
                                video_path=rel_path,
                                base_dir=str(out_dir),
                                thumbnail_path=thumb_rel,
                            )
                        except Exception as e:
                            logger.warning(f"Catalog update skipped for {fp}: {e}")
                except Exception as e:
                    logger.warning(f"Catalog write-through failed (download_complete): {e}")
            complete_job(job_id, result)

    except Exception as e:
        fail_job(job_id, str(e))


async def create_and_start_job(request: "DownloadRequest") -> str:
    """
    Create a job and start it in background.

    Args:
        request: Download request parameters

    Returns:
        Job ID
    """
    job_id = create_job(request.url, request)

    # Create async task
    task = asyncio.create_task(run_download_job(job_id, request.url, request))
    store.set_task(job_id, task)

    return job_id
