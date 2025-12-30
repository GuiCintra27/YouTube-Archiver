"""
Jobs module schemas (Pydantic models)
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field


class JobStatus(BaseModel):
    """Job status response"""
    model_config = ConfigDict(extra="allow")

    job_id: str
    status: str  # pending, downloading, completed, error, cancelled
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    url: Optional[str] = None
    progress: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class JobListResponse(BaseModel):
    """Response for job list"""
    total: int
    jobs: List[JobStatus]


class JobActionResponse(BaseModel):
    """Response for job actions (cancel, delete)"""
    status: str
    message: str
