"""
Download service - business logic for downloads
"""
import asyncio
from typing import Optional, Callable

from .downloader import Settings, download_video as yt_download, get_video_info as yt_get_info


async def get_video_info(url: str) -> dict:
    """
    Get video information without downloading.

    Args:
        url: Video URL

    Returns:
        Dict with video information
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, yt_get_info, url)


def create_download_settings(
    out_dir: str,
    archive_file: str,
    fmt: str = "bv*+ba/b",
    max_res: Optional[int] = None,
    subs: bool = True,
    auto_subs: bool = True,
    sub_langs: str = "pt,en",
    thumbnails: bool = True,
    audio_only: bool = False,
    limit: Optional[int] = None,
    cookies_file: Optional[str] = None,
    referer: Optional[str] = None,
    origin: Optional[str] = None,
    user_agent: str = "yt-archiver",
    concurrent_fragments: int = 10,
    custom_path: Optional[str] = None,
    file_name: Optional[str] = None,
    archive_id: Optional[str] = None,
    delay_between_downloads: int = 0,
    batch_size: Optional[int] = None,
    batch_delay: int = 0,
    randomize_delay: bool = False,
) -> Settings:
    """
    Create download settings from parameters.

    Returns:
        Settings object for downloader
    """
    return Settings(
        out_dir=out_dir,
        archive_file=archive_file,
        fmt=fmt,
        max_res=max_res,
        subs=subs,
        auto_subs=auto_subs,
        sub_langs=sub_langs,
        thumbnails=thumbnails,
        audio_only=audio_only,
        workers=1,
        limit=limit,
        dry_run=False,
        drive_upload=False,
        drive_root="YouTubeArchive",
        drive_credentials="./credentials.json",
        drive_token="./token.json",
        uploaded_log="./uploaded.jsonl",
        cookies_file=cookies_file,
        referer=referer,
        origin=origin,
        user_agent=user_agent,
        concurrent_fragments=concurrent_fragments,
        custom_path=custom_path,
        file_name=file_name,
        archive_id=archive_id,
        delay_between_downloads=delay_between_downloads,
        batch_size=batch_size,
        batch_delay=batch_delay,
        randomize_delay=randomize_delay,
    )


async def execute_download(
    url: str,
    settings: Settings,
    progress_callback: Optional[Callable] = None,
) -> dict:
    """
    Execute download in background thread.

    Args:
        url: Video URL
        settings: Download settings
        progress_callback: Optional callback for progress updates

    Returns:
        Dict with download results
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        yt_download,
        url,
        settings,
        progress_callback,
    )
