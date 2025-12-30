"""
Catalog module schemas (Pydantic models)
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, ConfigDict


class CatalogStatusResponse(BaseModel):
    """Catalog status response"""
    enabled: bool
    db_path: str
    counts: Dict[str, int]
    state: Dict[str, Dict[str, Any]]


class CatalogBootstrapResponse(BaseModel):
    """Response for local catalog bootstrap"""
    deleted: int
    inserted: int


class CatalogDriveImportResponse(BaseModel):
    """Response for drive catalog import"""
    model_config = ConfigDict(extra="allow")

    status: str
    message: Optional[str] = None
    file_id: Optional[str] = None
    deleted: Optional[int] = None
    inserted: Optional[int] = None
    generated_at: Optional[str] = None


class CatalogDrivePublishResponse(BaseModel):
    """Response for drive catalog publish"""
    status: str
    file_id: Optional[str] = None
    name: Optional[str] = None
    size: Optional[int] = None
    generated_at: Optional[str] = None
    videos: Optional[int] = None


class CatalogDriveRebuildResponse(BaseModel):
    """Response for drive catalog rebuild (sync)"""
    deleted: int
    inserted: int
    published: Optional[CatalogDrivePublishResponse] = None


class CatalogJobResponse(BaseModel):
    """Response for catalog background jobs"""
    status: str
    job_id: str
    message: str
