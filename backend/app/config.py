"""
Application configuration
"""
from pathlib import Path


class Settings:
    """Global application settings"""

    # App info
    APP_NAME: str = "YT-Archiver API"
    APP_VERSION: str = "2.0.0"
    APP_DESCRIPTION: str = "API para download de vídeos do YouTube e streams HLS"

    # Logging
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]

    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    DOWNLOADS_DIR: str = "./downloads"
    ARCHIVE_FILE: str = "./archive.txt"

    # Google Drive
    DRIVE_CREDENTIALS_PATH: str = "./credentials.json"
    DRIVE_TOKEN_PATH: str = "./token.json"

    # Video extensions
    VIDEO_EXTENSIONS: set = {'.mp4', '.mkv', '.webm', '.avi', '.mov', '.flv', '.wmv'}

    # Thumbnail extensions
    THUMBNAIL_EXTENSIONS: list = ['.jpg', '.jpeg', '.png', '.webp']

    # MIME types
    VIDEO_MIME_TYPES: dict = {
        '.mp4': 'video/mp4',
        '.webm': 'video/webm',
        '.mkv': 'video/x-matroska',
        '.avi': 'video/x-msvideo',
        '.mov': 'video/quicktime',
    }

    IMAGE_MIME_TYPES: dict = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.webp': 'image/webp',
    }


settings = Settings()
