"""
Drive catalog snapshot format (V1).

The snapshot is stored as a gzipped JSON file in Google Drive and imported into
the local SQLite catalog. This eliminates Drive list/search calls for the UI.
"""

from __future__ import annotations

import gzip
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


SCHEMA_VERSION = 1


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def encode_drive_snapshot(payload: Dict[str, Any]) -> bytes:
    """Encode a snapshot dict into gzipped JSON bytes."""
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return gzip.compress(raw)


def decode_drive_snapshot(data: bytes) -> Dict[str, Any]:
    """Decode gzipped JSON bytes into a snapshot dict."""
    try:
        raw = gzip.decompress(data)
    except Exception:
        # Accept plain JSON for debugging/manual tooling
        raw = data

    payload = json.loads(raw.decode("utf-8"))
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"Unsupported schema_version: {payload.get('schema_version')}")
    if "videos" not in payload or not isinstance(payload["videos"], list):
        raise ValueError("Invalid snapshot: missing videos[]")
    return payload


def build_drive_snapshot(
    *,
    videos: List[Dict[str, Any]],
    library_id: Optional[str] = None,
    generated_at: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a normalized snapshot payload (dict).

    Expected `videos` item format (minimum):
    - video_uid: str
    - title: str (optional)
    - channel: str (optional)
    - duration_seconds: int (optional)
    - modified_at: str (optional)
    - assets: list[{kind, drive_file_id, mime_type, size_bytes}] (optional)
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at or _utc_now_iso(),
        "library_id": library_id,
        "videos": videos,
    }

