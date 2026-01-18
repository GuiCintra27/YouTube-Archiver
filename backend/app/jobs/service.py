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
import re
import time
from datetime import datetime
from typing import TYPE_CHECKING, Optional, Dict, Any
from pathlib import Path

from . import store
from app.downloads.service import create_download_settings, execute_download
from app.catalog.service import upsert_local_video_from_fs
from app.config import settings
from app.core.logging import get_module_logger
from app.core.exceptions import JobNotFoundException
from app.core.types import JobData, JobProgress, DownloadResult
from app.core.metrics import (
    DOWNLOAD_JOBS_ACTIVE,
    DOWNLOAD_JOBS_COMPLETED,
    DOWNLOAD_JOBS_FAILED,
    DOWNLOAD_JOBS_STARTED,
    DOWNLOAD_JOB_DURATION,
)

if TYPE_CHECKING:
    from app.downloads.schemas import DownloadRequest

logger = get_module_logger("jobs.service")

FORMAT_SUFFIX_RE = re.compile(r"^\.f\d+$", re.IGNORECASE)
TEMP_SUFFIXES = {".part", ".ytdl", ".temp"}


def get_job_or_raise(job_id: str) -> Dict[str, Any]:
    job = store.get_job(job_id)
    if not job:
        raise JobNotFoundException()
    job.setdefault("job_id", job_id)
    return job


def _strip_suffix(path: Path) -> Path:
    if path.suffix:
        return path.with_suffix("")
    return path


def _candidate_variants(path: Path) -> list[Path]:
    variants = [path]
    if path.suffix.lower() in TEMP_SUFFIXES:
        variants.append(path.with_suffix(""))

    for variant in list(variants):
        if len(variant.suffixes) >= 2:
            base = _strip_suffix(variant)
            if FORMAT_SUFFIX_RE.match(base.suffix):
                variants.append(base.with_suffix(variant.suffix))
                variants.append(_strip_suffix(base))

    seen: set[str] = set()
    unique: list[Path] = []
    for item in variants:
        key = str(item)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def _resolve_video_path(candidate: Path) -> Optional[Path]:
    for variant in _candidate_variants(candidate):
        if variant.exists() and variant.suffix.lower() in settings.VIDEO_EXTENSIONS:
            return variant

    for variant in _candidate_variants(candidate):
        base = _strip_suffix(variant)
        for ext in settings.VIDEO_EXTENSIONS:
            alt = Path(f"{base}{ext}")
            if alt.exists():
                return alt
    return None


def _scan_recent_videos(base_dir: Path, since_ts: float) -> list[Path]:
    if not base_dir.exists():
        return []

    recent: list[Path] = []
    for root, _, files in os.walk(base_dir):
        for name in files:
            candidate = Path(root) / name
            if candidate.suffix.lower() not in settings.VIDEO_EXTENSIONS:
                continue
            try:
                if candidate.stat().st_mtime >= since_ts:
                    recent.append(candidate)
            except Exception:
                continue
    return recent


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
        store.set_job(job_id, job)


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
        store.set_job(job_id, job)


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
        store.set_job(job_id, job)


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
        store.set_job(job_id, job)


async def run_download_job(job_id: str, url: str, request: "DownloadRequest") -> None:
    """
    Execute download job in background.

    Args:
        job_id: Job ID
        url: Video URL
        request: Download request parameters
    """
    job_started_ts = datetime.now().timestamp()
    start_time = time.perf_counter()
    DOWNLOAD_JOBS_STARTED.inc()
    DOWNLOAD_JOBS_ACTIVE.inc()
    failed = False
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
            failed = True
            fail_job(job_id, result.get("error", "Unknown error"))
        else:
            file_candidates = set(finished_files)
            for item in result.get("results", []) or []:
                fp = item.get("filepath")
                if isinstance(fp, str) and fp:
                    file_candidates.add(fp)

            catalog_updates = 0
            resolved_paths: set[str] = set()
            out_dir = Path(settings.DOWNLOADS_DIR).resolve()
            if settings.CATALOG_ENABLED and file_candidates:
                try:
                    for fp in sorted(file_candidates):
                        try:
                            abs_path = Path(fp).resolve()
                            resolved = _resolve_video_path(abs_path)
                            if not resolved:
                                continue

                            resolved_key = str(resolved)
                            if resolved_key in resolved_paths:
                                continue
                            resolved_paths.add(resolved_key)

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
                            catalog_updates += 1
                        except Exception as e:
                            logger.warning(f"Catalog update skipped for {fp}: {e}")
                except Exception as e:
                    logger.warning(f"Catalog write-through failed (download_complete): {e}")
            if settings.CATALOG_ENABLED and catalog_updates == 0:
                try:
                    fallback_dir = Path(target_dir).resolve()
                    fallback_paths = _scan_recent_videos(fallback_dir, job_started_ts)
                    if fallback_paths:
                        logger.info(
                            f"Catalog fallback scan found {len(fallback_paths)} new file(s) in {fallback_dir}"
                        )
                    for resolved in fallback_paths:
                        try:
                            resolved_key = str(resolved)
                            if resolved_key in resolved_paths:
                                continue
                            resolved_paths.add(resolved_key)

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
                            catalog_updates += 1
                        except Exception as e:
                            logger.warning(f"Catalog fallback update skipped for {resolved}: {e}")
                except Exception as e:
                    logger.warning(f"Catalog fallback scan failed (download_complete): {e}")
            complete_job(job_id, result)

    except Exception as e:
        failed = True
        fail_job(job_id, str(e))
    finally:
        DOWNLOAD_JOBS_ACTIVE.dec()
        DOWNLOAD_JOB_DURATION.observe(time.perf_counter() - start_time)
        if failed:
            DOWNLOAD_JOBS_FAILED.inc()
        else:
            DOWNLOAD_JOBS_COMPLETED.inc()


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
