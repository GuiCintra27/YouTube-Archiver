"""
Unit tests for job store helpers.
"""
import asyncio
from typing import Dict

import pytest

from app.jobs import store as jobs_store
from app.jobs.store import InMemoryJobStore, JobType


@pytest.fixture
def memory_store(monkeypatch: pytest.MonkeyPatch) -> Dict[str, dict]:
    db: Dict[str, dict] = {}
    monkeypatch.setattr(jobs_store, "_JOB_STORE", InMemoryJobStore(db))
    return db


def test_set_and_get_job(memory_store: Dict[str, dict]) -> None:
    jobs_store.set_job("job-1", {"status": "pending"})
    job = jobs_store.get_job("job-1")
    assert job["job_id"] == "job-1"
    assert job["status"] == "pending"


def test_get_jobs_by_status(memory_store: Dict[str, dict]) -> None:
    jobs_store.set_job("job-a", {"status": "pending"})
    jobs_store.set_job("job-b", {"status": "completed"})
    pending = jobs_store.get_jobs_by_status("pending")
    assert len(pending) == 1
    assert pending[0]["job_id"] == "job-a"


def test_get_jobs_by_type(memory_store: Dict[str, dict]) -> None:
    jobs_store.set_job("job-a", {"status": "pending", "type": JobType.DOWNLOAD.value})
    jobs_store.set_job("job-b", {"status": "pending", "type": JobType.DRIVE_SYNC.value})
    downloads = jobs_store.get_jobs_by_type(JobType.DOWNLOAD)
    assert len(downloads) == 1
    assert downloads[0]["job_id"] == "job-a"


def test_create_job_sets_id(memory_store: Dict[str, dict]) -> None:
    jobs_store.create_job("job-2", {"status": "pending"})
    job = jobs_store.get_job("job-2")
    assert job["job_id"] == "job-2"


@pytest.mark.asyncio
async def test_clear_all_jobs_clears_tasks(memory_store: Dict[str, dict]) -> None:
    jobs_store.set_job("job-3", {"status": "pending"})
    task = asyncio.create_task(asyncio.sleep(10))
    jobs_store.set_task("job-3", task)

    removed = jobs_store.clear_all_jobs()
    assert removed == 1
    assert jobs_store.get_all_jobs() == []
    assert not jobs_store.task_exists("job-3")

    try:
        await task
    except asyncio.CancelledError:
        pass
