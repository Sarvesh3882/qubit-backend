"""
News Intelligence API.

Powered by GNews.  API key is server-side only.

Endpoints:
  GET /news/latest   — latest quantum-computing news
  GET /news/search   — keyword news search
"""
from __future__ import annotations
import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query

from app.services.research.gnews import latest_news, search_news
from app.services.research import cache as news_cache
from app.services.research.models import NewsItem

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/news", tags=["news"])


def _item_to_dict(item: NewsItem) -> dict[str, Any]:
    return {
        "id":           item.id,
        "source":       item.source,
        "title":        item.title,
        "description":  item.description,
        "content":      item.content,
        "url":          item.url,
        "image_url":    item.image_url,
        "publisher":    item.publisher,
        "published_at": item.published_at,
        "topics":       item.topics,
    }


@router.get("/latest")
async def get_latest_news(
    topic: str = Query("quantum computing", max_length=200),
    max_results: int = Query(10, ge=1, le=10),
    lang: str = Query("en", max_length=5),
):
    """Return the most recent quantum-computing news articles."""
    cache_key = news_cache.make_key("news:latest", topic=topic, max_results=max_results, lang=lang)
    cached = await news_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        items = await latest_news(topic=topic, max_results=max_results, lang=lang)
    except Exception as exc:
        logger.exception("News latest failed: %s", exc)
        raise HTTPException(status_code=502, detail="News feed temporarily unavailable")

    result = {
        "topic":   topic,
        "results": [_item_to_dict(i) for i in items],
        "count":   len(items),
    }
    await news_cache.set(cache_key, result)
    return result


@router.get("/search")
async def search_news_endpoint(
    q: str = Query(..., min_length=1, max_length=200),
    max_results: int = Query(10, ge=1, le=10),
    lang: str = Query("en", max_length=5),
    from_date: Optional[str] = Query(None, description="ISO date YYYY-MM-DD"),
):
    """Search for news articles matching a keyword."""
    cache_key = news_cache.make_key("news:search", q=q, max_results=max_results, lang=lang, from_date=from_date)
    cached = await news_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        items = await search_news(query=q, max_results=max_results, lang=lang, from_date=from_date)
    except Exception as exc:
        logger.exception("News search failed: %s", exc)
        raise HTTPException(status_code=502, detail="News search temporarily unavailable")

    result = {
        "query":   q,
        "results": [_item_to_dict(i) for i in items],
        "count":   len(items),
    }
    await news_cache.set(cache_key, result)
    return result
