"""
Tests for the catalog module endpoints.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from app.config import settings


@pytest.mark.asyncio
async def test_catalog_status_ok(client: httpx.AsyncClient):
    response = await client.get("/api/catalog/status")
    assert response.status_code == 200
    data = response.json()
    assert data["db_path"]
    assert "counts" in data
    assert "local" in data["counts"]
    assert "drive" in data["counts"]


@pytest.mark.asyncio
async def test_bootstrap_local_and_list_videos_via_catalog(
    client: httpx.AsyncClient, downloads_dir: Path, sample_video_with_thumbnail: dict, monkeypatch
):
    # Bootstrap catalog from a temp downloads dir
    response = await client.post(
        "/api/catalog/bootstrap-local",
        params={"base_dir": str(downloads_dir)},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["inserted"] == 1

    # Enable catalog-backed listing
    monkeypatch.setattr(settings, "CATALOG_ENABLED", True)

    response2 = await client.get(
        "/api/videos",
        params={"base_dir": str(downloads_dir), "page": 1, "limit": 10},
    )
    assert response2.status_code == 200
    payload = response2.json()
    assert payload["total"] == 1
    assert len(payload["videos"]) == 1
    assert payload["videos"][0]["title"] == "test_video"

    # Delete and ensure it's removed from catalog-backed listing
    rel_path = sample_video_with_thumbnail["video"].relative_to(downloads_dir)
    response3 = await client.delete(
        f"/api/videos/{rel_path}",
        params={"base_dir": str(downloads_dir)},
    )
    assert response3.status_code == 200

    response4 = await client.get(
        "/api/videos",
        params={"base_dir": str(downloads_dir), "page": 1, "limit": 10},
    )
    assert response4.status_code == 200
    payload2 = response4.json()
    assert payload2["total"] == 0
