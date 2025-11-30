"""
Library cache - caching layer for video directory scans.

Caches the results of directory scans to avoid repeated I/O operations.
The cache is automatically invalidated after a configurable TTL or
manually when videos are added/deleted.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from threading import Lock

from app.core.logging import get_module_logger

logger = get_module_logger("library.cache")


class VideoCache:
    """
    In-memory cache for video directory scans.

    Thread-safe implementation with TTL-based expiration.
    """

    def __init__(self, ttl_seconds: int = 30):
        """
        Initialize the video cache.

        Args:
            ttl_seconds: Time-to-live for cache entries in seconds
        """
        self._cache: Dict[str, List[Dict[str, Any]]] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._ttl = timedelta(seconds=ttl_seconds)
        self._lock = Lock()
        self._hit_count = 0
        self._miss_count = 0

    def get(self, base_dir: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached videos for a directory if valid.

        Args:
            base_dir: The base directory key

        Returns:
            Cached video list or None if cache miss/expired
        """
        with self._lock:
            if base_dir not in self._cache:
                self._miss_count += 1
                return None

            timestamp = self._timestamps.get(base_dir)
            if timestamp is None or datetime.now() - timestamp > self._ttl:
                # Cache expired
                del self._cache[base_dir]
                del self._timestamps[base_dir]
                self._miss_count += 1
                logger.debug(f"Cache expired for: {base_dir}")
                return None

            self._hit_count += 1
            logger.debug(f"Cache hit for: {base_dir}")
            return self._cache[base_dir]

    def set(self, base_dir: str, videos: List[Dict[str, Any]]) -> None:
        """
        Cache the video list for a directory.

        Args:
            base_dir: The base directory key
            videos: List of video metadata dicts
        """
        with self._lock:
            self._cache[base_dir] = videos
            self._timestamps[base_dir] = datetime.now()
            logger.debug(f"Cache set for: {base_dir} ({len(videos)} videos)")

    def invalidate(self, base_dir: Optional[str] = None) -> None:
        """
        Invalidate cache entries.

        Args:
            base_dir: Specific directory to invalidate, or None for all
        """
        with self._lock:
            if base_dir is None:
                # Invalidate all
                self._cache.clear()
                self._timestamps.clear()
                logger.debug("Cache fully invalidated")
            elif base_dir in self._cache:
                del self._cache[base_dir]
                del self._timestamps[base_dir]
                logger.debug(f"Cache invalidated for: {base_dir}")

    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with hit/miss counts and hit rate
        """
        total = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total * 100) if total > 0 else 0.0

        return {
            "hits": self._hit_count,
            "misses": self._miss_count,
            "hit_rate": f"{hit_rate:.1f}%",
            "cached_dirs": len(self._cache),
            "ttl_seconds": self._ttl.total_seconds(),
        }


# Global cache instance with 30 second TTL
video_cache = VideoCache(ttl_seconds=30)
