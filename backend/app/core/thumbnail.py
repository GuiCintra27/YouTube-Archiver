"""
Thumbnail generation utilities using ffmpeg.

This module provides functions to automatically generate video thumbnails
from video files using ffmpeg.
"""
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Tuple

from app.core.logging import get_module_logger
from app.core.constants import FileExtensions

logger = get_module_logger("thumbnail")


def is_ffmpeg_available() -> bool:
    """Check if ffmpeg is available on the system."""
    return shutil.which("ffmpeg") is not None


def get_video_duration(video_path: Path) -> Optional[float]:
    """
    Get video duration in seconds using ffprobe.

    Args:
        video_path: Path to the video file

    Returns:
        Duration in seconds or None if unable to determine
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(video_path)
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())

        return None
    except (subprocess.TimeoutExpired, ValueError, FileNotFoundError) as e:
        logger.warning(f"Failed to get video duration: {e}")
        return None


def calculate_thumbnail_timestamp(duration: Optional[float]) -> float:
    """
    Calculate the optimal timestamp for thumbnail extraction.

    Strategy:
    - Use 10% of the video duration (avoids black intro screens)
    - Minimum of 1 second (for very short videos)
    - Maximum of 30 seconds (no need to go further for long videos)
    - Default to 5 seconds if duration is unknown

    Args:
        duration: Video duration in seconds, or None if unknown

    Returns:
        Timestamp in seconds for thumbnail extraction
    """
    if duration is None:
        return 5.0

    # 10% of the video duration
    timestamp = duration * 0.1

    # Clamp between 1 and 30 seconds
    timestamp = max(1.0, min(timestamp, 30.0))

    return timestamp


def generate_thumbnail(
    video_path: Path,
    output_path: Optional[Path] = None,
    timestamp: Optional[float] = None,
    width: int = 1280,
    quality: int = 2
) -> Optional[Path]:
    """
    Generate a thumbnail from a video file using ffmpeg.

    The thumbnail is extracted as a single frame from the video and saved
    as a JPEG image. The default timestamp is calculated to avoid black
    intro screens (typically 10% into the video).

    Args:
        video_path: Path to the video file
        output_path: Output path for thumbnail. If None, uses video name with .jpg extension
        timestamp: Specific timestamp in seconds. If None, auto-calculated
        width: Output width in pixels (height auto-calculated to maintain aspect ratio)
        quality: JPEG quality (2-31, lower is better, 2 is highest quality)

    Returns:
        Path to the generated thumbnail, or None if generation failed

    Example:
        >>> thumbnail = generate_thumbnail(Path("video.mp4"))
        >>> print(thumbnail)  # video.jpg
    """
    if not is_ffmpeg_available():
        logger.error("ffmpeg not available on system")
        return None

    if not video_path.exists():
        logger.error(f"Video file not found: {video_path}")
        return None

    # Determine output path
    if output_path is None:
        output_path = video_path.with_suffix(".jpg")

    # Calculate timestamp if not provided
    if timestamp is None:
        duration = get_video_duration(video_path)
        timestamp = calculate_thumbnail_timestamp(duration)

    logger.debug(f"Generating thumbnail for {video_path.name} at {timestamp:.1f}s")

    try:
        # ffmpeg command:
        # -ss: seek to timestamp (before -i for faster seeking)
        # -i: input file
        # -vframes 1: extract only 1 frame
        # -vf scale: resize maintaining aspect ratio
        # -q:v: JPEG quality (2 = high quality)
        # -y: overwrite output file without asking
        result = subprocess.run(
            [
                "ffmpeg",
                "-ss", str(timestamp),
                "-i", str(video_path),
                "-vframes", "1",
                "-vf", f"scale={width}:-1",
                "-q:v", str(quality),
                "-y",
                str(output_path)
            ],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            logger.warning(f"ffmpeg failed: {result.stderr[:500]}")
            return None

        if not output_path.exists():
            logger.warning(f"Thumbnail file was not created: {output_path}")
            return None

        # Verify file is not empty
        if output_path.stat().st_size < 100:
            logger.warning(f"Thumbnail file is too small, likely invalid: {output_path}")
            output_path.unlink()
            return None

        logger.info(f"Generated thumbnail: {output_path.name}")
        return output_path

    except subprocess.TimeoutExpired:
        logger.error(f"Thumbnail generation timed out for {video_path.name}")
        return None
    except Exception as e:
        logger.error(f"Failed to generate thumbnail: {e}", exc_info=True)
        return None


def find_existing_thumbnail(video_path: Path) -> Optional[Path]:
    """
    Find an existing thumbnail for a video file.

    Searches for files with the same base name but image extensions
    (.jpg, .jpeg, .png, .webp) in the same directory.

    Args:
        video_path: Path to the video file

    Returns:
        Path to existing thumbnail, or None if not found
    """
    base_name = video_path.stem
    parent_dir = video_path.parent

    for ext in FileExtensions.THUMBNAIL:
        thumbnail_path = parent_dir / f"{base_name}{ext}"
        if thumbnail_path.exists():
            return thumbnail_path

    return None


def ensure_thumbnail(
    video_path: Path,
    force: bool = False
) -> Tuple[Optional[Path], bool]:
    """
    Ensure a thumbnail exists for a video, generating one if necessary.

    This is the main function to call when you need a thumbnail for a video.
    It first checks for an existing thumbnail, and if none exists, generates
    one automatically.

    Args:
        video_path: Path to the video file
        force: If True, generate new thumbnail even if one exists

    Returns:
        Tuple of (thumbnail_path, was_generated)
        - thumbnail_path: Path to the thumbnail (existing or newly generated), or None if failed
        - was_generated: True if a new thumbnail was generated, False if using existing

    Example:
        >>> thumb, generated = ensure_thumbnail(Path("video.mp4"))
        >>> if thumb:
        ...     print(f"Thumbnail: {thumb} (generated: {generated})")
    """
    # Check for existing thumbnail first
    if not force:
        existing = find_existing_thumbnail(video_path)
        if existing:
            logger.debug(f"Using existing thumbnail: {existing.name}")
            return existing, False

    # Generate new thumbnail
    thumbnail = generate_thumbnail(video_path)
    if thumbnail:
        return thumbnail, True

    return None, False
