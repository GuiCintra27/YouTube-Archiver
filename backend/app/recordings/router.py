"""
Recordings router - API endpoints for screen recording uploads
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from app.core.logging import get_module_logger
from .service import save_recording

logger = get_module_logger("recordings")

router = APIRouter(prefix="/api/recordings", tags=["recordings"])


@router.post("/upload")
async def upload_recording(
    file: UploadFile = File(...),
    target_path: str = Form(default=""),
    base_dir: str = "./downloads",
):
    """
    Recebe uma gravação enviada pelo frontend e salva na pasta de downloads.
    """
    try:
        result = save_recording(
            file=file.file,
            filename=file.filename,
            target_path=target_path,
            base_dir=base_dir,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload recording: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
