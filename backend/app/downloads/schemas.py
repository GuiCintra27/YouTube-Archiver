"""
Download module schemas (Pydantic models)
"""
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from app.core.validators import (
    validate_url,
    validate_path_safe,
    validate_resolution,
    validate_delay,
    validate_batch_size,
    sanitize_filename,
)


class VideoInfoRequest(BaseModel):
    """Request to get video information"""
    url: str = Field(..., description="URL do vídeo ou playlist")

    @field_validator('url')
    @classmethod
    def validate_url_field(cls, v: str) -> str:
        return validate_url(v)


class DownloadRequest(BaseModel):
    """Request to start a download"""
    url: str = Field(..., description="URL do vídeo, playlist ou arquivo .txt")
    out_dir: str = Field(default="./downloads", description="Diretório de saída")
    archive_file: str = Field(default="./archive.txt", description="Arquivo de controle de downloads")
    fmt: str = Field(default="bv*+ba/b", description="Formato do vídeo")
    max_res: Optional[int] = Field(default=None, description="Resolução máxima (altura)", ge=1, le=4320)
    subs: bool = Field(default=True, description="Baixar legendas")
    auto_subs: bool = Field(default=True, description="Baixar legendas automáticas")
    sub_langs: str = Field(default="pt,en", description="Idiomas de legendas")
    thumbnails: bool = Field(default=True, description="Baixar miniaturas")
    audio_only: bool = Field(default=False, description="Apenas áudio (MP3)")
    limit: Optional[int] = Field(default=None, description="Limitar itens de playlist", ge=1)
    cookies_file: Optional[str] = Field(default=None, description="Arquivo de cookies")
    referer: Optional[str] = Field(default=None, description="Header Referer")
    origin: Optional[str] = Field(default=None, description="Header Origin")
    user_agent: str = Field(default="yt-archiver", description="User Agent")
    concurrent_fragments: int = Field(default=10, description="Fragmentos simultâneos", ge=1, le=50)
    path: Optional[str] = Field(default=None, description="Subpasta personalizada")
    file_name: Optional[str] = Field(default=None, description="Nome do arquivo")
    archive_id: Optional[str] = Field(default=None, description="ID customizado para archive")
    # Anti-ban / Rate limiting
    delay_between_downloads: int = Field(default=0, description="Segundos entre vídeos (anti-ban)", ge=0, le=300)
    batch_size: Optional[int] = Field(default=None, description="Vídeos por batch (0=desabilitado)", ge=1, le=100)
    batch_delay: int = Field(default=0, description="Segundos entre batches", ge=0, le=300)
    randomize_delay: bool = Field(default=False, description="Randomizar delays")

    @field_validator('url')
    @classmethod
    def validate_url_field(cls, v: str) -> str:
        return validate_url(v)

    @field_validator('path')
    @classmethod
    def validate_path_field(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return validate_path_safe(v)

    @field_validator('file_name')
    @classmethod
    def validate_filename_field(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        return sanitize_filename(v)

    @field_validator('referer', 'origin')
    @classmethod
    def validate_header_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        return validate_url(v)


class VideoInfoResponse(BaseModel):
    """Response with video information"""
    status: str
    type: Optional[str] = None
    title: Optional[str] = None
    uploader: Optional[str] = None
    duration: Optional[int] = None
    view_count: Optional[int] = None
    thumbnail: Optional[str] = None
    video_count: Optional[int] = None
    error: Optional[str] = None


class DownloadResponse(BaseModel):
    """Response after starting a download"""
    status: str
    job_id: str
    message: str
