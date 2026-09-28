"""
Research Aggregator.

Orchestrates four providers:
  - OpenAlex         — primary research discovery
  - arXiv            — recent preprints
  - Semantic Scholar — related papers, citations, opt-in search (unauthenticated free tier)
  - Crossref         — DOI/publication metadata enrichment

Architecture is modular: add providers by implementing BaseResearchProvider
and registering them in the PROVIDERS list below.

Flow:
  search()        → OpenAlex + arXiv + (opt-in) Semantic Scholar — concurrent
                  → normalize → deduplicate → rank
  latest()        → OpenAlex + arXiv — concurrent → deduplicate → rank (recency)
  get_by_id()     → source-appropriate provider + Crossref DOI enrichment
  get_related()   → Semantic Scholar recommendations → OpenAlex fallback
  get_citations() → Semantic Scholar citations       → OpenAlex fallback

Deduplication keys (in priority order):
  1. DOI
  2. arXiv ID
  3. Normalized title + first-author-family + year
"""
from __future__ import annotations
import asyncio
import logging
import re
from datetime import datetime
from typing import Any, Optional

from .models import ResearchItem
from .openalex import OpenAlexProvider
from .arxiv import ArxivProvider
from .semantic_scholar import SemanticScholarProvider
from .crossref import CrossrefProvider

logger = logging.getLogger(__name__)

_oa = OpenAlexProvider()
_ax = ArxivProvider()
_ss = SemanticScholarProvider()
_cr = CrossrefProvider()

# ── Deduplication ─────────────────────────────────────────────────────────────

def _norm_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]", "", title.lower())[:60]


def _dedup_key(item: ResearchItem) -> str:
    if item.doi:
        return f"doi:{item.doi.lower()}"
    if item.arxiv_id:
        return f"arxiv:{item.arxiv_id}"
    year = (item.publication_date or "")[:4]
    author_fam = ""
    if item.authors:
        parts = item.authors[0].name.split()
        author_fam = parts[-1].lower() if parts else ""
    return f"title:{_norm_title(item.title)}:{author_fam}:{year}"


def _merge(primary: ResearchItem, secondary: ResearchItem) -> ResearchItem:
    """Merge secondary metadata into primary, keeping best available fields."""
    merged = primary.model_copy()
    if not merged.abstract and secondary.abstract:
        merged.abstract = secondary.abstract
    if not merged.doi and secondary.doi:
        merged.doi = secondary.doi
    if not merged.arxiv_id and secondary.arxiv_id:
        merged.arxiv_id = secondary.arxiv_id
    if not merged.pdf_url and secondary.pdf_url:
        merged.pdf_url = secondary.pdf_url
    if not merged.journal and secondary.journal:
        merged.journal = secondary.journal
    if not merged.publisher and secondary.publisher:
        merged.publisher = secondary.publisher
    if merged.citation_count == 0 and secondary.citation_count > 0:
        merged.citation_count = secondary.citation_count
    merged.source_ids = {**secondary.source_ids, **primary.source_ids}
    extra_topics = [t for t in secondary.topics if t not in merged.topics]
    merged.topics = (merged.topics + extra_topics)[:12]
    return merged


def deduplicate(items: list[ResearchItem]) -> list[ResearchItem]:
    seen: dict[str, ResearchItem] = {}
    for item in items:
        key = _dedup_key(item)
        if key in seen:
            seen[key] = _merge(seen[key], item)
        else:
            seen[key] = item
    return list(seen.values())


# ── Ranking ───────────────────────────────────────────────────────────────────

def _score(item: ResearchItem, query: str, mode: str = "search") -> float:
    """
    Transparent ranking score using three signals:
      recency · citation count · query-title overlap
    mode="search"  → relevance-first
    mode="latest"  → recency-first
    """
    import math
    score = 0.0

    if item.publication_date:
        try:
            pub = datetime.fromisoformat(item.publication_date[:10])
            days_old = (datetime.utcnow() - pub).days
            if mode == "latest":
                score += max(0.0, 1.0 - days_old / 730)
            else:
                score += max(0.0, 0.3 - days_old / 3650)
        except Exception:
            pass

    if item.citation_count > 0:
        score += min(0.4, math.log10(item.citation_count + 1) / 10)

    q_words = set(query.lower().split())
    t_words = set(item.title.lower().split())
    overlap = len(q_words & t_words) / max(len(q_words), 1)
    score += overlap * 0.4

    completeness = sum([
        bool(item.abstract), bool(item.doi), bool(item.pdf_url),
        bool(item.authors), bool(item.journal),
    ]) / 5
    score += completeness * 0.1

    return score


def rank(items: list[ResearchItem], query: str = "", mode: str = "search") -> list[ResearchItem]:
    return sorted(items, key=lambda x: _score(x, query, mode), reverse=True)


# ── Public aggregator interface ───────────────────────────────────────────────

async def search(
    query: str,
    page: int = 1,
    per_page: int = 10,
    sources: Optional[list[str]] = None,
    filters: Optional[dict[str, Any]] = None,
) -> list[ResearchItem]:
    """
    Search concurrently across enabled providers.

    Default sources: ["openalex", "arxiv"]
    Optional opt-in: add "semantic_scholar" to sources for SS results too.
    Crossref is intentionally excluded from primary search (DOI enrichment only).
    """
    enabled = sources or ["openalex", "arxiv"]

    tasks = []
    if "openalex" in enabled:
        tasks.append(_oa.search(query, page=page, per_page=per_page, filters=filters))
    if "arxiv" in enabled:
        tasks.append(_ax.search(query, page=page, per_page=per_page, filters=filters))
    if "semantic_scholar" in enabled:
        tasks.append(_ss.search(query, page=page, per_page=per_page, filters=filters))
    # Crossref is intentionally excluded from primary search

    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_items: list[ResearchItem] = []
    for r in results:
        if isinstance(r, Exception):
            logger.warning("Provider error during search: %s", r)
            continue
        all_items.extend(r)

    return rank(deduplicate(all_items), query, mode="search")[:per_page]


async def latest(
    query: str = "quantum computing",
    per_page: int = 10,
) -> list[ResearchItem]:
    """Return most recent papers from OpenAlex + arXiv."""
    tasks = [
        _oa.search(query, page=1, per_page=per_page),
        _ax.search(query, page=1, per_page=per_page),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    all_items: list[ResearchItem] = []
    for r in results:
        if not isinstance(r, Exception):
            all_items.extend(r)
    return rank(deduplicate(all_items), query, mode="latest")[:per_page]


async def get_by_id(item_id: str) -> Optional[ResearchItem]:
    """
    Fetch a specific paper.  item_id format: "<source>:<id>"
    e.g. "openalex:W1234", "arxiv:2504.02455", "doi:10.1234/xyz"

    For DOI lookups we try Crossref which has the richest metadata.
    """
    if not item_id or ":" not in item_id:
        return None
    source, ext_id = item_id.split(":", 1)

    if source == "openalex":
        item = await _oa.get_by_id(ext_id)
    elif source == "arxiv":
        item = await _ax.get_by_id(ext_id)
    elif source in ("doi", "crossref"):
        item = await _cr.get_by_id(ext_id)
    elif source == "semantic_scholar":
        item = await _ss.get_by_id(ext_id)
    else:
        # Unknown source — try OpenAlex first, then arXiv
        item = await _oa.get_by_id(ext_id)
        if item is None:
            item = await _ax.get_by_id(ext_id)

    # Enrich with Crossref DOI metadata if we have a DOI and no journal yet
    if item and item.doi and not item.journal:
        cr_item = await _cr.get_by_id(item.doi)
        if cr_item:
            item = _merge(item, cr_item)

    return item


async def get_related(item_id: str, limit: int = 5) -> list[ResearchItem]:
    """
    Return related papers.

    Strategy:
      1. Try Semantic Scholar Recommendations API (unauthenticated free tier).
         Works best when we can extract a DOI or arXiv ID from item_id.
      2. Fall back to OpenAlex concept-similarity if SS returns nothing.
    """
    if not item_id or ":" not in item_id:
        return []
    source, ext_id = item_id.split(":", 1)

    # Build the best lookup key for Semantic Scholar
    ss_key: Optional[str] = None
    if source == "arxiv":
        ss_key = ext_id          # plain arXiv ID — SS auto-prefixes ARXIV:
    elif source in ("doi", "crossref"):
        ss_key = ext_id          # plain DOI — SS auto-prefixes DOI:
    elif source == "semantic_scholar":
        ss_key = ext_id          # native SS paperId

    # 1. Try Semantic Scholar recommendations
    if ss_key:
        try:
            ss_results = await _ss.get_related(ss_key, limit=limit)
            if ss_results:
                return ss_results
        except Exception as exc:
            logger.warning("SS get_related failed (%s), falling back to OpenAlex: %s", ss_key, exc)

    # 2. Fall back to OpenAlex concept-similarity
    oa_id = ext_id if source == "openalex" else ext_id
    return await _oa.get_related(oa_id, limit=limit)


async def get_citations(item_id: str, limit: int = 20) -> list[ResearchItem]:
    """
    Return papers that cite the given item.

    Strategy:
      1. Try Semantic Scholar citations API (unauthenticated free tier).
         Works best for papers indexed by SS (most peer-reviewed + arXiv).
      2. Fall back to OpenAlex cited-by filter if SS returns nothing.
    """
    if not item_id or ":" not in item_id:
        return []
    source, ext_id = item_id.split(":", 1)

    # Build SS lookup key
    ss_key: Optional[str] = None
    if source == "arxiv":
        ss_key = ext_id
    elif source in ("doi", "crossref"):
        ss_key = ext_id
    elif source == "semantic_scholar":
        ss_key = ext_id

    # 1. Try Semantic Scholar
    if ss_key:
        try:
            ss_results = await _ss.get_citations(ss_key, limit=limit)
            if ss_results:
                return ss_results
        except Exception as exc:
            logger.warning("SS get_citations failed (%s), falling back to OpenAlex: %s", ss_key, exc)

    # 2. Fall back to OpenAlex cited-by filter
    return await _oa.get_citations(ext_id, limit=limit)

