"""
Tests for jobs endpoints.
"""
import pytest
from fastapi.testclient import TestClient

from app.jobs import store as jobs_store


class TestListJobs:
    """Tests for GET /api/jobs endpoint."""

    def test_list_jobs_empty(self, client: TestClient):
        """Test listing jobs when no jobs exist."""
        response = client.get("/api/jobs")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["jobs"] == []

    def test_list_jobs_with_jobs(self, client: TestClient, mock_job: dict):
        """Test listing jobs when jobs exist."""
        response = client.get("/api/jobs")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["jobs"]) == 1
        assert data["jobs"][0]["id"] == mock_job["id"]


class TestGetJobStatus:
    """Tests for GET /api/jobs/{job_id} endpoint."""

    def test_get_job_exists(self, client: TestClient, mock_job: dict):
        """Test getting status of existing job."""
        response = client.get(f"/api/jobs/{mock_job['id']}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == mock_job["id"]
        assert data["status"] == "pending"

    def test_get_job_not_found(self, client: TestClient):
        """Test getting status of non-existent job."""
        response = client.get("/api/jobs/nonexistent-job")

        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == "JOB_NOT_FOUND"


class TestCancelJob:
    """Tests for POST /api/jobs/{job_id}/cancel endpoint."""

    def test_cancel_pending_job(self, client: TestClient, mock_job: dict):
        """Test cancelling a pending job."""
        response = client.post(f"/api/jobs/{mock_job['id']}/cancel")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        # Verify job is cancelled
        job = jobs_store.get_job(mock_job["id"])
        assert job["status"] == "cancelled"

    def test_cancel_completed_job_fails(self, client: TestClient):
        """Test that cancelling a completed job fails."""
        # Create a completed job
        job_id = "completed-job"
        jobs_store.create_job(job_id, {
            "id": job_id,
            "status": "completed",
        })

        response = client.post(f"/api/jobs/{job_id}/cancel")

        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "INVALID_REQUEST"

    def test_cancel_nonexistent_job(self, client: TestClient):
        """Test cancelling a non-existent job."""
        response = client.post("/api/jobs/nonexistent/cancel")

        assert response.status_code == 404


class TestDeleteJob:
    """Tests for DELETE /api/jobs/{job_id} endpoint."""

    def test_delete_job_exists(self, client: TestClient, mock_job: dict):
        """Test deleting an existing job."""
        response = client.delete(f"/api/jobs/{mock_job['id']}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        # Verify job is deleted
        assert not jobs_store.job_exists(mock_job["id"])

    def test_delete_job_not_found(self, client: TestClient):
        """Test deleting a non-existent job."""
        response = client.delete("/api/jobs/nonexistent-job")

        assert response.status_code == 404
