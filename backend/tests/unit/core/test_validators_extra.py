"""
Additional unit tests for validators.
"""
import pytest

from app.core.validators import (
    detect_url_type,
    validate_youtube_url,
    validate_resolution,
    validate_delay,
    validate_batch_size,
    URLValidationError,
)


def test_validate_youtube_url_accepts_youtube() -> None:
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert validate_youtube_url(url) == url


def test_validate_youtube_url_rejects_non_youtube() -> None:
    with pytest.raises(URLValidationError):
        validate_youtube_url("https://vimeo.com/12345")


def test_detect_url_type_playlist() -> None:
    url = "https://www.youtube.com/playlist?list=PL123"
    assert detect_url_type(url) == "playlist"


def test_detect_url_type_video_watch() -> None:
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert detect_url_type(url) == "video"


def test_detect_url_type_video_short() -> None:
    url = "https://youtu.be/dQw4w9WgXcQ"
    assert detect_url_type(url) == "video"


def test_detect_url_type_channel() -> None:
    url = "https://www.youtube.com/@channel"
    assert detect_url_type(url) == "channel"


def test_validate_resolution_none() -> None:
    assert validate_resolution(None) is None


def test_validate_resolution_valid() -> None:
    assert validate_resolution(1080) == 1080


def test_validate_resolution_invalid_range() -> None:
    with pytest.raises(ValueError):
        validate_resolution(5000)


def test_validate_delay_valid() -> None:
    assert validate_delay(10) == 10


def test_validate_delay_negative() -> None:
    with pytest.raises(ValueError):
        validate_delay(-1)


def test_validate_batch_size_valid() -> None:
    assert validate_batch_size(5) == 5


def test_validate_batch_size_invalid() -> None:
    with pytest.raises(ValueError):
        validate_batch_size(0)
