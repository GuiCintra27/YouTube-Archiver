"""
Helpers to run blocking IO without freezing the event loop.
"""
from __future__ import annotations

import asyncio
from typing import Callable, Optional, TypeVar

from app.config import settings
from app.core.logging import get_module_logger

T = TypeVar("T")

logger = get_module_logger("core.blocking")

_SEMAPHORES: dict[str, asyncio.Semaphore] = {}


def _get_semaphore(name: str, limit: int) -> asyncio.Semaphore:
    semaphore = _SEMAPHORES.get(name)
    if semaphore is None:
        semaphore = asyncio.Semaphore(limit)
        _SEMAPHORES[name] = semaphore
    return semaphore


def get_drive_semaphore() -> asyncio.Semaphore:
    return _get_semaphore("drive", settings.BLOCKING_DRIVE_CONCURRENCY)


def get_fs_semaphore() -> asyncio.Semaphore:
    return _get_semaphore("fs", settings.BLOCKING_FS_CONCURRENCY)


def get_catalog_semaphore() -> asyncio.Semaphore:
    return _get_semaphore("catalog", settings.BLOCKING_CATALOG_CONCURRENCY)


async def run_blocking(
    fn: Callable[..., T],
    *args,
    semaphore: Optional[asyncio.Semaphore] = None,
    label: Optional[str] = None,
    **kwargs,
) -> T:
    if semaphore is None:
        return await asyncio.to_thread(fn, *args, **kwargs)

    async with semaphore:
        if label:
            logger.debug(f"Blocking start: {label}")
        try:
            return await asyncio.to_thread(fn, *args, **kwargs)
        finally:
            if label:
                logger.debug(f"Blocking end: {label}")


async def run_drive_blocking(
    fn: Callable[..., T],
    *args,
    label: Optional[str] = None,
    **kwargs,
) -> T:
    return await run_blocking(
        fn,
        *args,
        semaphore=get_drive_semaphore(),
        label=label,
        **kwargs,
    )


async def run_fs_blocking(
    fn: Callable[..., T],
    *args,
    label: Optional[str] = None,
    **kwargs,
) -> T:
    return await run_blocking(
        fn,
        *args,
        semaphore=get_fs_semaphore(),
        label=label,
        **kwargs,
    )
