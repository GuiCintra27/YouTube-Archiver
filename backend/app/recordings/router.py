"""
Recordings router - API endpoints for screen recording uploads
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request

from app.core.logging import get_module_logger
from app.core.rate_limit import limiter, RateLimits
from app.core.blocking import run_blocking, get_fs_semaphore
from .service import save_recording
from .schemas import RecordingUploadResponse

logger = get_module_logger("recordings")

router = APIRouter(prefix="/api/recordings", tags=["recordings"])


@router.post("/upload", response_model=RecordingUploadResponse)
@limiter.limit(RateLimits.UPLOAD)
async def upload_recording(
    request: Request,
    file: UploadFile = File(...),
    target_path: str = Form(default=""),
    base_dir: str = "./downloads",
):
    """
    Recebe uma gravação enviada pelo frontend e salva na pasta de downloads.
    """
    try:
        result = await run_blocking(
            save_recording,
            file=file.file,
            filename=file.filename,
            target_path=target_path,
            base_dir=base_dir,
            semaphore=get_fs_semaphore(),
            label="recordings.save",
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload recording: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
