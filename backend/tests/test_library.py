"""
Tests for library (local videos) endpoints.
"""
import pytest
import httpx
from pathlib import Path


class TestListVideos:
    """Tests for GET /api/videos endpoint."""

    async def test_list_videos_empty_directory(self, client: httpx.AsyncClient, downloads_dir: Path):
        """Test listing videos in empty directory."""
        response = await client.get("/api/videos", params={"base_dir": str(downloads_dir)})

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["videos"] == []

    async def test_list_videos_with_videos(
        self, client: httpx.AsyncClient, downloads_dir: Path, sample_video_file: Path
    ):
        """Test listing videos when videos exist."""
        response = await client.get("/api/videos", params={"base_dir": str(downloads_dir)})

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["videos"]) == 1

        video = data["videos"][0]
        assert video["title"] == "test_video"
        assert video["channel"] == "TestChannel"

    async def test_list_videos_with_pagination(
        self, client: httpx.AsyncClient, downloads_dir: Path, sample_video_file: Path
    ):
        """Test listing videos with pagination."""
        response = await client.get(
            "/api/videos",
            params={"base_dir": str(downloads_dir), "page": 1, "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["limit"] == 10

    async def test_list_videos_invalid_page(self, client: httpx.AsyncClient, downloads_dir: Path):
        """Test listing videos with invalid page number."""
        response = await client.get(
            "/api/videos",
            params={"base_dir": str(downloads_dir), "page": 0}
        )

        assert response.status_code == 400

    async def test_list_videos_invalid_limit(self, client: httpx.AsyncClient, downloads_dir: Path):
        """Test listing videos with invalid limit."""
        response = await client.get(
            "/api/videos",
            params={"base_dir": str(downloads_dir), "limit": 0}
        )

        assert response.status_code == 400


class TestStreamVideo:
    """Tests for GET /api/videos/stream/{path} endpoint."""

    async def test_stream_video_exists(
        self, client: httpx.AsyncClient, downloads_dir: Path, sample_video_file: Path
    ):
        """Test streaming an existing video."""
        rel_path = sample_video_file.relative_to(downloads_dir)
        async with client.stream(
            "GET",
            f"/api/videos/stream/{rel_path}",
            params={"base_dir": str(downloads_dir)},
        ) as response:
            assert response.status_code == 200
            assert "Accept-Ranges" in response.headers

    async def test_stream_video_not_found(self, client: httpx.AsyncClient, downloads_dir: Path):
        """Test streaming a non-existent video."""
        async with client.stream(
            "GET",
            "/api/videos/stream/nonexistent/video.mp4",
            params={"base_dir": str(downloads_dir)},
        ) as response:
            assert response.status_code == 404

    async def test_stream_video_range_request(
        self, client: httpx.AsyncClient, downloads_dir: Path, sample_video_file: Path
    ):
        """Test streaming with range request header."""
        rel_path = sample_video_file.relative_to(downloads_dir)
        async with client.stream(
            "GET",
            f"/api/videos/stream/{rel_path}",
            params={"base_dir": str(downloads_dir)},
            headers={"Range": "bytes=0-10"},
        ) as response:
            assert response.status_code == 206
            assert "Content-Range" in response.headers


class TestGetThumbnail:
    """Tests for GET /api/videos/thumbnail/{path} endpoint."""

    async def test_get_thumbnail_exists(
        self, client: httpx.AsyncClient, downloads_dir: Path, sample_video_with_thumbnail: dict
    ):
        """Test getting an existing thumbnail."""
        thumbnail_path = sample_video_with_thumbnail["thumbnail"]
        rel_path = thumbnail_path.relative_to(downloads_dir)

        response = await client.get(
            f"/api/videos/thumbnail/{rel_path}",
            params={"base_dir": str(downloads_dir)}
        )

        assert response.status_code == 200

    async def test_get_thumbnail_not_found(self, client: httpx.AsyncClient, downloads_dir: Path):
        """Test getting a non-existent thumbnail."""
        response = await client.get(
            "/api/videos/thumbnail/nonexistent/thumb.jpg",
            params={"base_dir": str(downloads_dir)}
        )

        assert response.status_code == 404


class TestDeleteVideo:
    """Tests for DELETE /api/videos/{path} endpoint."""

    async def test_delete_video_exists(
        self, client: httpx.AsyncClient, downloads_dir: Path, sample_video_file: Path
    ):
        """Test deleting an existing video."""
        rel_path = sample_video_file.relative_to(downloads_dir)

        response = await client.delete(
            f"/api/videos/{rel_path}",
            params={"base_dir": str(downloads_dir)}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert not sample_video_file.exists()

    async def test_delete_video_with_related_files(
        self, client: httpx.AsyncClient, downloads_dir: Path, sample_video_with_thumbnail: dict
    ):
        """Test deleting a video also deletes related files."""
        video_path = sample_video_with_thumbnail["video"]
        thumbnail_path = sample_video_with_thumbnail["thumbnail"]
        rel_path = video_path.relative_to(downloads_dir)

        response = await client.delete(
            f"/api/videos/{rel_path}",
            params={"base_dir": str(downloads_dir)}
        )

        assert response.status_code == 200
        assert not video_path.exists()
        assert not thumbnail_path.exists()

    async def test_delete_video_not_found(self, client: httpx.AsyncClient, downloads_dir: Path):
        """Test deleting a non-existent video."""
        response = await client.delete(
            "/api/videos/nonexistent/video.mp4",
            params={"base_dir": str(downloads_dir)}
        )

        assert response.status_code == 404
