"""
Recordings router - API endpoints for screen recording uploads
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from .service import save_recording

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
        import traceback
        print(f"[ERROR] {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
