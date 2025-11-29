"""
Recordings service - business logic for screen recording uploads
"""
import shutil
from pathlib import Path
from typing import BinaryIO

from app.core.security import get_safe_relative_path, validate_path_within_base


def save_recording(
    file: BinaryIO,
    filename: str,
    target_path: str = "",
    base_dir: str = "./downloads"
) -> dict:
    """
    Save a recording file to the downloads directory.

    Args:
        file: File-like object with the recording data
        filename: Original filename
        target_path: Optional relative path within base_dir
        base_dir: Base directory for saving

    Returns:
        Dict with status and file paths
    """
    base_path = Path(base_dir).resolve()
    relative_target = get_safe_relative_path(target_path)

    target_dir = (base_path / relative_target).resolve()

    # Validate target is within base
    validate_path_within_base(target_dir, base_path)

    # Create directory if needed
    target_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize filename
    safe_name = Path(filename or "gravacao.webm").name
    final_path = target_dir / safe_name

    # Avoid overwriting existing files
    counter = 1
    while final_path.exists():
        stem = final_path.stem
        suffix = final_path.suffix
        final_path = target_dir / f"{stem}-{counter}{suffix}"
        counter += 1

    # Save file
    with open(final_path, "wb") as buffer:
        shutil.copyfileobj(file, buffer)

    return {
        "status": "success",
        "path": str(final_path.relative_to(base_path)),
        "full_path": str(final_path),
        "message": "Gravação salva com sucesso",
    }
