"""
Unit tests for jobs service state transitions.
"""
from typing import Dict

import pytest

from app.jobs import store as jobs_store
from app.jobs.service import update_job_progress, complete_job, fail_job, cancel_job
from app.jobs.store import InMemoryJobStore


@pytest.fixture
def memory_job_store(monkeypatch: pytest.MonkeyPatch) -> Dict[str, dict]:
    db: Dict[str, dict] = {}
    monkeypatch.setattr(jobs_store, "_JOB_STORE", InMemoryJobStore(db))
    return db


def _seed_job(job_id: str) -> None:
    jobs_store.set_job(
        job_id,
        {
            "job_id": job_id,
            "status": "pending",
            "created_at": "2024-01-01T00:00:00",
            "progress": {},
            "result": None,
            "error": None,
        },
    )


def test_update_job_progress_persists_status(memory_job_store: Dict[str, dict]) -> None:
    job_id = "job-1"
    _seed_job(job_id)
    update_job_progress(job_id, {"status": "downloading", "percent": 10})
    job = jobs_store.get_job(job_id)
    assert job["status"] == "downloading"
    assert job["progress"]["percent"] == 10


def test_complete_job_marks_completed(memory_job_store: Dict[str, dict]) -> None:
    job_id = "job-2"
    _seed_job(job_id)
    complete_job(job_id, {"status": "success"})
    job = jobs_store.get_job(job_id)
    assert job["status"] == "completed"
    assert job["result"]["status"] == "success"
    assert job["progress"]["status"] == "completed"
    assert "completed_at" in job


def test_fail_job_marks_error(memory_job_store: Dict[str, dict]) -> None:
    job_id = "job-3"
    _seed_job(job_id)
    fail_job(job_id, "boom")
    job = jobs_store.get_job(job_id)
    assert job["status"] == "error"
    assert job["error"] == "boom"
    assert "completed_at" in job


def test_cancel_job_marks_cancelled(memory_job_store: Dict[str, dict]) -> None:
    job_id = "job-4"
    _seed_job(job_id)
    cancel_job(job_id)
    job = jobs_store.get_job(job_id)
    assert job["status"] == "cancelled"
    assert job["error"] == "Download cancelado pelo usuário"
    assert "completed_at" in job
