"""
Drive module schemas (Pydantic models)
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


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
    custom_thumbnail_id: Optional[str] = None


class DriveVideoListResponse(BaseModel):
    """Response for video list"""
    total: int
    page: int
    limit: int
    videos: List[DriveVideo]
    warning: Optional[str] = None


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
    local_only: Optional[List[str]] = None
    drive_only: Optional[List[str]] = None
    synced: Optional[List[str]] = None
    total_local: int
    total_drive: int
    local_only_count: int
    drive_only_count: int
    synced_count: int
    warnings: Optional[List[str]] = None


class DriveSyncItem(BaseModel):
    """Paginated sync item"""
    path: str
    file_id: Optional[str] = None


class DriveSyncItemsResponse(BaseModel):
    """Response for paginated sync items"""
    kind: str
    total: int
    page: int
    limit: int
    items: List[DriveSyncItem]


class DriveSyncResult(BaseModel):
    """Sync all result"""
    total: int
    results: List[dict]


class DriveDeleteResult(BaseModel):
    """Delete result"""
    model_config = ConfigDict(extra="allow")

    status: str
    message: str


class DriveJobResponse(BaseModel):
    """Response for background Drive jobs"""
    status: str
    job_id: str
    message: str


class DriveExternalUploadResponse(DriveJobResponse):
    """Response for external upload job"""
    folder_name: str
    files_count: int


class DriveShareStatusResponse(BaseModel):
    """Response for share status or update"""
    status: str
    shared: bool
    link: Optional[str] = None


class DriveRenameResponse(BaseModel):
    """Response for Drive rename"""
    status: str
    message: Optional[str] = None
    file_id: str
    new_name: str
    renamed_related: List[str]


class DriveThumbnailUpdateResponse(BaseModel):
    """Response for Drive thumbnail update"""
    status: str
    message: Optional[str] = None
    thumbnail_id: str
    thumbnail_name: str
