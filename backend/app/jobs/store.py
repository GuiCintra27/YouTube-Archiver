"""
Jobs store - in-memory storage for job state
"""
import asyncio
from typing import Dict

# In-memory storage for jobs
jobs_db: Dict[str, dict] = {}

# Active asyncio tasks
active_tasks: Dict[str, asyncio.Task] = {}


def get_job(job_id: str) -> dict | None:
    """Get a job by ID"""
    return jobs_db.get(job_id)


def get_all_jobs() -> list:
    """Get all jobs"""
    return list(jobs_db.values())


def set_job(job_id: str, job_data: dict) -> None:
    """Set a job in the store"""
    jobs_db[job_id] = job_data


def delete_job(job_id: str) -> bool:
    """Delete a job from the store"""
    if job_id in jobs_db:
        del jobs_db[job_id]
        return True
    return False


def get_task(job_id: str) -> asyncio.Task | None:
    """Get an active task by job ID"""
    return active_tasks.get(job_id)


def set_task(job_id: str, task: asyncio.Task) -> None:
    """Set an active task"""
    active_tasks[job_id] = task


def delete_task(job_id: str) -> bool:
    """Delete an active task"""
    if job_id in active_tasks:
        del active_tasks[job_id]
        return True
    return False


def job_exists(job_id: str) -> bool:
    """Check if a job exists"""
    return job_id in jobs_db


def task_exists(job_id: str) -> bool:
    """Check if a task exists"""
    return job_id in active_tasks
