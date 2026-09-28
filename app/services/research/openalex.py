"""
OpenAlex provider.

OpenAlex is the primary research discovery source.
Free, no API key required — but providing a polite-pool email gives higher
rate limits.  Rate limit without email: ~10 req/s.  With email: higher.

Docs: https://docs.openalex.org
"""
from __future__ import annotations
import asyncio
import logging
from typing import Any, Optional

import httpx

from app.core.config import settings
from .base_provider import BaseResearchProvider
from .models import Author, ResearchItem

logger = logging.getLogger(__name__)

BASE_URL = "https://api.openalex.org"
TIMEOUT  = 15.0


def _headers() -> dict[str, str]:
    h = {"User-Agent": "QUBIT-Research/1.0 (https://github.com/qubit)"}
    if settings.OPENALEX_EMAIL:
        h["mailto"] = settings.OPENALEX_EMAIL
    return h


def _norm(raw: dict[str, Any]) -> ResearchItem:
    """Normalize a single OpenAlex Work object."""
    work_id = raw.get("id", "")           # "https://openalex.org/W1234"
    ext_id  = work_id.split("/")[-1] if "/" in work_id else work_id

    # DOI
    doi = raw.get("doi")
    if doi and doi.startswith("https://doi.org/"):
        doi = doi[len("https://doi.org/"):]

    # arXiv ID from locations
    arxiv_id: Optional[str] = None
    for loc in raw.get("locations", []):
        src = loc.get("source") or {}
        if "arxiv" in (src.get("display_name") or "").lower():
            lp = loc.get("landing_page_url") or ""
            if "arxiv.org/abs/" in lp:
                arxiv_id = lp.split("arxiv.org/abs/")[-1].split("v")[0]
            break

    # Authors
    authors = [
        Author(
            name=a.get("author", {}).get("display_name", ""),
            id=a.get("author", {}).get("id", ""),
            affiliation=(a.get("institutions") or [{}])[0].get("display_name") if a.get("institutions") else None,
        )
        for a in raw.get("authorships", [])
    ]

    # Topics / concepts
    topics    = [c.get("display_name", "") for c in raw.get("concepts", [])[:8] if c.get("score", 0) > 0.3]
    topics   += [t.get("display_name", "") for t in raw.get("topics", [])[:5]]
    topics    = list(dict.fromkeys(topics))[:12]  # dedup, cap

    # Open-access PDF
    pdf_url = None
    oa = raw.get("open_access") or {}
    if oa.get("oa_url"):
        pdf_url = oa["oa_url"]

    # Best URL
    url = raw.get("doi") or f"https://openalex.org/{ext_id}"

    # Publication date
    pub_date = raw.get("publication_date") or raw.get("publication_year")
    if isinstance(pub_date, int):
        pub_date = str(pub_date)

    # Journal / venue
    journal   = None
    publisher = None
    prim_loc  = raw.get("primary_location") or {}
    src       = prim_loc.get("source") or {}
    if src.get("display_name"):
        journal = src["display_name"]
    if src.get("publisher"):
        publisher = src["publisher"]

    abstract_raw = raw.get("abstract_inverted_index")
    abstract: Optional[str] = None
    if abstract_raw:
        try:
            word_list = sorted(
                ((w, min(positions)) for w, positions in abstract_raw.items()),
                key=lambda x: x[1],
            )
            abstract = " ".join(w for w, _ in word_list)[:2000]
        except Exception:
            pass

    return ResearchItem(
        id=f"openalex:{ext_id}",
        source="openalex",
        external_id=ext_id,
        doi=doi or None,
        arxiv_id=arxiv_id,
        title=raw.get("title") or raw.get("display_name") or "Untitled",
        abstract=abstract,
        authors=authors,
        publication_date=pub_date,
        updated_date=raw.get("updated_date"),
        journal=journal,
        publisher=publisher,
        url=url,
        pdf_url=pdf_url,
        citation_count=raw.get("cited_by_count", 0),
        topics=topics,
        categories=[],
        source_ids={"openalex": ext_id, **({"doi": doi} if doi else {}), **({"arxiv": arxiv_id} if arxiv_id else {})},
    )


class OpenAlexProvider(BaseResearchProvider):

    @property
    def name(self) -> str:
        return "openalex"

    async def search(
        self,
        query: str,
        page: int = 1,
        per_page: int = 10,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[ResearchItem]:
        params: dict[str, Any] = {
            "search":    query,
            "per-page":  per_page,
            "page":      page,
            "select":    "id,title,abstract_inverted_index,authorships,concepts,topics,"
                         "publication_date,updated_date,doi,open_access,locations,"
                         "primary_location,cited_by_count,open_access",
        }
        if filters:
            if filters.get("from_date"):
                params["filter"] = f"publication_date:>{filters['from_date']}"
        if settings.OPENALEX_EMAIL:
            params["mailto"] = settings.OPENALEX_EMAIL

        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(f"{BASE_URL}/works", params=params, headers=_headers())
                resp.raise_for_status()
                data = resp.json()
                return [_norm(w) for w in data.get("results", [])]
        except httpx.TimeoutException:
            logger.warning("OpenAlex search timed out for query=%r", query)
            return []
        except Exception as exc:
            logger.warning("OpenAlex search error: %s", exc)
            return []

    async def get_by_id(self, external_id: str) -> Optional[ResearchItem]:
        # external_id may be "W1234" or full URL
        if not external_id.startswith("http"):
            url = f"{BASE_URL}/works/{external_id}"
        else:
            url = external_id
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(url, headers=_headers())
                resp.raise_for_status()
                return _norm(resp.json())
        except Exception as exc:
            logger.warning("OpenAlex get_by_id error: %s", exc)
            return None

    async def get_related(self, external_id: str, limit: int = 5) -> list[ResearchItem]:
        """Use concept similarity to find related papers."""
        item = await self.get_by_id(external_id)
        if not item or not item.topics:
            return []
        concept_query = " ".join(item.topics[:3])
        results = await self.search(concept_query, per_page=limit + 1)
        return [r for r in results if r.external_id != external_id][:limit]

    async def get_citations(self, external_id: str, limit: int = 20) -> list[ResearchItem]:
        params: dict[str, Any] = {
            "filter":   f"cites:{external_id}",
            "per-page": limit,
            "select":   "id,title,abstract_inverted_index,authorships,concepts,"
                        "publication_date,doi,open_access,cited_by_count,primary_location",
            "sort":     "cited_by_count:desc",
        }
        if settings.OPENALEX_EMAIL:
            params["mailto"] = settings.OPENALEX_EMAIL
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(f"{BASE_URL}/works", params=params, headers=_headers())
                resp.raise_for_status()
                return [_norm(w) for w in resp.json().get("results", [])]
        except Exception as exc:
            logger.warning("OpenAlex get_citations error: %s", exc)
            return []
