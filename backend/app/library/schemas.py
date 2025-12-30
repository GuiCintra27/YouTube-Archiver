"""
Library module schemas (Pydantic models)
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class VideoItem(BaseModel):
    """Video item in the library"""
    model_config = ConfigDict(extra="allow")

    id: str
    title: str
    channel: str
    path: str
    thumbnail: Optional[str] = None
    duration: Optional[str] = None
    duration_seconds: Optional[int] = None
    size: int
    created_at: str
    modified_at: str


class VideoListResponse(BaseModel):
    """Response for video list"""
    total: int
    page: int
    limit: Optional[int] = None
    videos: List[VideoItem]


class DeleteVideoResponse(BaseModel):
    """Response for video deletion"""
    status: str
    message: str
    deleted_files: List[str]
    removed_from_archive: bool


class BatchDeleteResponse(BaseModel):
    """Response for batch video deletion"""
    status: str
    message: str
    deleted: List[Dict[str, Any]]
    failed: List[Dict[str, Any]]
    total_deleted: int
    total_failed: int


class RenameVideoResponse(BaseModel):
    """Response for video rename"""
    status: str
    message: str
    new_path: str
    renamed_files: List[Dict[str, str]]


class ThumbnailUpdateResponse(BaseModel):
    """Response for thumbnail update"""
    status: str
    message: str
    thumbnail_path: str
