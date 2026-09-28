"""
arXiv provider — recent preprints.

Uses the arXiv Atom API (no key required).
Rate limit: max 1 request per 3 seconds recommended.
Docs: https://info.arxiv.org/help/api/index.html
"""
from __future__ import annotations
import logging
import re
import xml.etree.ElementTree as ET
from typing import Any, Optional

import httpx

from .base_provider import BaseResearchProvider
from .models import Author, ResearchItem

logger = logging.getLogger(__name__)

BASE_URL = "https://export.arxiv.org/api/query"
TIMEOUT  = 15.0
NS       = {
    "atom":   "http://www.w3.org/2005/Atom",
    "arxiv":  "http://arxiv.org/schemas/atom",
    "openSearch": "http://a9.com/-/spec/opensearch/1.1/",
}


def _arxiv_id_from_url(url: str) -> str:
    """Extract arXiv ID like '2504.02455' from an arxiv URL."""
    m = re.search(r"arxiv\.org/(?:abs|pdf)/([^\s/v]+(?:v\d+)?)", url)
    return m.group(1).split("v")[0] if m else url.split("/")[-1]


def _norm_entry(entry: ET.Element) -> ResearchItem:
    """Normalize one <entry> element from the arXiv Atom feed."""
    def t(tag: str) -> str:
        el = entry.find(f"atom:{tag}", NS)
        return (el.text or "").strip() if el is not None else ""

    arxiv_id_raw = t("id")
    arxiv_id = _arxiv_id_from_url(arxiv_id_raw)

    title   = re.sub(r"\s+", " ", t("title")).strip()
    summary = re.sub(r"\s+", " ", t("summary")).strip()[:2000]
    updated = t("updated")[:10] if t("updated") else None
    pub     = t("published")[:10] if t("published") else None

    authors = [
        Author(name=a.find("atom:name", NS).text.strip())
        for a in entry.findall("atom:author", NS)
        if a.find("atom:name", NS) is not None
    ]

    # DOI
    doi: Optional[str] = None
    doi_el = entry.find("arxiv:doi", NS)
    if doi_el is not None and doi_el.text:
        doi = doi_el.text.strip()

    # PDF link
    pdf_url: Optional[str] = None
    for link in entry.findall("atom:link", NS):
        if link.get("type") == "application/pdf":
            pdf_url = link.get("href")
            break

    # Abstract URL
    abs_url = f"https://arxiv.org/abs/{arxiv_id}"

    # Categories
    cats = [
        c.get("term", "")
        for c in entry.findall("atom:category", NS)
        if c.get("term")
    ]

    # Journal ref
    journal = None
    jr = entry.find("arxiv:journal_ref", NS)
    if jr is not None and jr.text:
        journal = jr.text.strip()

    return ResearchItem(
        id=f"arxiv:{arxiv_id}",
        source="arxiv",
        external_id=arxiv_id,
        arxiv_id=arxiv_id,
        doi=doi,
        title=title,
        abstract=summary,
        authors=authors,
        publication_date=pub,
        updated_date=updated,
        journal=journal,
        url=abs_url,
        pdf_url=pdf_url,
        citation_count=0,
        categories=cats[:6],
        topics=cats[:6],
        source_ids={"arxiv": arxiv_id, **({"doi": doi} if doi else {})},
    )


class ArxivProvider(BaseResearchProvider):

    @property
    def name(self) -> str:
        return "arxiv"

    async def search(
        self,
        query: str,
        page: int = 1,
        per_page: int = 10,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[ResearchItem]:
        start = (page - 1) * per_page
        params = {
            "search_query": f"all:{query}",
            "start":        start,
            "max_results":  per_page,
            "sortBy":       "submittedDate",
            "sortOrder":    "descending",
        }
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(BASE_URL, params=params)
                resp.raise_for_status()
                root = ET.fromstring(resp.text)
                return [_norm_entry(e) for e in root.findall("atom:entry", NS)]
        except httpx.TimeoutException:
            logger.warning("arXiv search timed out for query=%r", query)
            return []
        except Exception as exc:
            logger.warning("arXiv search error: %s", exc)
            return []

    async def get_by_id(self, external_id: str) -> Optional[ResearchItem]:
        # external_id is the arXiv ID e.g. "2504.02455"
        clean_id = _arxiv_id_from_url(external_id) if "/" in external_id else external_id
        params = {"id_list": clean_id, "max_results": 1}
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(BASE_URL, params=params)
                resp.raise_for_status()
                root = ET.fromstring(resp.text)
                entries = root.findall("atom:entry", NS)
                return _norm_entry(entries[0]) if entries else None
        except Exception as exc:
            logger.warning("arXiv get_by_id error: %s", exc)
            return None
