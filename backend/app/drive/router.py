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
    get_sync_items_from_catalog,
    sync_all_videos,
    delete_video,
    delete_videos_batch,
    get_drive_share_status,
    rename_drive_video as rename_drive_video_service,
    share_drive_video,
    unshare_drive_video,
    update_drive_thumbnail as update_drive_thumbnail_service,
    stream_video,
    get_thumbnail,
    get_custom_thumbnail,
    download_single_from_drive,
    download_all_from_drive,
    resolve_drive_file_id_by_path,
)
from .manager import drive_manager
from .schemas import (
    DriveAuthStatus,
    DriveAuthUrl,
    DriveAuthResult,
    DriveVideoListResponse,
    DriveSyncStatus,
    DriveSyncItemsResponse,
    DriveJobResponse,
    DriveDeleteResult,
    DriveShareStatusResponse,
    DriveRenameResponse,
    DriveThumbnailUpdateResponse,
    DriveExternalUploadResponse,
)
from app.core.exceptions import (
    DriveNotAuthenticatedException,
    DriveCredentialsNotFoundException,
    InvalidRequestException,
    ThumbnailNotFoundException,
)
from app.core.errors import AppException
from app.core.rate_limit import limiter, RateLimits
from app.core.blocking import run_blocking, get_drive_semaphore
from app.config import settings
from pydantic import BaseModel


class RenameRequest(BaseModel):
    new_name: str


router = APIRouter(prefix="/api/drive", tags=["drive"])


def _require_auth():
    """Helper to check Drive authentication"""
    if not drive_manager.is_authenticated():
        raise DriveNotAuthenticatedException()


@router.get("/auth-status", response_model=DriveAuthStatus)
@limiter.limit(RateLimits.GET_STATUS)
async def auth_status(request: Request):
    """Check if user is authenticated with Google Drive"""
    return get_auth_status()


@router.get("/auth-url", response_model=DriveAuthUrl)
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


@router.get("/oauth2callback", response_model=DriveAuthResult)
@limiter.limit(RateLimits.AUTH)
async def oauth2callback(request: Request, code: str):
    """OAuth callback - exchange code for tokens"""
    try:
        result = await run_blocking(
            exchange_auth_code,
            code,
            semaphore=get_drive_semaphore(),
            label="drive.oauth",
        )

        # Trigger initial cache sync after successful authentication
        if settings.DRIVE_CACHE_ENABLED:
            try:
                from .cache import trigger_initial_sync_if_authenticated
                # Run in background to not block the callback response
                import asyncio
                asyncio.create_task(trigger_initial_sync_if_authenticated())
            except Exception as e:
                # Log but don't fail the auth callback
                import logging
                logging.warning(f"Failed to trigger initial cache sync: {e}")

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/videos", response_model=DriveVideoListResponse)
@limiter.limit(RateLimits.LIST_VIDEOS)
async def list_videos(request: Request, page: int = 1, limit: int = 24):
    """List videos in Google Drive with pagination"""
    try:
        _require_auth()

        if page < 1 or limit < 1:
            raise InvalidRequestException("page and limit must be positive integers")

        return await list_videos_paginated(page, limit)
    except (DriveNotAuthenticatedException, InvalidRequestException):
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/{video_path:path}", response_model=DriveJobResponse)
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
    except AppException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync-status", response_model=DriveSyncStatus)
@limiter.limit(RateLimits.GET_STATUS)
async def sync_status(request: Request, base_dir: str = "./downloads"):
    """Get sync status between local and Drive"""
    try:
        _require_auth()
        return await get_sync_status(base_dir)
    except DriveNotAuthenticatedException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sync-items", response_model=DriveSyncItemsResponse)
@limiter.limit(RateLimits.GET_STATUS)
async def sync_items(request: Request, kind: str, page: int = 1, limit: int = 50):
    """
    Paginated sync items between local and Drive catalogs.

    kind: local_only | drive_only | synced
    """
    try:
        _require_auth()
        if page < 1 or limit < 1:
            raise InvalidRequestException("page and limit must be positive integers")
        return await get_sync_items_from_catalog(kind=kind, page=page, limit=limit)
    except (DriveNotAuthenticatedException, InvalidRequestException):
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-all", response_model=DriveJobResponse)
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


@router.delete("/videos/{file_id}", response_model=DriveDeleteResult)
@limiter.limit(RateLimits.DELETE)
async def delete_drive_video(request: Request, file_id: str):
    """Remove a video from Google Drive"""
    try:
        _require_auth()
        return await delete_video(file_id)
    except DriveNotAuthenticatedException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/videos/delete-batch", response_model=DriveDeleteResult)
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

        return await delete_videos_batch(file_ids)
    except (DriveNotAuthenticatedException, InvalidRequestException):
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/videos/{file_id}/share", response_model=DriveShareStatusResponse)
@limiter.limit(RateLimits.DEFAULT)
async def get_drive_share(request: Request, file_id: str):
    """Get public sharing status for a Drive video"""
    try:
        _require_auth()
        return await get_drive_share_status(file_id)
    except DriveNotAuthenticatedException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/videos/{file_id}/share", response_model=DriveShareStatusResponse)
@limiter.limit(RateLimits.DEFAULT)
async def share_drive(request: Request, file_id: str):
    """Enable public sharing for a Drive video"""
    try:
        _require_auth()
        return await share_drive_video(file_id)
    except DriveNotAuthenticatedException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/videos/{file_id}/share", response_model=DriveShareStatusResponse)
@limiter.limit(RateLimits.DEFAULT)
async def unshare_drive(request: Request, file_id: str):
    """Disable public sharing for a Drive video"""
    try:
        _require_auth()
        return await unshare_drive_video(file_id)
    except DriveNotAuthenticatedException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/videos/{file_id}/rename", response_model=DriveRenameResponse)
@limiter.limit(RateLimits.DEFAULT)
async def rename_drive_video(request: Request, file_id: str, body: RenameRequest):
    """
    Rename a video in Google Drive.
    Also renames related files (thumbnails, metadata, subtitles).
    """
    try:
        _require_auth()

        if not body.new_name or not body.new_name.strip():
            raise InvalidRequestException("New name cannot be empty")

        return await rename_drive_video_service(file_id, body.new_name.strip())
    except (DriveNotAuthenticatedException, InvalidRequestException):
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/videos/{file_id}/thumbnail", response_model=DriveThumbnailUpdateResponse)
@limiter.limit(RateLimits.DEFAULT)
async def update_drive_thumbnail(
    request: Request,
    file_id: str,
    thumbnail: UploadFile = File(...)
):
    """
    Update/upload a new thumbnail for a video in Google Drive.
    Replaces any existing thumbnail.
    """
    try:
        _require_auth()

        if not thumbnail.filename:
            raise InvalidRequestException("Thumbnail filename is required")

        file_ext = Path(thumbnail.filename).suffix.lower()
        if file_ext not in settings.THUMBNAIL_EXTENSIONS:
            raise InvalidRequestException(
                f"Invalid image format: {file_ext}. Supported: {', '.join(settings.THUMBNAIL_EXTENSIONS)}"
            )

        thumbnail_data = await thumbnail.read()

        return await update_drive_thumbnail_service(file_id, thumbnail_data, file_ext)
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
        file_metadata = await run_blocking(
            drive_manager.get_file_metadata,
            file_id,
            semaphore=get_drive_semaphore(),
            label="drive.stream.metadata",
        )
        access_token = await run_blocking(
            drive_manager._get_access_token,
            semaphore=get_drive_semaphore(),
            label="drive.stream.token",
        )
        generator, headers, status_code = stream_video(
            file_id,
            range_header,
            file_metadata=file_metadata,
            access_token=access_token,
        )

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

        thumbnail_bytes = await run_blocking(
            get_thumbnail,
            file_id,
            semaphore=get_drive_semaphore(),
            label="drive.thumbnail",
        )

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

        result = await run_blocking(
            get_custom_thumbnail,
            file_id,
            semaphore=get_drive_semaphore(),
            label="drive.custom_thumbnail",
        )

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


@router.post("/upload-external", response_model=DriveExternalUploadResponse)
@limiter.limit(RateLimits.UPLOAD)
async def upload_external_to_drive(
    request: Request,
    folder_name: str = Form(...),
    video: UploadFile = File(...),
    thumbnail: UploadFile = File(default=None),
    subtitles: List[UploadFile] = File(default=[]),
    transcription: UploadFile = File(default=None),
):
    """
    Upload de arquivos externos para o Google Drive.

    Permite fazer upload de qualquer vídeo do PC para o Drive,
    com possibilidade de adicionar:
    - thumbnail: imagem de capa (jpg, png, webp)
    - subtitles: arquivos de legenda (.srt, .vtt) - múltiplos permitidos
    - transcription: arquivo de transcrição (.txt)

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

            # Salvar thumbnail (se fornecida)
            if thumbnail and thumbnail.filename:
                thumb_path = temp_dir / thumbnail.filename
                with open(thumb_path, "wb") as f:
                    shutil.copyfileobj(thumbnail.file, f)
                temp_files.append(str(thumb_path))

            # Salvar legendas (múltiplas)
            for subtitle in subtitles:
                if subtitle.filename:
                    sub_path = temp_dir / subtitle.filename
                    with open(sub_path, "wb") as f:
                        shutil.copyfileobj(subtitle.file, f)
                    temp_files.append(str(sub_path))

            # Salvar transcrição (se fornecida)
            if transcription and transcription.filename:
                trans_path = temp_dir / transcription.filename
                with open(trans_path, "wb") as f:
                    shutil.copyfileobj(transcription.file, f)
                temp_files.append(str(trans_path))

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


@router.post("/download", response_model=DriveJobResponse)
@limiter.limit(RateLimits.DOWNLOAD_BATCH)
async def download_from_drive(
    request: Request,
    path: str,
    file_id: str | None = None,
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

        resolved_file_id = file_id
        if not resolved_file_id:
            if settings.CATALOG_ENABLED:
                resolved_file_id = await resolve_drive_file_id_by_path(drive_path=path)
            else:
                video = await run_blocking(
                    drive_manager.get_video_by_path,
                    path,
                    semaphore=get_drive_semaphore(),
                    label="drive.get_video_by_path",
                )
                if not video:
                    raise HTTPException(status_code=404, detail=f"Vídeo não encontrado no Drive: {path}")
                resolved_file_id = video["id"]

        job_id = await download_single_from_drive(resolved_file_id, path, base_dir)
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


@router.post("/download-all", response_model=DriveJobResponse)
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


# ============================================================================
# Cache Management Endpoints
# ============================================================================

@router.post("/cache/sync")
@limiter.limit(RateLimits.DEFAULT)
async def sync_cache(request: Request, full: bool = False):
    """
    Trigger manual cache synchronization.

    Args:
        full: If True, performs a complete rebuild. Otherwise, incremental sync.

    Returns:
        Sync result with statistics
    """
    try:
        _require_auth()

        if not settings.DRIVE_CACHE_ENABLED:
            raise InvalidRequestException("Drive cache is disabled")

        from .cache import full_sync, incremental_sync

        if full:
            result = await full_sync()
        else:
            result = await incremental_sync()

        return {
            "success": result.success,
            "sync_type": "full" if full else "incremental",
            "message": result.message,
            "added": result.added,
            "updated": result.updated,
            "deleted": result.deleted,
            "changes_detected": result.changes_detected,
        }
    except (DriveNotAuthenticatedException, InvalidRequestException):
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
@limiter.limit(RateLimits.GET_STATUS)
async def get_cache_stats(request: Request):
    """
    Get cache statistics and sync metadata.

    Returns:
        Cache stats including video count, last sync times, etc.
    """
    try:
        if not settings.DRIVE_CACHE_ENABLED:
            return {
                "enabled": False,
                "message": "Drive cache is disabled"
            }

        from .cache import get_repository

        repo = get_repository()
        stats = await repo.get_stats()

        return {
            "enabled": True,
            **stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/rebuild")
@limiter.limit(RateLimits.DEFAULT)
async def rebuild_cache(request: Request):
    """
    Force a complete cache rebuild.

    Clears all cached data and re-fetches everything from Google Drive.
    Use this when cache seems out of sync or corrupted.

    Returns:
        Rebuild result with statistics
    """
    try:
        _require_auth()

        if not settings.DRIVE_CACHE_ENABLED:
            raise InvalidRequestException("Drive cache is disabled")

        from .cache import full_sync

        result = await full_sync()

        return {
            "success": result.success,
            "message": result.message,
            "total_videos": result.added,
            "sync_duration": "completed"
        }
    except (DriveNotAuthenticatedException, InvalidRequestException):
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache")
@limiter.limit(RateLimits.DELETE)
async def clear_cache(request: Request):
    """
    Clear all cached data.

    Removes all videos and folders from cache. Next list operation
    will trigger a fresh sync from Google Drive.

    Returns:
        Confirmation of cache clear
    """
    try:
        if not settings.DRIVE_CACHE_ENABLED:
            raise InvalidRequestException("Drive cache is disabled")

        from .cache import get_repository

        repo = get_repository()
        await repo.clear_all()

        return {
            "success": True,
            "message": "Cache cleared successfully"
        }
    except InvalidRequestException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
