"""
Application configuration with environment variable support.

Settings can be configured via:
1. Environment variables (highest priority)
2. .env file in the backend directory
3. Default values defined below

Example .env file:
    APP_NAME=YT-Archiver API
    LOG_LEVEL=DEBUG
    DOWNLOADS_DIR=./my-downloads
"""
from pathlib import Path
from typing import List, Set, Dict

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Global application settings.

    All settings can be overridden via environment variables.
    Environment variables are case-insensitive and can use either
    underscores or the exact field name.
    """

    # App info
    APP_NAME: str = Field(
        default="YT-Archiver API",
        description="Application name displayed in API docs"
    )
    APP_VERSION: str = Field(
        default="2.0.0",
        description="Application version"
    )
    APP_DESCRIPTION: str = Field(
        default="API para download de vídeos do YouTube e streams HLS",
        description="Application description for API docs"
    )

    # Server
    HOST: str = Field(
        default="0.0.0.0",
        description="Server host"
    )
    PORT: int = Field(
        default=8000,
        description="Server port"
    )

    # Logging
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    # CORS - comma-separated string for env var, converted to list
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:3001,http://localhost:3002",
        description="Allowed CORS origins (comma-separated)"
    )

    # Paths
    DOWNLOADS_DIR: str = Field(
        default="./downloads",
        description="Directory for downloaded videos"
    )
    ARCHIVE_FILE: str = Field(
        default="./archive.txt",
        description="File to track downloaded videos"
    )

    # Google Drive
    DRIVE_CREDENTIALS_PATH: str = Field(
        default="./credentials.json",
        description="Path to Google OAuth credentials file"
    )
    DRIVE_TOKEN_PATH: str = Field(
        default="./token.json",
        description="Path to Google OAuth token file"
    )
    DRIVE_ROOT_FOLDER: str = Field(
        default="YouTube Archiver",
        description="Root folder name in Google Drive"
    )

    # Download defaults
    DEFAULT_MAX_RESOLUTION: int = Field(
        default=1080,
        description="Default maximum video resolution"
    )
    DEFAULT_CONCURRENT_FRAGMENTS: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Default concurrent fragment downloads"
    )

    # Job settings
    JOB_EXPIRY_HOURS: int = Field(
        default=24,
        ge=1,
        description="Hours after which completed jobs are cleaned up"
    )

    # Drive Cache settings
    DRIVE_CACHE_DB_PATH: str = Field(
        default="./drive_cache.db",
        description="Path to SQLite cache database file"
    )
    DRIVE_CACHE_SYNC_INTERVAL: int = Field(
        default=30,
        ge=5,
        le=1440,
        description="Minutes between automatic cache sync (5-1440)"
    )
    DRIVE_CACHE_ENABLED: bool = Field(
        default=True,
        description="Enable/disable Drive cache"
    )
    DRIVE_CACHE_FALLBACK_TO_API: bool = Field(
        default=True,
        description="Fall back to direct API if cache unavailable"
    )

    # Pydantic settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields in .env
    )

    # Computed property for BASE_DIR
    @property
    def BASE_DIR(self) -> Path:
        """Base directory of the backend application"""
        return Path(__file__).parent.parent

    # Computed property to convert CORS string to list
    @property
    def cors_origins_list(self) -> List[str]:
        """CORS origins as a list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # Static configurations - imported from core.constants for consistency
    # These are duplicated here for backward compatibility with existing code
    # that accesses them via settings.VIDEO_EXTENSIONS etc.
    VIDEO_EXTENSIONS: Set[str] = {'.mp4', '.mkv', '.webm', '.avi', '.mov', '.flv', '.wmv', '.m4v'}
    THUMBNAIL_EXTENSIONS: List[str] = ['.jpg', '.jpeg', '.png', '.webp']

    VIDEO_MIME_TYPES: Dict[str, str] = {
        '.mp4': 'video/mp4',
        '.webm': 'video/webm',
        '.mkv': 'video/x-matroska',
        '.avi': 'video/x-msvideo',
        '.mov': 'video/quicktime',
        '.flv': 'video/x-flv',
        '.wmv': 'video/x-ms-wmv',
        '.m4v': 'video/x-m4v',
    }

    IMAGE_MIME_TYPES: Dict[str, str] = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.webp': 'image/webp',
        '.gif': 'image/gif',
    }


# Singleton instance
settings = Settings()
