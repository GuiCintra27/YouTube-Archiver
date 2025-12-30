"""Core response schemas."""
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    worker_role: str
    catalog_enabled: bool
    metrics_enabled: bool
