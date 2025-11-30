"""
Automatic job cleanup - removes old completed/failed jobs from memory.

This module provides a background task that periodically cleans up old jobs
to prevent memory leaks during long-running sessions.
"""
import asyncio
from datetime import datetime, timedelta
from typing import List

from app.config import settings
from app.core.logging import get_module_logger
from . import store

logger = get_module_logger("jobs.cleanup")

# Terminal states that can be cleaned up
TERMINAL_STATES = {"completed", "error", "cancelled"}


def get_jobs_to_cleanup(max_age_hours: int) -> List[str]:
    """
    Get list of job IDs that should be cleaned up.

    Args:
        max_age_hours: Maximum age in hours for completed jobs

    Returns:
        List of job IDs to clean up
    """
    cutoff = datetime.now() - timedelta(hours=max_age_hours)
    jobs_to_remove = []

    for job_id, job in store.jobs_db.items():
        # Only clean up terminal states
        if job.get("status") not in TERMINAL_STATES:
            continue

        # Check completed_at timestamp
        completed_at_str = job.get("completed_at")
        if not completed_at_str:
            # Fallback to created_at for old jobs without completed_at
            completed_at_str = job.get("created_at")

        if not completed_at_str:
            continue

        try:
            completed_at = datetime.fromisoformat(completed_at_str)
            if completed_at < cutoff:
                jobs_to_remove.append(job_id)
        except (ValueError, TypeError):
            # Invalid timestamp, skip
            continue

    return jobs_to_remove


def cleanup_jobs(job_ids: List[str]) -> int:
    """
    Remove jobs from the store.

    Args:
        job_ids: List of job IDs to remove

    Returns:
        Number of jobs removed
    """
    removed = 0
    for job_id in job_ids:
        if store.delete_job(job_id):
            removed += 1
        # Also clean up any associated tasks
        store.delete_task(job_id)

    return removed


async def run_cleanup_loop(interval_minutes: int = 30) -> None:
    """
    Background task that periodically cleans up old jobs.

    Args:
        interval_minutes: Interval between cleanup runs
    """
    logger.info(
        f"Job cleanup task started (interval: {interval_minutes}min, "
        f"max age: {settings.JOB_EXPIRY_HOURS}h)"
    )

    while True:
        try:
            # Wait for the interval
            await asyncio.sleep(interval_minutes * 60)

            # Get jobs to cleanup
            jobs_to_remove = get_jobs_to_cleanup(settings.JOB_EXPIRY_HOURS)

            if jobs_to_remove:
                removed = cleanup_jobs(jobs_to_remove)
                logger.info(f"Cleaned up {removed} old jobs")
            else:
                logger.debug("No jobs to clean up")

        except asyncio.CancelledError:
            logger.info("Job cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in job cleanup task: {e}", exc_info=True)
            # Continue running despite errors
            await asyncio.sleep(60)  # Wait a bit before retrying


def cleanup_now() -> int:
    """
    Manually trigger cleanup of old jobs.

    Returns:
        Number of jobs removed
    """
    jobs_to_remove = get_jobs_to_cleanup(settings.JOB_EXPIRY_HOURS)
    if jobs_to_remove:
        return cleanup_jobs(jobs_to_remove)
    return 0


def get_cleanup_stats() -> dict:
    """
    Get statistics about jobs for cleanup monitoring.

    Returns:
        Dictionary with job statistics
    """
    total = len(store.jobs_db)
    by_status = {}

    for job in store.jobs_db.values():
        status = job.get("status", "unknown")
        by_status[status] = by_status.get(status, 0) + 1

    eligible_for_cleanup = len(get_jobs_to_cleanup(settings.JOB_EXPIRY_HOURS))

    return {
        "total_jobs": total,
        "by_status": by_status,
        "eligible_for_cleanup": eligible_for_cleanup,
        "expiry_hours": settings.JOB_EXPIRY_HOURS,
    }
