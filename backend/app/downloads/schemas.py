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
    """Request to get video information without downloading."""

    url: str = Field(
        ...,
        description="URL do vídeo ou playlist do YouTube",
        json_schema_extra={"example": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            }
        }
    }

    @field_validator('url')
    @classmethod
    def validate_url_field(cls, v: str) -> str:
        return validate_url(v)


class DownloadRequest(BaseModel):
    """
    Request to start a video download.

    Supports single videos, playlists, and batch downloads from text files.
    Includes options for quality control, subtitles, anti-ban measures, and more.
    """

    # Core settings
    url: str = Field(
        ...,
        description="URL do vídeo, playlist ou arquivo .txt com URLs",
        json_schema_extra={"example": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    )
    archive_file: str = Field(
        default="./archive.txt",
        description="Arquivo de controle para evitar downloads duplicados"
    )

    # Quality settings
    fmt: str = Field(
        default="bv*+ba/b",
        description="Formato yt-dlp (bv*+ba/b = melhor vídeo + melhor áudio)"
    )
    max_res: Optional[int] = Field(
        default=None,
        description="Resolução máxima em pixels (720, 1080, 1440, 2160)",
        ge=1,
        le=4320
    )
    audio_only: bool = Field(
        default=False,
        description="Extrair apenas áudio em formato MP3"
    )

    # Subtitles settings
    subs: bool = Field(default=True, description="Baixar legendas manuais")
    auto_subs: bool = Field(default=True, description="Baixar legendas automáticas")
    sub_langs: str = Field(
        default="pt,en",
        description="Idiomas de legendas separados por vírgula"
    )

    # Media settings
    thumbnails: bool = Field(default=True, description="Baixar miniaturas/thumbnails")

    # Playlist settings
    limit: Optional[int] = Field(
        default=None,
        description="Limitar quantidade de vídeos da playlist",
        ge=1
    )

    # Authentication
    cookies_file: Optional[str] = Field(
        default=None,
        description="Caminho para arquivo de cookies (formato Netscape)"
    )

    # HTTP Headers
    referer: Optional[str] = Field(default=None, description="Header Referer para requests")
    origin: Optional[str] = Field(default=None, description="Header Origin para requests")
    user_agent: str = Field(default="yt-archiver", description="User Agent string")

    # Performance
    concurrent_fragments: int = Field(
        default=10,
        description="Número de fragmentos baixados simultaneamente",
        ge=1,
        le=50
    )

    # File naming
    path: Optional[str] = Field(
        default=None,
        description="Subpasta personalizada dentro do diretório de saída"
    )
    file_name: Optional[str] = Field(
        default=None,
        description="Nome personalizado para o arquivo (sem extensão)"
    )
    archive_id: Optional[str] = Field(
        default=None,
        description="ID customizado para o arquivo de archive"
    )

    # Anti-ban / Rate limiting
    delay_between_downloads: int = Field(
        default=0,
        description="Segundos de delay entre downloads (anti-ban)",
        ge=0,
        le=300
    )
    batch_size: Optional[int] = Field(
        default=None,
        description="Quantidade de vídeos por batch antes de pausar",
        ge=1,
        le=100
    )
    batch_delay: int = Field(
        default=0,
        description="Segundos de pausa entre batches",
        ge=0,
        le=300
    )
    randomize_delay: bool = Field(
        default=False,
        description="Adicionar variação aleatória aos delays"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    "max_res": 1080,
                    "subs": True,
                    "thumbnails": True
                },
                {
                    "url": "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf",
                    "max_res": 720,
                    "limit": 10,
                    "delay_between_downloads": 5,
                    "batch_size": 5,
                    "batch_delay": 30
                }
            ]
        }
    }

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
    """
    Response containing video or playlist metadata.

    The response varies depending on the type of content:
    - For single videos: includes title, uploader, duration, view_count
    - For playlists: includes title, uploader, video_count
    """

    status: str = Field(description="Status da operação (success ou error)")
    type: Optional[str] = Field(
        default=None,
        description="Tipo de conteúdo: 'video' ou 'playlist'"
    )
    title: Optional[str] = Field(default=None, description="Título do vídeo ou playlist")
    uploader: Optional[str] = Field(default=None, description="Nome do canal/uploader")
    duration: Optional[int] = Field(
        default=None,
        description="Duração em segundos (apenas para vídeos)"
    )
    view_count: Optional[int] = Field(
        default=None,
        description="Contagem de visualizações"
    )
    thumbnail: Optional[str] = Field(default=None, description="URL da thumbnail")
    video_count: Optional[int] = Field(
        default=None,
        description="Número de vídeos (apenas para playlists)"
    )
    error: Optional[str] = Field(default=None, description="Mensagem de erro, se houver")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "type": "video",
                "title": "Never Gonna Give You Up",
                "uploader": "Rick Astley",
                "duration": 212,
                "view_count": 1500000000,
                "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"
            }
        }
    }


class DownloadResponse(BaseModel):
    """
    Response after starting a download job.

    The download runs asynchronously in the background.
    Use the job_id to poll for progress at /api/jobs/{job_id}.
    """

    status: str = Field(description="Status da operação (success)")
    job_id: str = Field(description="ID único do job para acompanhamento")
    message: str = Field(description="Mensagem de confirmação")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "job_id": "abc123-def456-ghi789",
                "message": "Download iniciado"
            }
        }
    }
