"""
Jobs module schemas (Pydantic models)
"""
from typing import Optional
from pydantic import BaseModel


class JobStatus(BaseModel):
    """Job status response"""
    job_id: str
    status: str  # pending, downloading, completed, error, cancelled
    created_at: str
    url: str
    progress: dict = {}
    result: Optional[dict] = None
    error: Optional[str] = None


class JobListResponse(BaseModel):
    """Response for job list"""
    total: int
    jobs: list


class JobActionResponse(BaseModel):
    """Response for job actions (cancel, delete)"""
    status: str
    message: str
