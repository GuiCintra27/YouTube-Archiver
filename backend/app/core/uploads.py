"""
Upload helpers for validating and reading incoming files.
"""
import shutil
from pathlib import Path
from typing import Sequence, Tuple

from fastapi import UploadFile

from app.core.exceptions import InvalidRequestException


async def read_thumbnail_upload(
    thumbnail: UploadFile,
    allowed_exts: Sequence[str],
) -> Tuple[bytes, str]:
    if not thumbnail.filename:
        raise InvalidRequestException("Thumbnail filename is required")

    file_ext = Path(thumbnail.filename).suffix.lower()
    if file_ext not in allowed_exts:
        raise InvalidRequestException(
            f"Invalid image format: {file_ext}. Supported: {', '.join(allowed_exts)}"
        )

    thumbnail_data = await thumbnail.read()
    return thumbnail_data, file_ext


def save_upload_file(upload: UploadFile, destination: Path) -> None:
    with open(destination, "wb") as handle:
        shutil.copyfileobj(upload.file, handle)
