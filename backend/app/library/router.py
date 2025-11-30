"""
Library router - API endpoints for local video library
"""
import re
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse, FileResponse

from app.core.logging import get_module_logger
from app.core.rate_limit import limiter, RateLimits
from .service import get_paginated_videos, delete_video_with_related
from app.config import settings
from app.core.security import sanitize_path, validate_path_within_base, validate_file_exists, encode_filename_for_header
from app.core.exceptions import (
    VideoNotFoundException,
    ThumbnailNotFoundException,
    InvalidRequestException,
    InvalidRangeHeaderException,
    RangeNotSatisfiableException,
)

logger = get_module_logger("library")

router = APIRouter(prefix="/api/videos", tags=["library"])


@router.get("")
@limiter.limit(RateLimits.LIST_VIDEOS)
async def list_videos(request: Request, base_dir: str = "./downloads", page: int = 1, limit: Optional[int] = None):
    """Lista vídeos disponíveis na biblioteca (com paginação opcional)"""
    if page < 1:
        raise InvalidRequestException("Página deve ser >= 1")
    if limit is not None and limit <= 0:
        raise InvalidRequestException("Limite deve ser > 0")

    return get_paginated_videos(base_dir, page, limit)


@router.get("/stream/{video_path:path}")
@limiter.limit(RateLimits.STREAM_VIDEO)
async def stream_video(request: Request, video_path: str, base_dir: str = "./downloads"):
    """
    Serve o arquivo de vídeo para streaming.
    Suporta range requests para seek/skip.
    """
    try:
        # Sanitize and validate path
        video_path = sanitize_path(video_path)
        full_path = Path(base_dir) / video_path
        base_path = Path(base_dir)

        logger.debug(f"Streaming video: {video_path}")
        logger.debug(f"Full path: {full_path}")

        validate_file_exists(full_path)
        validate_path_within_base(full_path, base_path)

        # Detect MIME type
        file_ext = full_path.suffix.lower()
        media_type = settings.VIDEO_MIME_TYPES.get(file_ext, 'video/mp4')

        logger.debug(f"Media type: {media_type}, File size: {full_path.stat().st_size}")

        # Check for range request
        range_header = request.headers.get("range")

        if not range_header:
            # Normal response without range
            encoded_filename = encode_filename_for_header(full_path.name)
            return FileResponse(
                full_path,
                media_type=media_type,
                headers={
                    "Accept-Ranges": "bytes",
                    "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"
                }
            )

        # Process range request
        file_size = full_path.stat().st_size
        range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)

        if not range_match:
            raise InvalidRangeHeaderException()

        start = int(range_match.group(1))
        end = int(range_match.group(2)) if range_match.group(2) else file_size - 1

        if start >= file_size or end >= file_size or start > end:
            raise RangeNotSatisfiableException()

        chunk_size = end - start + 1

        def iterfile():
            with open(full_path, 'rb') as f:
                f.seek(start)
                remaining = chunk_size
                while remaining > 0:
                    read_size = min(8192, remaining)
                    data = f.read(read_size)
                    if not data:
                        break
                    remaining -= len(data)
                    yield data

        encoded_filename = encode_filename_for_header(full_path.name)
        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(chunk_size),
            "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"
        }

        return StreamingResponse(
            iterfile(),
            status_code=206,
            media_type=media_type,
            headers=headers
        )

    except (VideoNotFoundException, InvalidRangeHeaderException, RangeNotSatisfiableException):
        raise
    except Exception as e:
        logger.error(f"Exception in stream_video: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/thumbnail/{thumbnail_path:path}")
@limiter.limit(RateLimits.DEFAULT)
async def get_thumbnail(request: Request, thumbnail_path: str, base_dir: str = "./downloads"):
    """Serve a thumbnail do vídeo"""
    try:
        thumbnail_path = sanitize_path(thumbnail_path)
        full_path = Path(base_dir) / thumbnail_path
        base_path = Path(base_dir)

        if not full_path.exists() or not full_path.is_file():
            raise ThumbnailNotFoundException()

        validate_path_within_base(full_path, base_path)

        media_type = settings.IMAGE_MIME_TYPES.get(full_path.suffix.lower(), 'image/jpeg')

        return FileResponse(full_path, media_type=media_type)

    except ThumbnailNotFoundException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{video_path:path}")
@limiter.limit(RateLimits.DELETE)
async def delete_video(request: Request, video_path: str, base_dir: str = "./downloads"):
    """Exclui um vídeo e seus arquivos associados (thumbnail, legendas, etc)."""
    try:
        return delete_video_with_related(video_path, base_dir)
    except (VideoNotFoundException,):
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
