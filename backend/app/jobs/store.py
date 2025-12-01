"""
Jobs store - in-memory storage for job state.

This module provides a simple in-memory storage for download jobs.
Jobs are stored in a dictionary and are not persisted across restarts.

For production use, consider implementing persistent storage
(Redis, database, etc.) by implementing the same interface.
"""
import asyncio
from enum import Enum
from typing import Dict, List, Optional, Any


class JobType(str, Enum):
    """Types of background jobs supported by the system."""
    DOWNLOAD = "download"
    DRIVE_UPLOAD = "drive_upload"
    DRIVE_SYNC = "drive_sync"
    DRIVE_DOWNLOAD = "drive_download"


# Type aliases for clarity
JobId = str
JobDict = Dict[str, Any]

# In-memory storage for jobs
_jobs_db: Dict[JobId, JobDict] = {}

# Active asyncio tasks (for cancellation)
_active_tasks: Dict[JobId, asyncio.Task[None]] = {}


def get_job(job_id: JobId) -> Optional[JobDict]:
    """
    Get a job by ID.

    Args:
        job_id: Job identifier

    Returns:
        Job data dict or None if not found
    """
    return _jobs_db.get(job_id)


def get_all_jobs() -> List[JobDict]:
    """
    Get all jobs.

    Returns:
        List of all job data dicts
    """
    return list(_jobs_db.values())


def set_job(job_id: JobId, job_data: JobDict) -> None:
    """
    Set a job in the store.

    Args:
        job_id: Job identifier
        job_data: Job data to store
    """
    _jobs_db[job_id] = job_data


def delete_job(job_id: JobId) -> bool:
    """
    Delete a job from the store.

    Args:
        job_id: Job identifier

    Returns:
        True if job was deleted, False if not found
    """
    if job_id in _jobs_db:
        del _jobs_db[job_id]
        return True
    return False


def get_task(job_id: JobId) -> Optional[asyncio.Task[None]]:
    """
    Get an active task by job ID.

    Args:
        job_id: Job identifier

    Returns:
        Task object or None if not found
    """
    return _active_tasks.get(job_id)


def set_task(job_id: JobId, task: asyncio.Task[None]) -> None:
    """
    Set an active task.

    Args:
        job_id: Job identifier
        task: Asyncio task to store
    """
    _active_tasks[job_id] = task


def delete_task(job_id: JobId) -> bool:
    """
    Delete an active task.

    Args:
        job_id: Job identifier

    Returns:
        True if task was deleted, False if not found
    """
    if job_id in _active_tasks:
        del _active_tasks[job_id]
        return True
    return False


def job_exists(job_id: JobId) -> bool:
    """
    Check if a job exists.

    Args:
        job_id: Job identifier

    Returns:
        True if job exists
    """
    return job_id in _jobs_db


def task_exists(job_id: JobId) -> bool:
    """
    Check if a task exists.

    Args:
        job_id: Job identifier

    Returns:
        True if task exists
    """
    return job_id in _active_tasks


def create_job(job_id: JobId, job_data: JobDict) -> JobDict:
    """
    Create a new job in the store.

    Args:
        job_id: Job identifier
        job_data: Job data to store

    Returns:
        The stored job data
    """
    _jobs_db[job_id] = job_data
    return job_data


def clear_all_jobs() -> int:
    """
    Clear all jobs from the store (primarily for testing).

    Returns:
        Number of jobs that were cleared
    """
    count: int = len(_jobs_db)
    _jobs_db.clear()
    _active_tasks.clear()
    return count


def get_jobs_by_status(status: str) -> List[JobDict]:
    """
    Get all jobs with a specific status.

    Args:
        status: Job status to filter by

    Returns:
        List of jobs matching the status
    """
    return [job for job in _jobs_db.values() if job.get("status") == status]


def get_jobs_by_type(job_type: JobType) -> List[JobDict]:
    """
    Get all jobs with a specific type.

    Args:
        job_type: Job type to filter by

    Returns:
        List of jobs matching the type
    """
    return [job for job in _jobs_db.values() if job.get("type") == job_type.value]


def count_jobs() -> int:
    """
    Get total number of jobs.

    Returns:
        Total job count
    """
    return len(_jobs_db)
