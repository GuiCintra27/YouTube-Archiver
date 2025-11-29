"""
Drive module schemas (Pydantic models)
"""
from typing import Optional, List
from pydantic import BaseModel


class DriveAuthStatus(BaseModel):
    """Auth status response"""
    authenticated: bool
    credentials_exists: bool


class DriveAuthUrl(BaseModel):
    """Auth URL response"""
    auth_url: str


class DriveAuthResult(BaseModel):
    """OAuth callback result"""
    status: str
    message: str
    token: Optional[str] = None
    refresh_token: Optional[str] = None
    expiry: Optional[str] = None


class DriveVideo(BaseModel):
    """Video item in Drive"""
    id: str
    name: str
    path: str
    size: int
    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    thumbnail: Optional[str] = None


class DriveVideoListResponse(BaseModel):
    """Response for video list"""
    total: int
    page: int
    limit: int
    videos: List[DriveVideo]


class DriveUploadResult(BaseModel):
    """Upload result"""
    status: str
    message: Optional[str] = None
    file_id: Optional[str] = None
    file_name: Optional[str] = None
    size: Optional[int] = None
    related_files: Optional[List[str]] = None


class DriveSyncStatus(BaseModel):
    """Sync status between local and Drive"""
    local_only: List[str]
    drive_only: List[str]
    synced: List[str]
    total_local: int
    total_drive: int


class DriveSyncResult(BaseModel):
    """Sync all result"""
    total: int
    results: List[dict]


class DriveDeleteResult(BaseModel):
    """Delete result"""
    status: str
    message: str
