"""
Downloads router - API endpoints for video downloads
"""
from fastapi import APIRouter, HTTPException

from .schemas import VideoInfoRequest, DownloadRequest
from .service import get_video_info, create_download_settings
from app.jobs.service import create_and_start_job

router = APIRouter(prefix="/api", tags=["downloads"])


@router.post("/video-info")
async def video_info(request: VideoInfoRequest):
    """Obtém informações sobre um vídeo sem baixar"""
    try:
        info = await get_video_info(request.url)
        return info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/download")
async def start_download(request: DownloadRequest):
    """Inicia um download em background"""
    try:
        job_id = await create_and_start_job(request)
        return {
            "status": "success",
            "job_id": job_id,
            "message": "Download iniciado",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
