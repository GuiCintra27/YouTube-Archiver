"""
Pytest configuration and shared fixtures for YT-Archiver tests.
"""
import os
import pytest
import pytest_asyncio
from pathlib import Path
from typing import Generator
import httpx

# The Drive cache uses `aiosqlite`, which may hang in some environments.
# For unit tests that don't explicitly target the Drive cache subsystem,
# disable it to keep the FastAPI app startup deterministic.
os.environ.setdefault("DRIVE_CACHE_ENABLED", "false")
os.environ.setdefault("DRIVE_CACHE_FALLBACK_TO_API", "false")
os.environ.setdefault("CATALOG_DB_PATH", ":memory:")

from app.main import app
from app.jobs import store as jobs_store
from app.library.cache import video_cache
from app.catalog.repository import CatalogRepository
from app.config import settings


@pytest_asyncio.fixture
async def client() -> Generator[httpx.AsyncClient, None, None]:
    """
    Create an async test client for the FastAPI application.

    Yields:
        httpx.AsyncClient instance for making HTTP requests
    """
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as test_client:
            yield test_client


@pytest.fixture
def downloads_dir(tmp_path: Path) -> Path:
    """
    Create a temporary downloads directory for testing.

    Args:
        tmp_path: pytest's built-in temporary path fixture

    Returns:
        Path to the temporary downloads directory
    """
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    return downloads


@pytest.fixture
def sample_video_file(downloads_dir: Path) -> Path:
    """
    Create a sample video file for testing.

    Args:
        downloads_dir: Temporary downloads directory

    Returns:
        Path to the sample video file
    """
    channel_dir = downloads_dir / "TestChannel"
    channel_dir.mkdir()

    video_file = channel_dir / "test_video.mp4"
    video_file.write_bytes(b"fake video content for testing")

    return video_file


@pytest.fixture
def sample_video_with_thumbnail(sample_video_file: Path) -> dict:
    """
    Create a sample video file with associated thumbnail.

    Args:
        sample_video_file: Path to the sample video

    Returns:
        Dict with video and thumbnail paths
    """
    thumbnail = sample_video_file.with_suffix(".jpg")
    thumbnail.write_bytes(b"fake thumbnail content")

    return {
        "video": sample_video_file,
        "thumbnail": thumbnail,
    }


@pytest.fixture(autouse=True)
def clear_jobs():
    """
    Clear all jobs before and after each test.

    This ensures test isolation.
    """
    jobs_store.clear_all_jobs()
    yield
    jobs_store.clear_all_jobs()


@pytest.fixture(autouse=True)
def clear_cache():
    """
    Clear video cache before and after each test.

    This ensures test isolation.
    """
    video_cache.invalidate()
    yield
    video_cache.invalidate()


@pytest.fixture(autouse=True)
def clear_catalog_and_reset_flags():
    """
    Clear the in-memory catalog DB and reset settings flags mutated by tests.

    Some tests monkeypatch `settings.CATALOG_ENABLED` at runtime; since `settings`
    is a singleton, we must restore defaults to avoid cross-test leakage.
    """
    original_catalog_enabled = settings.CATALOG_ENABLED
    try:
        repo = CatalogRepository()
        repo.clear_location("local")
        repo.clear_location("drive")
    except Exception:
        pass

    settings.CATALOG_ENABLED = False
    yield

    settings.CATALOG_ENABLED = original_catalog_enabled


@pytest.fixture
def mock_job() -> dict:
    """
    Create a mock job for testing.

    Returns:
        Dict with job data
    """
    job_id = "test-job-123"
    job_data = {
        "id": job_id,
        "status": "pending",
        "url": "https://www.youtube.com/watch?v=test123",
        "progress": {},
        "created_at": "2024-01-01T00:00:00",
    }
    jobs_store.create_job(job_id, job_data)
    return job_data
