"""
Semantic Scholar provider — related papers, citations, enrichment.

Unauthenticated endpoints are used by default (100 requests per 5 minutes).
If SEMANTIC_SCHOLAR_API_KEY is set in the environment, it is added as the
x-api-key header, raising the rate limit to 1 req/s with higher quotas.

No API key is required for initial use.

Docs: https://api.semanticscholar.org/api-docs/
"""
from __future__ import annotations
import logging
from typing import Any, Optional

import httpx

from app.core.config import settings
from .base_provider import BaseResearchProvider
from .models import Author, ResearchItem

logger = logging.getLogger(__name__)

BASE_URL = "https://api.semanticscholar.org/graph/v1"
TIMEOUT  = 15.0

# Fields for search responses — keep lean to avoid 400s on free tier
SEARCH_FIELDS = (
    "paperId,externalIds,title,abstract,authors,year,"
    "publicationDate,venue,journal,citationCount,openAccessPdf,fieldsOfStudy"
)

# Fields for single-paper detail
DETAIL_FIELDS = (
    "paperId,externalIds,title,abstract,authors,year,"
    "publicationDate,venue,journal,publisher,citationCount,"
    "openAccessPdf,fieldsOfStudy,topics"
)


def _headers() -> dict[str, str]:
    """Return headers. Key is optional — unauthenticated works fine at lower rate limits."""
    h: dict[str, str] = {}
    key = getattr(settings, "SEMANTIC_SCHOLAR_API_KEY", None)
    if key:
        h["x-api-key"] = key
    return h


def _norm(raw: dict[str, Any]) -> Optional[ResearchItem]:
    """Normalize a Semantic Scholar paper object. Returns None if title is missing."""
    title = raw.get("title")
    if not title:
        return None

    ext = raw.get("externalIds") or {}
    doi      = ext.get("DOI")
    arxiv_id = ext.get("ArXiv")
    ss_id    = raw.get("paperId", "")

    authors = [
        Author(name=a.get("name", ""), id=a.get("authorId"))
        for a in (raw.get("authors") or [])
        if a.get("name")
    ]

    pdf_url = None
    oa = raw.get("openAccessPdf") or {}
    if oa.get("url"):
        pdf_url = oa["url"]

    # Topics and fields of study
    topics: list[str] = []
    for fos in raw.get("fieldsOfStudy") or []:
        if isinstance(fos, str):
            topics.append(fos)
        elif isinstance(fos, dict) and fos.get("category"):
            topics.append(fos["category"])
    for t in raw.get("topics") or []:
        name = t.get("topic") if isinstance(t, dict) else t
        if name and name not in topics:
            topics.append(name)

    pub_date = raw.get("publicationDate") or (str(raw["year"]) if raw.get("year") else None)

    # Journal / venue
    journal = None
    j = raw.get("journal") or {}
    if isinstance(j, dict) and j.get("name"):
        journal = j["name"]
    elif raw.get("venue"):
        journal = str(raw["venue"])

    return ResearchItem(
        id=f"semantic_scholar:{ss_id}",
        source="semantic_scholar",
        external_id=ss_id,
        doi=doi,
        arxiv_id=arxiv_id,
        title=title,
        abstract=raw.get("abstract"),
        authors=authors,
        publication_date=pub_date,
        journal=journal,
        publisher=raw.get("publisher"),
        url=f"https://www.semanticscholar.org/paper/{ss_id}" if ss_id else None,
        pdf_url=pdf_url,
        citation_count=raw.get("citationCount", 0),
        topics=topics[:10],
        categories=[],
        source_ids={
            "semantic_scholar": ss_id,
            **({"doi": doi} if doi else {}),
            **({"arxiv": arxiv_id} if arxiv_id else {}),
        },
    )


class SemanticScholarProvider(BaseResearchProvider):

    @property
    def name(self) -> str:
        return "semantic_scholar"

    async def search(
        self,
        query: str,
        page: int = 1,
        per_page: int = 10,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[ResearchItem]:
        offset = (page - 1) * per_page
        params: dict[str, Any] = {
            "query":  query,
            "offset": offset,
            "limit":  per_page,
            "fields": SEARCH_FIELDS,
        }
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(
                    f"{BASE_URL}/paper/search",
                    params=params,
                    headers=_headers(),
                )
                if resp.status_code == 429:
                    logger.warning("Semantic Scholar rate limited (search) — skipping")
                    return []
                resp.raise_for_status()
                items = [_norm(p) for p in resp.json().get("data", [])]
                return [i for i in items if i is not None]
        except httpx.TimeoutException:
            logger.warning("Semantic Scholar search timed out for query=%r", query)
            return []
        except Exception as exc:
            logger.warning("Semantic Scholar search error: %s", exc)
            return []

    async def get_by_id(self, external_id: str) -> Optional[ResearchItem]:
        """
        Accept any of:
          - SS paperId              e.g. "649def34f8be52c8b66281af98ae884c09aef38b"
          - DOI:10.1234/xyz         prefixed
          - ARXIV:2504.02455        prefixed
          - plain DOI or arXiv ID  (auto-prefixed)
        """
        # Auto-prefix plain arXiv IDs (YYYY.NNNNN format)
        import re
        from urllib.parse import quote
        if re.match(r"^\d{4}\.\d{4,5}(v\d+)?$", external_id):
            external_id = f"ARXIV:{external_id}"
        # Auto-prefix plain DOIs
        elif external_id.startswith("10."):
            external_id = f"DOI:{external_id}"

        # URL-encode the id so DOI slashes don't break the path segment
        # e.g. "DOI:10.1038/nature09866" → "DOI%3A10.1038%2Fnature09866"
        encoded_id = quote(external_id, safe="")
        url = f"{BASE_URL}/paper/{encoded_id}"
        params = {"fields": DETAIL_FIELDS}
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(url, params=params, headers=_headers())
                if resp.status_code == 404:
                    return None
                if resp.status_code == 429:
                    logger.warning("Semantic Scholar rate limited (get_by_id)")
                    return None
                resp.raise_for_status()
                return _norm(resp.json())
        except Exception as exc:
            logger.warning("Semantic Scholar get_by_id error: %s", exc)
            return None

    async def get_related(self, external_id: str, limit: int = 5) -> list[ResearchItem]:
        """
        Uses the Semantic Scholar Recommendations API (unauthenticated, free tier).
        Accepts the same ID formats as get_by_id.
        """
        import re
        from urllib.parse import quote
        if re.match(r"^\d{4}\.\d{4,5}(v\d+)?$", external_id):
            external_id = f"ARXIV:{external_id}"
        elif external_id.startswith("10."):
            external_id = f"DOI:{external_id}"

        encoded_id = quote(external_id, safe="")
        url = f"{BASE_URL}/paper/{encoded_id}/recommendations"
        params: dict[str, Any] = {
            "fields": "paperId,externalIds,title,authors,year,citationCount,openAccessPdf",
            "limit":  limit,
        }
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(url, params=params, headers=_headers())
                if resp.status_code in (404, 429):
                    logger.warning("Semantic Scholar recommendations: HTTP %s", resp.status_code)
                    return []
                resp.raise_for_status()
                items = [_norm(p) for p in resp.json().get("recommendedPapers", [])]
                return [i for i in items if i is not None][:limit]
        except Exception as exc:
            logger.warning("Semantic Scholar get_related error: %s", exc)
            return []

    async def get_citations(self, external_id: str, limit: int = 20) -> list[ResearchItem]:
        """Return papers that cite the given paper."""
        import re
        from urllib.parse import quote
        if re.match(r"^\d{4}\.\d{4,5}(v\d+)?$", external_id):
            external_id = f"ARXIV:{external_id}"
        elif external_id.startswith("10."):
            external_id = f"DOI:{external_id}"

        encoded_id = quote(external_id, safe="")
        url = f"{BASE_URL}/paper/{encoded_id}/citations"
        params: dict[str, Any] = {
            "fields": (
                "citingPaper.paperId,citingPaper.externalIds,citingPaper.title,"
                "citingPaper.authors,citingPaper.year,citingPaper.citationCount,"
                "citingPaper.openAccessPdf"
            ),
            "limit": limit,
        }
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(url, params=params, headers=_headers())
                if resp.status_code in (404, 429):
                    logger.warning("Semantic Scholar citations: HTTP %s", resp.status_code)
                    return []
                resp.raise_for_status()
                items = [
                    _norm(c["citingPaper"])
                    for c in resp.json().get("data", [])
                    if c.get("citingPaper")
                ]
                return [i for i in items if i is not None]
        except Exception as exc:
            logger.warning("Semantic Scholar get_citations error: %s", exc)
            return []
