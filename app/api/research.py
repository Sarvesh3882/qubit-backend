"""
Research Intelligence API.

All external provider communication happens here — the frontend never
contacts external APIs directly.  API keys remain server-side.

Endpoints:
  GET /research/search        — multi-provider paper search
  GET /research/latest        — most recent papers (no query required)
  GET /research/{id}          — paper detail by composite ID
  GET /research/{id}/related  — related papers
  GET /research/{id}/citations — citing papers
"""
from __future__ import annotations
import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse

from app.services.research import aggregator
from app.services.research import cache as research_cache
from app.services.research.models import ResearchItem

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/research", tags=["research"])

QUANTUM_DEFAULT_QUERIES = [
    "quantum computing",
    "quantum algorithms",
    "quantum error correction",
    "quantum hardware",
    "quantum simulation",
    "quantum machine learning",
    "quantum cryptography",
]


def _item_to_dict(item: ResearchItem) -> dict[str, Any]:
    return {
        "id":               item.id,
        "source":           item.source,
        "external_id":      item.external_id,
        "doi":              item.doi,
        "arxiv_id":         item.arxiv_id,
        "title":            item.title,
        "abstract":         item.abstract,
        "authors":          [a.model_dump() for a in item.authors],
        "publication_date": item.publication_date,
        "updated_date":     item.updated_date,
        "journal":          item.journal,
        "publisher":        item.publisher,
        "url":              item.url,
        "pdf_url":          item.pdf_url,
        "citation_count":   item.citation_count,
        "topics":           item.topics,
        "categories":       item.categories,
        "source_ids":       item.source_ids,
    }


@router.get("/search")
async def search_research(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    page: int = Query(1, ge=1, le=50),
    per_page: int = Query(10, ge=1, le=30),
    sources: Optional[str] = Query(None, description="Comma-separated: openalex,arxiv,semantic_scholar"),
    from_date: Optional[str] = Query(None, description="ISO date YYYY-MM-DD — filter from this date"),
):
    """Search for research papers across providers."""
    source_list = [s.strip() for s in sources.split(",")] if sources else None
    # Only allow the three active providers
    if source_list:
        source_list = [s for s in source_list if s in ("openalex", "arxiv", "crossref")]
    filters = {"from_date": from_date} if from_date else None

    cache_key = research_cache.make_key(
        "research:search", q=q, page=page, per_page=per_page,
        sources=source_list, filters=filters
    )
    cached = await research_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        items = await aggregator.search(
            query=q,
            page=page,
            per_page=per_page,
            sources=source_list,
            filters=filters,
        )
    except Exception as exc:
        logger.exception("Research search failed: %s", exc)
        raise HTTPException(status_code=502, detail="Research search temporarily unavailable")

    result = {
        "query":   q,
        "page":    page,
        "results": [_item_to_dict(i) for i in items],
        "count":   len(items),
    }
    await research_cache.set(cache_key, result)
    return result


@router.get("/latest")
async def latest_research(
    topic: str = Query("quantum computing", max_length=200),
    per_page: int = Query(10, ge=1, le=30),
):
    """Return the most recent papers for a given topic."""
    cache_key = research_cache.make_key("research:latest", topic=topic, per_page=per_page)
    cached = await research_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        items = await aggregator.latest(query=topic, per_page=per_page)
    except Exception as exc:
        logger.exception("Research latest failed: %s", exc)
        raise HTTPException(status_code=502, detail="Research feed temporarily unavailable")

    result = {
        "topic":   topic,
        "results": [_item_to_dict(i) for i in items],
        "count":   len(items),
    }
    await research_cache.set(cache_key, result)
    return result


@router.get("/{item_id:path}/related")
async def related_papers(
    item_id: str,
    limit: int = Query(5, ge=1, le=20),
):
    """Return papers related to the given item."""
    cache_key = research_cache.make_key("research:related", item_id=item_id, limit=limit)
    cached = await research_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        items = await aggregator.get_related(item_id, limit=limit)
    except Exception as exc:
        logger.exception("Related papers failed: %s", exc)
        return {"results": [], "count": 0}

    result = {"results": [_item_to_dict(i) for i in items], "count": len(items)}
    await research_cache.set(cache_key, result)
    return result


@router.get("/{item_id:path}/citations")
async def paper_citations(
    item_id: str,
    limit: int = Query(20, ge=1, le=50),
):
    """Return papers that cite the given item."""
    cache_key = research_cache.make_key("research:citations", item_id=item_id, limit=limit)
    cached = await research_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        items = await aggregator.get_citations(item_id, limit=limit)
    except Exception as exc:
        logger.exception("Citations failed: %s", exc)
        return {"results": [], "count": 0}

    result = {"results": [_item_to_dict(i) for i in items], "count": len(items)}
    await research_cache.set(cache_key, result)
    return result


@router.get("/{item_id:path}")
async def get_paper(item_id: str):
    """Fetch a specific paper by composite ID (source:external_id)."""
    cache_key = research_cache.make_key("research:item", item_id=item_id)
    cached = await research_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        item = await aggregator.get_by_id(item_id)
    except Exception as exc:
        logger.exception("Paper fetch failed: %s", exc)
        raise HTTPException(status_code=502, detail="Research lookup temporarily unavailable")

    if item is None:
        raise HTTPException(status_code=404, detail=f"Paper '{item_id}' not found")

    result = _item_to_dict(item)
    await research_cache.set(cache_key, result)
    return result
