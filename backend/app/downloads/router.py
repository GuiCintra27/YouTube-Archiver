"""
Downloads router - API endpoints for video downloads
"""
from fastapi import APIRouter, HTTPException, Request

from .schemas import VideoInfoRequest, DownloadRequest
from .service import get_video_info, create_download_settings
from app.jobs.service import create_and_start_job
from app.core.rate_limit import limiter, RateLimits

router = APIRouter(prefix="/api", tags=["downloads"])


@router.post("/video-info")
@limiter.limit(RateLimits.LIST_VIDEOS)
async def video_info(request: Request, body: VideoInfoRequest):
    """Obtém informações sobre um vídeo sem baixar"""
    try:
        info = await get_video_info(body.url)
        return info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/download")
@limiter.limit(RateLimits.DOWNLOAD_START)
async def start_download(request: Request, body: DownloadRequest):
    """Inicia um download em background"""
    try:
        job_id = await create_and_start_job(body)
        return {
            "status": "success",
            "job_id": job_id,
            "message": "Download iniciado",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
