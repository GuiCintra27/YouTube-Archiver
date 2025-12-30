"""
Integration tests for jobs SSE endpoint.
"""
import json

import pytest
import httpx

from app.jobs import store as jobs_store


@pytest.mark.asyncio
async def test_job_stream_emits_event(client: httpx.AsyncClient) -> None:
    job_id = "job-stream-1"
    jobs_store.set_job(
        job_id,
        {
            "job_id": job_id,
            "status": "completed",
            "created_at": "2024-01-01T00:00:00",
            "progress": {},
            "result": {"status": "success"},
            "error": None,
        },
    )

    async with client.stream("GET", f"/api/jobs/{job_id}/stream") as response:
        assert response.status_code == 200
        data_line = None
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data_line = line
                break
        assert data_line is not None
        payload = json.loads(data_line.replace("data: ", ""))
        assert payload["job_id"] == job_id
