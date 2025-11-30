"""
Jobs router - API endpoints for job management
"""
import asyncio
import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.core.rate_limit import limiter, RateLimits
from . import store
from .service import cancel_job
from app.core.exceptions import JobNotFoundException, InvalidRequestException

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("")
@limiter.limit(RateLimits.GET_STATUS)
async def list_jobs(request: Request):
    """Lista todos os jobs"""
    jobs = store.get_all_jobs()
    return {
        "total": len(jobs),
        "jobs": jobs,
    }


@router.get("/{job_id}")
@limiter.limit(RateLimits.GET_STATUS)
async def get_job_status(request: Request, job_id: str):
    """Obtém o status de um job"""
    job = store.get_job(job_id)
    if not job:
        raise JobNotFoundException()
    return job


@router.post("/{job_id}/cancel")
@limiter.limit(RateLimits.DELETE)
async def cancel_job_endpoint(request: Request, job_id: str):
    """Cancela um job em execução"""
    job = store.get_job(job_id)
    if not job:
        raise JobNotFoundException()

    # Only cancel running jobs
    if job["status"] not in ["pending", "downloading"]:
        raise InvalidRequestException("Job não está em execução")

    # Cancel task if exists
    task = store.get_task(job_id)
    if task:
        task.cancel()
        store.delete_task(job_id)

    # Mark as cancelled
    cancel_job(job_id)

    return {"status": "success", "message": "Download cancelado"}


@router.delete("/{job_id}")
@limiter.limit(RateLimits.DELETE)
async def delete_job(request: Request, job_id: str):
    """Remove um job do histórico"""
    if not store.job_exists(job_id):
        raise JobNotFoundException()

    # Cancel first if running
    task = store.get_task(job_id)
    if task:
        task.cancel()
        store.delete_task(job_id)

    store.delete_job(job_id)
    return {"status": "success", "message": "Job removido"}


@router.get("/{job_id}/stream")
@limiter.limit(RateLimits.GET_STATUS)
async def stream_job_progress(request: Request, job_id: str):
    """Stream de progresso em tempo real usando Server-Sent Events (SSE)"""
    if not store.job_exists(job_id):
        raise JobNotFoundException()

    async def event_generator():
        last_progress = None
        while True:
            job = store.get_job(job_id)
            if not job:
                break

            current_progress = job.get("progress", {})

            # Send update if changed
            if current_progress != last_progress:
                yield f"data: {json.dumps(job)}\n\n"
                last_progress = current_progress.copy() if current_progress else None

            # Stop if job finished
            if job["status"] in ["completed", "error", "cancelled"]:
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
