"""
Jobs store - pluggable storage for job state.

Defaults to in-memory storage, with optional Redis backend for persistence.
Active asyncio tasks are always tracked in-memory per process.
"""
from __future__ import annotations

import asyncio
import json
from enum import Enum
from typing import Dict, List, Optional, Any, Protocol

from app.config import settings
from app.core.logging import get_module_logger

logger = get_module_logger("jobs.store")


class JobType(str, Enum):
    """Types of background jobs supported by the system."""
    DOWNLOAD = "download"
    DRIVE_UPLOAD = "drive_upload"
    DRIVE_SYNC = "drive_sync"
    DRIVE_DOWNLOAD = "drive_download"
    CATALOG_DRIVE_REBUILD = "catalog_drive_rebuild"
    DRIVE_CLEANUP = "drive_cleanup"


# Type aliases for clarity
JobId = str
JobDict = Dict[str, Any]

# In-memory fallback storage for jobs
_jobs_db: Dict[JobId, JobDict] = {}

# Active asyncio tasks (for cancellation)
_active_tasks: Dict[JobId, asyncio.Task[None]] = {}

# Backward-compatible aliases (some modules still reference these directly)
# NOTE: when Redis is enabled, jobs_db will NOT reflect persisted jobs.
jobs_db = _jobs_db
active_tasks = _active_tasks


class JobStore(Protocol):
    def get_job(self, job_id: JobId) -> Optional[JobDict]:
        ...

    def get_all_jobs(self) -> List[JobDict]:
        ...

    def set_job(self, job_id: JobId, job_data: JobDict) -> None:
        ...

    def delete_job(self, job_id: JobId) -> bool:
        ...

    def job_exists(self, job_id: JobId) -> bool:
        ...

    def count_jobs(self) -> int:
        ...

    def get_jobs_by_status(self, status: str) -> List[JobDict]:
        ...

    def get_jobs_by_type(self, job_type: JobType) -> List[JobDict]:
        ...


class InMemoryJobStore:
    def __init__(self, backing: Dict[JobId, JobDict]) -> None:
        self._db = backing

    def get_job(self, job_id: JobId) -> Optional[JobDict]:
        return self._db.get(job_id)

    def get_all_jobs(self) -> List[JobDict]:
        return list(self._db.values())

    def set_job(self, job_id: JobId, job_data: JobDict) -> None:
        job_data.setdefault("job_id", job_id)
        self._db[job_id] = job_data

    def delete_job(self, job_id: JobId) -> bool:
        if job_id in self._db:
            del self._db[job_id]
            return True
        return False

    def job_exists(self, job_id: JobId) -> bool:
        return job_id in self._db

    def count_jobs(self) -> int:
        return len(self._db)

    def get_jobs_by_status(self, status: str) -> List[JobDict]:
        return [job for job in self._db.values() if job.get("status") == status]

    def get_jobs_by_type(self, job_type: JobType) -> List[JobDict]:
        return [job for job in self._db.values() if job.get("type") == job_type.value]


class RedisJobStore:
    def __init__(self, client: "Redis", key_prefix: str) -> None:
        self._client = client
        self._prefix = key_prefix

    def _key(self, job_id: JobId) -> str:
        return f"{self._prefix}{job_id}"

    def _parse(self, job_id: JobId, raw: Optional[str]) -> Optional[JobDict]:
        if raw is None:
            return None
        try:
            job = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning(f"Invalid job payload in Redis for {job_id}")
            return None
        job.setdefault("job_id", job_id)
        return job

    def get_job(self, job_id: JobId) -> Optional[JobDict]:
        raw = self._client.get(self._key(job_id))
        return self._parse(job_id, raw)

    def get_all_jobs(self) -> List[JobDict]:
        jobs: List[JobDict] = []
        pattern = f"{self._prefix}*"
        for key in self._client.scan_iter(match=pattern, count=200):
            key_str = str(key)
            if not key_str.startswith(self._prefix):
                continue
            job_id = key_str[len(self._prefix):]
            job = self.get_job(job_id)
            if job:
                jobs.append(job)
        return jobs

    def set_job(self, job_id: JobId, job_data: JobDict) -> None:
        job_data.setdefault("job_id", job_id)
        payload = json.dumps(job_data, ensure_ascii=True)
        self._client.set(self._key(job_id), payload)

    def delete_job(self, job_id: JobId) -> bool:
        return bool(self._client.delete(self._key(job_id)))

    def job_exists(self, job_id: JobId) -> bool:
        return bool(self._client.exists(self._key(job_id)))

    def count_jobs(self) -> int:
        return len(self.get_all_jobs())

    def get_jobs_by_status(self, status: str) -> List[JobDict]:
        return [job for job in self.get_all_jobs() if job.get("status") == status]

    def get_jobs_by_type(self, job_type: JobType) -> List[JobDict]:
        return [job for job in self.get_all_jobs() if job.get("type") == job_type.value]


def _create_job_store() -> JobStore:
    backend = settings.JOB_STORE_BACKEND.lower()
    if backend == "redis":
        try:
            from redis import Redis

            client = Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT,
            )
            client.ping()
            logger.info("Using Redis job store")
            return RedisJobStore(client, settings.REDIS_JOB_KEY_PREFIX)
        except Exception as e:
            logger.warning(f"Redis unavailable, falling back to memory: {e}")

    logger.info("Using in-memory job store")
    return InMemoryJobStore(_jobs_db)


_JOB_STORE: JobStore = _create_job_store()


def configure_job_store() -> None:
    """Recreate the job store based on current settings."""
    global _JOB_STORE
    _JOB_STORE = _create_job_store()


def get_job(job_id: JobId) -> Optional[JobDict]:
    return _JOB_STORE.get_job(job_id)


def get_all_jobs() -> List[JobDict]:
    return _JOB_STORE.get_all_jobs()


def set_job(job_id: JobId, job_data: JobDict) -> None:
    _JOB_STORE.set_job(job_id, job_data)


def delete_job(job_id: JobId) -> bool:
    return _JOB_STORE.delete_job(job_id)


def job_exists(job_id: JobId) -> bool:
    return _JOB_STORE.job_exists(job_id)


def count_jobs() -> int:
    return _JOB_STORE.count_jobs()


def get_task(job_id: JobId) -> Optional[asyncio.Task[None]]:
    return _active_tasks.get(job_id)


def set_task(job_id: JobId, task: asyncio.Task[None]) -> None:
    _active_tasks[job_id] = task


def delete_task(job_id: JobId) -> bool:
    if job_id in _active_tasks:
        del _active_tasks[job_id]
        return True
    return False


def task_exists(job_id: JobId) -> bool:
    return job_id in _active_tasks


def create_job(job_id: JobId, job_data: JobDict) -> JobDict:
    _JOB_STORE.set_job(job_id, job_data)
    return job_data


def clear_all_jobs() -> int:
    jobs = get_all_jobs()
    for job in jobs:
        job_id = job.get("job_id")
        if job_id:
            delete_job(str(job_id))
    for task in list(_active_tasks.values()):
        try:
            task.cancel()
        except Exception:
            pass
    _active_tasks.clear()
    return len(jobs)


def get_jobs_by_status(status: str) -> List[JobDict]:
    return _JOB_STORE.get_jobs_by_status(status)


def get_jobs_by_type(job_type: JobType) -> List[JobDict]:
    return _JOB_STORE.get_jobs_by_type(job_type)
