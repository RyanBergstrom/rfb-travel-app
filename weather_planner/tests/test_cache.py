import pytest
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'weather_planner'))

from backend.services.cache_service import CacheService


class TestCacheService:
    def test_set_and_get(self):
        cache = CacheService(ttl_seconds=60)
        cache.set("key1", {"data": "test"})
        result = cache.get("key1")
        assert result == {"data": "test"}

    def test_get_missing_key(self):
        cache = CacheService(ttl_seconds=60)
        result = cache.get("nonexistent")
        assert result is None

    def test_ttl_expiration(self):
        cache = CacheService(ttl_seconds=1)
        cache.set("key1", "value1")
        time.sleep(1.1)
        result = cache.get("key1")
        assert result is None

    def test_invalidate(self):
        cache = CacheService(ttl_seconds=60)
        cache.set("key1", "value1")
        cache.invalidate("key1")
        result = cache.get("key1")
        assert result is None

    def test_invalidate_missing_key(self):
        cache = CacheService(ttl_seconds=60)
        cache.invalidate("nonexistent")
        assert cache.get("nonexistent") is None

    def test_invalidate_all(self):
        cache = CacheService(ttl_seconds=60)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.invalidate_all()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_is_valid(self):
        cache = CacheService(ttl_seconds=60)
        cache.set("key1", "value1")
        assert cache.is_valid("key1") is True

    def test_is_valid_expired(self):
        cache = CacheService(ttl_seconds=1)
        cache.set("key1", "value1")
        time.sleep(1.1)
        assert cache.is_valid("key1") is False

    def test_is_valid_missing(self):
        cache = CacheService(ttl_seconds=60)
        assert cache.is_valid("nonexistent") is False

    def test_overwrite_key(self):
        cache = CacheService(ttl_seconds=60)
        cache.set("key1", "value1")
        cache.set("key1", "value2")
        assert cache.get("key1") == "value2"

    def test_multiple_keys(self):
        cache = CacheService(ttl_seconds=60)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        assert cache.get("a") == 1
        assert cache.get("b") == 2
        assert cache.get("c") == 3
