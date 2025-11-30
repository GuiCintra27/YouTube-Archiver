"""
Library service - business logic for local video library
"""
import re
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

from app.config import settings
from app.core.logging import get_module_logger
from app.core.security import validate_path_within_base, validate_file_exists, sanitize_path
from .cache import video_cache

logger = get_module_logger("library")


def scan_videos_directory(base_dir: str = "./downloads", use_cache: bool = True) -> List[Dict[str, Any]]:
    """
    Scan the downloads directory and return list of videos with metadata.
    Structure expected: downloads/[channel]/[subcategory]/video.mp4

    Uses caching to avoid repeated I/O operations. Cache is invalidated
    automatically after TTL or when videos are added/deleted.

    Args:
        base_dir: Base directory to scan
        use_cache: Whether to use cached results (default True)

    Returns:
        List of video metadata dicts
    """
    # Check cache first
    if use_cache:
        cached = video_cache.get(base_dir)
        if cached is not None:
            return cached

    videos = []
    base_path = Path(base_dir)

    if not base_path.exists():
        return videos

    logger.debug(f"Scanning directory: {base_dir}")

    # Scan recursively
    for video_file in base_path.rglob('*'):
        if video_file.suffix.lower() in settings.VIDEO_EXTENSIONS:
            # Calculate relative path
            rel_path = video_file.relative_to(base_path)
            parts = rel_path.parts

            # Extract "channel" (first folder in hierarchy)
            channel = parts[0] if len(parts) > 1 else "Sem categoria"

            # Video name (without extension)
            title = video_file.stem

            # Find thumbnail
            thumbnail = None
            for thumb_ext in settings.THUMBNAIL_EXTENSIONS:
                thumb_path = video_file.with_suffix(thumb_ext)
                if thumb_path.exists():
                    thumbnail = str(thumb_path.relative_to(base_path))
                    break

            # File info
            stat = video_file.stat()

            videos.append({
                "id": str(rel_path),
                "title": title,
                "channel": channel,
                "path": str(rel_path),
                "thumbnail": thumbnail,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })

    # Sort by modification date (newest first)
    videos.sort(key=lambda x: x["modified_at"], reverse=True)

    # Cache the results
    video_cache.set(base_dir, videos)
    logger.debug(f"Scanned {len(videos)} videos from {base_dir}")

    return videos


def get_paginated_videos(
    base_dir: str = "./downloads",
    page: int = 1,
    limit: Optional[int] = None
) -> dict:
    """
    Get paginated list of videos.

    Args:
        base_dir: Base directory to scan
        page: Page number (1-indexed)
        limit: Items per page (None for all)

    Returns:
        Dict with total, page, limit, and videos
    """
    videos = scan_videos_directory(base_dir)
    total = len(videos)

    if limit:
        start = (page - 1) * limit
        end = start + limit
        videos = videos[start:end]

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "videos": videos,
    }


def delete_video_with_related(
    video_path: str,
    base_dir: str = "./downloads",
    archive_file: str = "./archive.txt"
) -> dict:
    """
    Delete a video and its related files (thumbnail, subtitles, etc).

    Args:
        video_path: Relative path to video
        base_dir: Base directory
        archive_file: Archive file path

    Returns:
        Dict with deletion results
    """
    # Sanitize and validate path
    video_path = sanitize_path(video_path)
    full_path = Path(base_dir) / video_path
    base_path = Path(base_dir)

    # Validate path is within base_dir
    validate_path_within_base(full_path, base_path)
    validate_file_exists(full_path)

    # Find related files (same name, different extensions)
    related_files = []
    base_name = full_path.stem
    parent_dir = full_path.parent

    # Find files with same base name
    for file in parent_dir.iterdir():
        if file.is_file():
            if file.name.startswith(base_name + "."):
                related_files.append(file)

    # Extract video ID from filename for archive removal
    video_id = None
    match = re.search(r'\[([^\]]+)\]', base_name)
    if match:
        video_id = match.group(1)

    # Delete all related files
    deleted_files = []
    for file in related_files:
        try:
            file.unlink()
            deleted_files.append(str(file.relative_to(base_path)))
        except Exception as e:
            logger.error(f"Error deleting {file}: {e}")

    # Remove from archive file if ID found
    if video_id:
        _remove_from_archive(archive_file, video_id)

    # Try to remove empty directories (cleanup)
    _cleanup_empty_dirs(parent_dir, base_path)

    # Invalidate cache after deletion
    video_cache.invalidate(base_dir)
    logger.info(f"Deleted video: {video_path} ({len(deleted_files)} files)")

    return {
        "status": "success",
        "message": "Vídeo excluído com sucesso",
        "deleted_files": deleted_files,
        "removed_from_archive": video_id is not None,
    }


def _remove_from_archive(archive_file: str, video_id: str) -> None:
    """Remove video ID from archive file"""
    archive_path = Path(archive_file)
    if not archive_path.exists():
        return

    try:
        with open(archive_path, "r") as f:
            lines = f.readlines()

        filtered_lines = [line for line in lines if video_id not in line]

        with open(archive_path, "w") as f:
            f.writelines(filtered_lines)

        logger.debug(f"Removed '{video_id}' from archive file")
    except Exception as e:
        logger.error(f"Error removing from archive: {e}")


def _cleanup_empty_dirs(directory: Path, base_dir: Path) -> None:
    """Remove empty directories after file deletion"""
    try:
        if directory != base_dir and not any(directory.iterdir()):
            directory.rmdir()
            # Try parent too
            grandparent = directory.parent
            if grandparent != base_dir and not any(grandparent.iterdir()):
                grandparent.rmdir()
    except Exception:
        pass
