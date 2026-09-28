"""
GNews provider — quantum computing news.

Requires GNEWS_API_KEY.  Free tier: 100 requests/day, 10 articles/request.
Docs: https://gnews.io/docs/v4
"""
from __future__ import annotations
import hashlib
import logging
from typing import Any, Optional

import httpx

from app.core.config import settings
from .models import NewsItem

logger = logging.getLogger(__name__)

BASE_URL = "https://gnews.io/api/v4"
TIMEOUT  = 12.0

DEFAULT_TOPICS = [
    "quantum computing",
    "quantum algorithm",
    "quantum hardware",
    "quantum error correction",
    "qubit",
]


def _url_hash(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:16]


def _norm_article(raw: dict[str, Any], query: str = "") -> NewsItem:
    url = raw.get("url", "")
    return NewsItem(
        id=f"gnews:{_url_hash(url)}",
        source="gnews",
        external_id=_url_hash(url),
        title=raw.get("title", ""),
        description=raw.get("description"),
        content=raw.get("content"),
        url=url,
        image_url=raw.get("image"),
        publisher=raw.get("source", {}).get("name"),
        published_at=raw.get("publishedAt"),
        topics=[query] if query else DEFAULT_TOPICS[:1],
    )


async def search_news(
    query: str,
    max_results: int = 10,
    lang: str = "en",
    from_date: Optional[str] = None,
) -> list[NewsItem]:
    if not settings.GNEWS_API_KEY:
        logger.warning("GNEWS_API_KEY not set — news search unavailable")
        return []
    params: dict[str, Any] = {
        "q":       query,
        "max":     min(max_results, 10),   # free tier max = 10
        "lang":    lang,
        "apikey":  settings.GNEWS_API_KEY,
    }
    if from_date:
        params["from"] = from_date
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(f"{BASE_URL}/search", params=params)
            resp.raise_for_status()
            articles = resp.json().get("articles", [])
            return [_norm_article(a, query) for a in articles]
    except httpx.TimeoutException:
        logger.warning("GNews search timed out for query=%r", query)
        return []
    except Exception as exc:
        logger.warning("GNews search error: %s", exc)
        return []


async def latest_news(
    topic: str = "quantum computing",
    max_results: int = 10,
    lang: str = "en",
) -> list[NewsItem]:
    return await search_news(topic, max_results, lang)
