"""
Library module schemas (Pydantic models)
"""
from typing import Optional, List
from pydantic import BaseModel


class VideoItem(BaseModel):
    """Video item in the library"""
    id: str
    title: str
    channel: str
    path: str
    thumbnail: Optional[str] = None
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
