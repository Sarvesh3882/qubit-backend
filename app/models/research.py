"""
Research Intelligence models.

Two lightweight cache tables:
  - ResearchItem  — normalized paper/preprint from any provider
  - NewsItem      — normalized news article from GNews

These serve as the cache layer.  External provider data is normalized and
stored here.  The cache is TTL-based — stale rows are simply overwritten
on the next fetch.
"""
from __future__ import annotations
from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


class ResearchItem(SQLModel, table=True):
    __tablename__ = "research_items"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Stable composite key: source + external_id
    source: str = Field(index=True)              # "openalex" | "arxiv" | "semantic_scholar" | "crossref"
    external_id: str = Field(index=True)         # source-native ID

    # De-duplication keys (nullable — not all sources have all three)
    doi: Optional[str] = Field(default=None, index=True)
    arxiv_id: Optional[str] = Field(default=None, index=True)

    # Core content
    title: str
    abstract: Optional[str] = None
    # JSON-encoded lists stored as TEXT (SQLite) — authors, topics, categories
    authors_json:    str = Field(default="[]")   # [{name, id?, affiliation?}]
    topics_json:     str = Field(default="[]")   # ["quantum error correction", ...]
    categories_json: str = Field(default="[]")   # ["cs.QI", "quant-ph", ...]

    # Publication metadata
    publication_date: Optional[str] = None       # ISO date string YYYY-MM-DD
    updated_date:     Optional[str] = None
    journal:          Optional[str] = None
    publisher:        Optional[str] = None

    # Links
    url:     Optional[str] = None
    pdf_url: Optional[str] = None

    # Metrics
    citation_count: int = 0

    # Cache metadata
    cached_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    query_key: Optional[str] = Field(default=None, index=True)  # search query that produced this


class NewsItem(SQLModel, table=True):
    __tablename__ = "news_items"

    id: Optional[int] = Field(default=None, primary_key=True)

    source: str = Field(index=True)         # "gnews"
    external_id: str = Field(index=True)    # hash of URL

    title:       str
    description: Optional[str] = None
    content:     Optional[str] = None
    url:         str
    image_url:   Optional[str] = None
    publisher:   Optional[str] = None
    published_at: Optional[str] = None      # ISO datetime string
    topics_json: str = Field(default="[]")  # ["quantum computing", ...]

    cached_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    query_key: Optional[str] = Field(default=None, index=True)
