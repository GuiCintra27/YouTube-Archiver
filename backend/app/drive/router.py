"""
Drive router - API endpoints for Google Drive integration
"""
import shutil
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, Request, File, Form, UploadFile
from fastapi.responses import StreamingResponse, Response

from .service import (
    get_auth_status,
    get_auth_url,
    exchange_auth_code,
    list_videos_paginated,
    upload_video,
    upload_single_video,
    upload_external_files,
    get_sync_status,
    sync_all_videos,
    delete_video,
    delete_videos_batch,
    stream_video,
    get_thumbnail,
    get_custom_thumbnail,
    download_single_from_drive,
    download_all_from_drive,
)
from .manager import drive_manager
from app.core.exceptions import (
    DriveNotAuthenticatedException,
    DriveCredentialsNotFoundException,
    InvalidRequestException,
    ThumbnailNotFoundException,
)
from app.core.rate_limit import limiter, RateLimits

router = APIRouter(prefix="/api/drive", tags=["drive"])


def _require_auth():
    """Helper to check Drive authentication"""
    if not drive_manager.is_authenticated():
        raise DriveNotAuthenticatedException()


@router.get("/auth-status")
@limiter.limit(RateLimits.GET_STATUS)
async def auth_status(request: Request):
    """Check if user is authenticated with Google Drive"""
    return get_auth_status()


@router.get("/auth-url")
@limiter.limit(RateLimits.AUTH)
async def auth_url(request: Request):
    """Generate OAuth authentication URL"""
    try:
        url = get_auth_url()
        return {"auth_url": url}
    except FileNotFoundError:
        raise DriveCredentialsNotFoundException()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/oauth2callback")
@limiter.limit(RateLimits.AUTH)
async def oauth2callback(request: Request, code: str):
    """OAuth callback - exchange code for tokens"""
    try:
        return exchange_auth_code(code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/videos")
@limiter.limit(RateLimits.LIST_VIDEOS)
async def list_videos(request: Request, page: int = 1, limit: int = 24):
    """List videos in Google Drive with pagination"""
    try:
        _require_auth()

        if page < 1 or limit < 1:
            raise InvalidRequestException("page and limit must be positive integers")

        return list_videos_paginated(page, limit)
    except (DriveNotAuthenticatedException, InvalidRequestException):
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/{video_path:path}")
@limiter.limit(RateLimits.UPLOAD)
async def upload_to_drive(request: Request, video_path: str, base_dir: str = "./downloads"):
    """
    Inicia upload assíncrono de um vídeo local para o Google Drive.

    Retorna job_id imediatamente. O upload acontece em background.
    Use GET /api/jobs/{job_id} para acompanhar o progresso.
    """
    try:
        _require_auth()
        job_id = await upload_single_video(video_path, base_dir)
        return {
            "status": "success",
            "job_id": job_id,
            "message": "Upload iniciado em background"
        }
    except DriveNotAuthenticatedException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync-status")
@limiter.limit(RateLimits.GET_STATUS)
async def sync_status(request: Request, base_dir: str = "./downloads"):
    """Get sync status between local and Drive"""
    try:
        _require_auth()
        return get_sync_status(base_dir)
    except DriveNotAuthenticatedException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-all")
@limiter.limit(RateLimits.DOWNLOAD_BATCH)
async def sync_all(request: Request, base_dir: str = "./downloads"):
    """
    Inicia sincronização assíncrona de vídeos locais para o Drive.

    Retorna job_id imediatamente. O upload acontece em background
    com até 3 uploads simultâneos. Use GET /api/jobs/{job_id} para
    acompanhar o progresso.
    """
    try:
        _require_auth()
        job_id = await sync_all_videos(base_dir)
        return {
            "status": "success",
            "job_id": job_id,
            "message": "Sincronização iniciada em background"
        }
    except DriveNotAuthenticatedException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/videos/{file_id}")
@limiter.limit(RateLimits.DELETE)
async def delete_drive_video(request: Request, file_id: str):
    """Remove a video from Google Drive"""
    try:
        _require_auth()
        return delete_video(file_id)
    except DriveNotAuthenticatedException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/videos/delete-batch")
@limiter.limit(RateLimits.DELETE)
async def delete_drive_videos_batch(request: Request, file_ids: List[str]):
    """
    Delete multiple videos from Google Drive.

    Args:
        file_ids: List of file IDs to delete

    Returns:
        Results with deleted count and any failures
    """
    try:
        _require_auth()

        if not file_ids:
            raise InvalidRequestException("file_ids list cannot be empty")

        if len(file_ids) > 100:
            raise InvalidRequestException("Cannot delete more than 100 files at once")

        return delete_videos_batch(file_ids)
    except (DriveNotAuthenticatedException, InvalidRequestException):
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stream/{file_id}")
@limiter.limit(RateLimits.STREAM_VIDEO)
async def stream_drive_video(request: Request, file_id: str):
    """
    Stream video from Google Drive with Range Request support.
    Allows direct playback in browser with seek/skip.
    """
    try:
        _require_auth()

        range_header = request.headers.get('range')
        generator, headers, status_code = stream_video(file_id, range_header)

        if generator is None:
            # Range not satisfiable
            return Response(
                status_code=status_code,
                headers=headers
            )

        return StreamingResponse(
            generator,
            status_code=status_code,
            headers=headers,
            media_type=headers.get("Content-Type", "video/mp4")
        )
    except DriveNotAuthenticatedException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/thumbnail/{file_id}")
@limiter.limit(RateLimits.DEFAULT)
async def get_drive_thumbnail(request: Request, file_id: str):
    """Get thumbnail for a Drive video"""
    try:
        _require_auth()

        thumbnail_bytes = get_thumbnail(file_id)

        if not thumbnail_bytes:
            raise ThumbnailNotFoundException()

        return Response(
            content=thumbnail_bytes,
            media_type="image/jpeg",
            headers={
                "Cache-Control": "public, max-age=86400"  # Cache for 1 day
            }
        )
    except (DriveNotAuthenticatedException, ThumbnailNotFoundException):
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/custom-thumbnail/{file_id}")
@limiter.limit(RateLimits.DEFAULT)
async def get_drive_custom_thumbnail(request: Request, file_id: str):
    """
    Get custom thumbnail image file directly from Drive.
    Used for serving uploaded thumbnail files (e.g., .webp, .jpg) that
    are stored alongside videos.
    """
    try:
        _require_auth()

        result = get_custom_thumbnail(file_id)

        if not result:
            raise ThumbnailNotFoundException()

        thumbnail_bytes, mime_type = result

        return Response(
            content=thumbnail_bytes,
            media_type=mime_type,
            headers={
                "Cache-Control": "public, max-age=86400"  # Cache for 1 day
            }
        )
    except (DriveNotAuthenticatedException, ThumbnailNotFoundException):
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-external")
@limiter.limit(RateLimits.UPLOAD)
async def upload_external_to_drive(
    request: Request,
    folder_name: str = Form(...),
    video: UploadFile = File(...),
    extra_files: List[UploadFile] = File(default=[]),
):
    """
    Upload de arquivos externos para o Google Drive.

    Permite fazer upload de qualquer vídeo do PC para o Drive,
    com possibilidade de adicionar arquivos extras (thumbnail, legendas, etc.).
    A pasta é criada automaticamente se não existir.

    Retorna job_id para tracking de progresso via GET /api/jobs/{job_id}.
    """
    try:
        _require_auth()

        # Criar diretório temporário único
        temp_dir = Path(f"/tmp/yt-archiver-upload/{uuid.uuid4()}")
        temp_dir.mkdir(parents=True, exist_ok=True)

        temp_files = []

        try:
            # Salvar vídeo principal
            video_path = temp_dir / video.filename
            with open(video_path, "wb") as f:
                shutil.copyfileobj(video.file, f)
            temp_files.append(str(video_path))

            # Salvar arquivos extras
            for extra in extra_files:
                if extra.filename:  # Ignorar arquivos vazios
                    extra_path = temp_dir / extra.filename
                    with open(extra_path, "wb") as f:
                        shutil.copyfileobj(extra.file, f)
                    temp_files.append(str(extra_path))

            # Iniciar upload em background
            job_id = await upload_external_files(folder_name, temp_files)

            return {
                "status": "success",
                "job_id": job_id,
                "message": "Upload iniciado em background",
                "folder_name": folder_name,
                "files_count": len(temp_files)
            }

        except Exception as e:
            # Limpar arquivos temporários em caso de erro
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise

    except DriveNotAuthenticatedException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/download")
@limiter.limit(RateLimits.DOWNLOAD_BATCH)
async def download_from_drive(
    request: Request,
    path: str,
    base_dir: str = "./downloads"
):
    """
    Download assíncrono de um vídeo do Drive para o armazenamento local.

    Retorna job_id imediatamente. O download acontece em background.
    Use GET /api/jobs/{job_id} para acompanhar o progresso.

    Args:
        path: Caminho relativo do arquivo no Drive (e.g., "Channel/video.mp4")
        base_dir: Diretório base local para downloads
    """
    try:
        _require_auth()

        # Buscar file_id pelo path
        video = drive_manager.get_video_by_path(path)
        if not video:
            raise HTTPException(status_code=404, detail=f"Vídeo não encontrado no Drive: {path}")

        file_id = video['id']
        job_id = await download_single_from_drive(file_id, path, base_dir)
        return {
            "status": "success",
            "job_id": job_id,
            "message": "Download iniciado em background"
        }
    except DriveNotAuthenticatedException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/download-all")
@limiter.limit(RateLimits.DOWNLOAD_BATCH)
async def download_all_from_drive_endpoint(
    request: Request,
    base_dir: str = "./downloads"
):
    """
    Download assíncrono de todos os vídeos que estão apenas no Drive.

    Retorna job_id imediatamente. O download acontece em background
    com até 3 downloads simultâneos. Use GET /api/jobs/{job_id} para
    acompanhar o progresso.

    Args:
        base_dir: Diretório base local para downloads
    """
    try:
        _require_auth()
        job_id = await download_all_from_drive(base_dir)
        return {
            "status": "success",
            "job_id": job_id,
            "message": "Download de todos os vídeos iniciado em background"
        }
    except DriveNotAuthenticatedException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
