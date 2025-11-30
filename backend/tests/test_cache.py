"""
Tests for the video cache module.
"""
import pytest
import time

from app.library.cache import VideoCache


class TestVideoCache:
    """Tests for VideoCache class."""

    def test_cache_miss_empty(self):
        """Test cache miss on empty cache."""
        cache = VideoCache(ttl_seconds=30)
        result = cache.get("./downloads")
        assert result is None

    def test_cache_set_and_get(self):
        """Test setting and getting from cache."""
        cache = VideoCache(ttl_seconds=30)
        videos = [{"id": "test.mp4", "title": "Test"}]

        cache.set("./downloads", videos)
        result = cache.get("./downloads")

        assert result == videos

    def test_cache_ttl_expiry(self):
        """Test cache expires after TTL."""
        cache = VideoCache(ttl_seconds=1)  # 1 second TTL
        videos = [{"id": "test.mp4", "title": "Test"}]

        cache.set("./downloads", videos)
        assert cache.get("./downloads") is not None

        # Wait for TTL to expire
        time.sleep(1.1)
        assert cache.get("./downloads") is None

    def test_cache_invalidate_specific(self):
        """Test invalidating specific directory."""
        cache = VideoCache(ttl_seconds=30)

        cache.set("./downloads", [{"id": "1"}])
        cache.set("./other", [{"id": "2"}])

        cache.invalidate("./downloads")

        assert cache.get("./downloads") is None
        assert cache.get("./other") is not None

    def test_cache_invalidate_all(self):
        """Test invalidating all cache entries."""
        cache = VideoCache(ttl_seconds=30)

        cache.set("./downloads", [{"id": "1"}])
        cache.set("./other", [{"id": "2"}])

        cache.invalidate()  # No argument = invalidate all

        assert cache.get("./downloads") is None
        assert cache.get("./other") is None

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = VideoCache(ttl_seconds=30)

        # Initial stats
        stats = cache.stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0

        # Miss
        cache.get("./downloads")
        stats = cache.stats()
        assert stats["misses"] == 1

        # Set and hit
        cache.set("./downloads", [])
        cache.get("./downloads")
        stats = cache.stats()
        assert stats["hits"] == 1

    def test_cache_thread_safety(self):
        """Test cache is thread-safe."""
        import threading

        cache = VideoCache(ttl_seconds=30)
        errors = []

        def writer():
            try:
                for i in range(100):
                    cache.set(f"./dir{i}", [{"id": str(i)}])
            except Exception as e:
                errors.append(e)

        def reader():
            try:
                for i in range(100):
                    cache.get(f"./dir{i}")
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=writer),
            threading.Thread(target=reader),
            threading.Thread(target=writer),
            threading.Thread(target=reader),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
