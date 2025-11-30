"""
Jobs service - business logic for async job management
"""
import os
import uuid
import asyncio
from datetime import datetime
from typing import TYPE_CHECKING

from . import store
from app.downloads.service import create_download_settings, execute_download

if TYPE_CHECKING:
    from app.downloads.schemas import DownloadRequest


def create_job(url: str, request: "DownloadRequest") -> str:
    """
    Create a new download job.

    Args:
        url: Video URL
        request: Download request parameters

    Returns:
        Job ID
    """
    job_id = str(uuid.uuid4())
    store.set_job(job_id, {
        "job_id": job_id,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "url": url,
        "request": request.model_dump(),
        "progress": {},
        "result": None,
        "error": None,
    })
    return job_id


def update_job_progress(job_id: str, progress: dict) -> None:
    """Update the progress of a job"""
    job = store.get_job(job_id)
    if job:
        job["progress"] = progress
        if progress.get("status") == "downloading":
            job["status"] = "downloading"


def complete_job(job_id: str, result: dict) -> None:
    """Mark a job as completed"""
    job = store.get_job(job_id)
    if job:
        job["status"] = "completed"
        job["result"] = result
        job["progress"] = {"status": "completed", "percentage": 100}
        job["completed_at"] = datetime.now().isoformat()


def fail_job(job_id: str, error: str) -> None:
    """Mark a job as failed"""
    job = store.get_job(job_id)
    if job:
        job["status"] = "error"
        job["error"] = error
        job["completed_at"] = datetime.now().isoformat()


def cancel_job(job_id: str) -> None:
    """Mark a job as cancelled"""
    job = store.get_job(job_id)
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
        settings = create_download_settings(
            out_dir=request.out_dir,
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
        target_dir = os.path.join(request.out_dir, request.path) if request.path else request.out_dir
        os.makedirs(target_dir, exist_ok=True)

        # Progress callback
        def progress_callback(progress: dict):
            update_job_progress(job_id, progress)

        # Execute download
        result = await execute_download(url, settings, progress_callback)

        if result["status"] == "error":
            fail_job(job_id, result.get("error", "Unknown error"))
        else:
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
