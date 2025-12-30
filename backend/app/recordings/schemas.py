"""
Recordings module schemas (Pydantic models)
"""
from pydantic import BaseModel


class RecordingUploadResponse(BaseModel):
    """Response for recording upload"""
    status: str
    path: str
    full_path: str
    message: str
