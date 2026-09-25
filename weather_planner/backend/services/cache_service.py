import time
from typing import Any, Optional

CACHE_TTL_SECONDS = 6 * 60 * 60  # 6 hours


class CacheService:
    def __init__(self, ttl_seconds: int = CACHE_TTL_SECONDS):
        self._store: dict[str, dict] = {}
        self.ttl_seconds = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.time() - entry["timestamp"] > self.ttl_seconds:
            del self._store[key]
            return None
        return entry["value"]

    def set(self, key: str, value: Any) -> None:
        self._store[key] = {
            "value": value,
            "timestamp": time.time(),
        }

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def invalidate_all(self) -> None:
        self._store.clear()

    def is_valid(self, key: str) -> bool:
        entry = self._store.get(key)
        if entry is None:
            return False
        return time.time() - entry["timestamp"] <= self.ttl_seconds
