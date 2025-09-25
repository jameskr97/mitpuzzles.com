from typing import Optional, Any
from datetime import datetime, timedelta, UTC
from dataclasses import dataclass


@dataclass
class CachedItem:
    data: Any
    etag: str
    expires: datetime


class AppCache:
    """simple application cache - reset if app restarts"""

    def __init__(self):
        self._cache = {}

    def get(self, key: str) -> Optional[CachedItem]:
        if key in self._cache:
            entry = self._cache[key]
            if datetime.now(UTC) < entry.expires:
                return entry
            else:
                del self._cache[key]
        return None

    def set(self, key: str, data: Any, etag: str, ttl_seconds: int = 300):
        self._cache[key] = CachedItem(data, etag, datetime.now(UTC) + timedelta(seconds=ttl_seconds))


app_cache = AppCache()
