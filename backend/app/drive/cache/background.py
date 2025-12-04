"""
Background task for periodic Drive cache synchronization.

Runs incremental sync at configured intervals to keep cache up-to-date
with any manual changes made directly in Google Drive.
"""

import asyncio

from app.config import settings
from app.core.logging import get_module_logger
from .sync import incremental_sync, full_sync, ensure_cache_initialized
from .database import get_database

logger = get_module_logger("drive.cache.background")


async def run_cache_sync_loop(interval_minutes: int = None) -> None:
    """
    Background task that periodically syncs Drive cache.

    Runs incremental sync at the configured interval.
    Automatically skips if Drive is not authenticated.

    Args:
        interval_minutes: Override interval (uses settings.DRIVE_CACHE_SYNC_INTERVAL if None)
    """
    if not settings.DRIVE_CACHE_ENABLED:
        logger.info("Drive cache disabled, sync loop not started")
        return

    interval = interval_minutes or settings.DRIVE_CACHE_SYNC_INTERVAL

    logger.info(f"Drive cache sync task started (interval: {interval} minutes)")

    # Wait initial delay to let app fully start and avoid hitting
    # Drive API immediately on startup
    await asyncio.sleep(60)  # 1 minute initial delay

    while True:
        try:
            # Wait for configured interval
            await asyncio.sleep(interval * 60)

            # Check if Drive is authenticated before syncing
            from app.drive.manager import drive_manager

            if not drive_manager.is_authenticated():
                logger.debug("Drive not authenticated, skipping periodic sync")
                continue

            # Run incremental sync
            result = await incremental_sync()

            if result.success:
                if result.changes_detected:
                    logger.info(
                        f"Periodic sync completed: "
                        f"+{result.added} ~{result.updated} -{result.deleted}"
                    )
                else:
                    logger.debug("Periodic sync: no changes detected")
            else:
                logger.warning(f"Periodic sync failed: {result.message}")

        except asyncio.CancelledError:
            logger.info("Drive cache sync task cancelled")
            break

        except Exception as e:
            logger.error(f"Error in cache sync loop: {e}", exc_info=True)
            # Wait a bit before retrying to avoid hammering on errors
            await asyncio.sleep(60)


async def initialize_cache_on_startup() -> None:
    """
    Initialize cache database and optionally trigger initial sync.

    Called during application startup.
    """
    if not settings.DRIVE_CACHE_ENABLED:
        logger.debug("Drive cache disabled")
        return

    try:
        # Initialize database (creates tables if needed)
        db = get_database()
        await db.initialize()
        logger.info("Drive cache database initialized")

    except Exception as e:
        logger.error(f"Failed to initialize cache database: {e}", exc_info=True)


async def trigger_initial_sync_if_authenticated() -> None:
    """
    Check if Drive is authenticated and trigger initial sync if cache is empty.

    This should be called after OAuth callback to populate cache on first auth.
    """
    if not settings.DRIVE_CACHE_ENABLED:
        return

    try:
        from app.drive.manager import drive_manager

        if not drive_manager.is_authenticated():
            return

        # This will trigger full sync if cache is empty
        await ensure_cache_initialized()

    except Exception as e:
        logger.error(f"Failed to trigger initial sync: {e}", exc_info=True)


async def shutdown_cache() -> None:
    """
    Cleanup cache resources on application shutdown.
    """
    try:
        db = get_database()
        await db.close()
        logger.debug("Drive cache closed")
    except Exception as e:
        logger.error(f"Error closing cache: {e}")
