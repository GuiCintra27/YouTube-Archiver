"""
Catalog identity helpers (stable IDs stored alongside media files).
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Optional

from app.core.logging import get_module_logger

logger = get_module_logger("catalog.identity")

CATALOG_ID_SUFFIX = ".ytarchiver.json"
CATALOG_ID_KEY = "catalog_id"


def sidecar_path_for(video_path: Path) -> Path:
    base_name = video_path.stem
    return video_path.with_name(f"{base_name}{CATALOG_ID_SUFFIX}")


def read_catalog_id_from_sidecar(sidecar_path: Path) -> Optional[str]:
    if not sidecar_path.exists():
        return None
    try:
        payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.debug(f"Failed to read catalog sidecar {sidecar_path}: {exc}")
        return None
    catalog_id = payload.get(CATALOG_ID_KEY)
    return str(catalog_id) if catalog_id else None


def read_catalog_id_for_video(video_path: Path) -> Optional[str]:
    return read_catalog_id_from_sidecar(sidecar_path_for(video_path))


def ensure_catalog_id_for_video(video_path: Path) -> str:
    sidecar_path = sidecar_path_for(video_path)
    catalog_id = read_catalog_id_from_sidecar(sidecar_path)
    if catalog_id:
        return catalog_id

    catalog_id = str(uuid.uuid4())
    try:
        sidecar_path.write_text(
            json.dumps({CATALOG_ID_KEY: catalog_id}, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.warning(f"Failed to write catalog sidecar {sidecar_path}: {exc}")
    return catalog_id
