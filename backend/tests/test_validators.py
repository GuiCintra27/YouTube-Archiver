"""
Tests for input validators.
"""
import pytest

from app.core.validators import (
    validate_url,
    validate_path_safe,
    sanitize_filename,
    URLValidationError,
)


class TestValidateURL:
    """Tests for URL validation."""

    def test_valid_youtube_video_url(self):
        """Test valid YouTube video URL."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        result = validate_url(url)
        assert result == url

    def test_valid_youtube_short_url(self):
        """Test valid YouTube short URL."""
        url = "https://youtu.be/dQw4w9WgXcQ"
        result = validate_url(url)
        assert result == url

    def test_valid_youtube_playlist_url(self):
        """Test valid YouTube playlist URL."""
        url = "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
        result = validate_url(url)
        assert result == url

    def test_invalid_empty_url(self):
        """Test that empty URL raises error."""
        with pytest.raises(URLValidationError):
            validate_url("")

    def test_other_supported_urls(self):
        """Test that other video sites are accepted (yt-dlp supports 1000+ sites)."""
        # yt-dlp supports many sites, so non-YouTube URLs are valid
        url = "https://www.vimeo.com/123456"
        result = validate_url(url)
        assert result == url

    def test_invalid_malformed_url(self):
        """Test that malformed URL raises error."""
        with pytest.raises(URLValidationError):
            validate_url("not-a-url")


class TestValidatePathSafe:
    """Tests for path safety validation."""

    def test_valid_simple_path(self):
        """Test valid simple path."""
        path = "channel/video.mp4"
        result = validate_path_safe(path)
        assert result == path

    def test_path_traversal_double_dot(self):
        """Test path traversal with .. is rejected."""
        with pytest.raises(ValueError):
            validate_path_safe("../../../etc/passwd")

    def test_path_traversal_absolute(self):
        """Test absolute path starting with / is rejected."""
        with pytest.raises(ValueError):
            validate_path_safe("/etc/passwd")

    def test_path_with_backslash(self):
        """Test path with backslash is rejected."""
        with pytest.raises(ValueError):
            validate_path_safe("..\\..\\windows\\system32")


class TestSanitizeFilename:
    """Tests for filename sanitization."""

    def test_valid_filename(self):
        """Test valid filename passes through."""
        filename = "video_title.mp4"
        result = sanitize_filename(filename)
        assert result == filename

    def test_removes_special_characters(self):
        """Test special characters are removed."""
        filename = 'video<title>:test|"name?.mp4'
        result = sanitize_filename(filename)
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert "|" not in result
        assert '"' not in result
        assert "?" not in result

    def test_removes_path_traversal(self):
        """Test path traversal chars are removed."""
        filename = "../../../video.mp4"
        result = sanitize_filename(filename)
        assert ".." not in result
        assert "/" not in result

    def test_preserves_unicode(self):
        """Test Unicode characters are preserved."""
        filename = "vídeo_título_测试.mp4"
        result = sanitize_filename(filename)
        assert "í" in result
        assert "测试" in result

    def test_trims_whitespace(self):
        """Test whitespace is trimmed."""
        filename = "  video title  .mp4  "
        result = sanitize_filename(filename)
        assert not result.startswith(" ")
        assert not result.endswith(" ")
