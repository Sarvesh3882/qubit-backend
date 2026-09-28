"""
Crossref provider — DOI / journal / publisher metadata enrichment.

Used primarily to enrich existing items, not as a primary search source.
Free, no API key required.
Docs: https://www.crossref.org/documentation/retrieve-metadata/rest-api/
"""
from __future__ import annotations
import logging
from typing import Any, Optional

import httpx

from .base_provider import BaseResearchProvider
from .models import Author, ResearchItem

logger = logging.getLogger(__name__)

BASE_URL = "https://api.crossref.org/works"
TIMEOUT  = 12.0
HEADERS  = {"User-Agent": "QUBIT-Research/1.0 (mailto:support@qubit.example)"}


def _norm(raw: dict[str, Any]) -> ResearchItem:
    msg = raw.get("message", raw)  # /works/{doi} wraps in "message"

    doi   = msg.get("DOI", "")
    title = " ".join(msg.get("title", ["Untitled"]))

    # Authors
    authors = []
    for a in msg.get("author", []):
        given  = a.get("given", "")
        family = a.get("family", "")
        name   = f"{given} {family}".strip() or a.get("name", "")
        aff    = None
        affils = a.get("affiliation", [])
        if affils:
            aff = affils[0].get("name")
        authors.append(Author(name=name, affiliation=aff))

    # Publication date
    pub_date = None
    for date_field in ("published", "published-print", "published-online"):
        dp = msg.get(date_field, {}).get("date-parts")
        if dp and dp[0]:
            parts = dp[0]
            pub_date = "-".join(str(p).zfill(2) for p in parts[:3]).rstrip("-0").lstrip("0-")
            if pub_date:
                break

    journal   = None
    publisher = msg.get("publisher")
    ct_title  = msg.get("container-title", [])
    if ct_title:
        journal = ct_title[0]

    # Open access URL
    url     = f"https://doi.org/{doi}" if doi else None
    pdf_url = msg.get("link", [{}])[0].get("URL") if msg.get("link") else None

    # Topics from subject
    topics = msg.get("subject", [])[:8]

    return ResearchItem(
        id=f"crossref:{doi}",
        source="crossref",
        external_id=doi,
        doi=doi,
        title=title,
        abstract=msg.get("abstract"),
        authors=authors,
        publication_date=pub_date,
        journal=journal,
        publisher=publisher,
        url=url,
        pdf_url=pdf_url,
        citation_count=msg.get("is-referenced-by-count", 0),
        topics=topics,
        categories=[],
        source_ids={"crossref": doi, "doi": doi},
    )


class CrossrefProvider(BaseResearchProvider):

    @property
    def name(self) -> str:
        return "crossref"

    async def search(
        self,
        query: str,
        page: int = 1,
        per_page: int = 10,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[ResearchItem]:
        """Crossref is used for enrichment, not primary search — returns limited results."""
        params = {
            "query":   query,
            "rows":    per_page,
            "offset":  (page - 1) * per_page,
            "select":  "DOI,title,author,published,container-title,publisher,"
                       "is-referenced-by-count,subject,link,abstract",
        }
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(BASE_URL, params=params, headers=HEADERS)
                resp.raise_for_status()
                items = resp.json().get("message", {}).get("items", [])
                return [_norm({"message": i}) for i in items]
        except httpx.TimeoutException:
            logger.warning("Crossref search timed out for query=%r", query)
            return []
        except Exception as exc:
            logger.warning("Crossref search error: %s", exc)
            return []

    async def get_by_id(self, external_id: str) -> Optional[ResearchItem]:
        """Look up by DOI."""
        encoded = external_id.replace("/", "%2F")
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(f"{BASE_URL}/{encoded}", headers=HEADERS)
                resp.raise_for_status()
                return _norm(resp.json())
        except Exception as exc:
            logger.warning("Crossref get_by_id error: %s", exc)
            return None
