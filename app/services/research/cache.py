"""
In-process TTL cache for research/news results.

No Redis required — uses a simple dict with timestamps.
TTL defaults to settings.RESEARCH_CACHE_TTL_SECONDS (30 min).

The SQLite tables (ResearchItem, NewsItem) serve as persistent cache
across restarts.  The in-process dict avoids hammering the DB for
hot queries within a single process lifetime.
"""
from __future__ import annotations
import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

_store: dict[str, tuple[Any, float]] = {}
_lock = asyncio.Lock()


def _cache_key(prefix: str, **kwargs: Any) -> str:
    raw = json.dumps({**kwargs}, sort_keys=True, default=str)
    return f"{prefix}:{hashlib.md5(raw.encode()).hexdigest()}"


async def get(key: str) -> Optional[Any]:
    async with _lock:
        entry = _store.get(key)
        if not entry:
            return None
        value, ts = entry
        age = (datetime.now(timezone.utc).timestamp() - ts)
        if age > settings.RESEARCH_CACHE_TTL_SECONDS:
            del _store[key]
            return None
        return value


async def set(key: str, value: Any) -> None:
    async with _lock:
        _store[key] = (value, datetime.now(timezone.utc).timestamp())


async def invalidate(prefix: str) -> int:
    """Delete all cache entries whose key starts with prefix."""
    async with _lock:
        to_delete = [k for k in _store if k.startswith(prefix)]
        for k in to_delete:
            del _store[k]
        return len(to_delete)


def make_key(prefix: str, **kwargs: Any) -> str:
    return _cache_key(prefix, **kwargs)
