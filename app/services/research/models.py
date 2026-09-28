"""
Internal normalized models for Research + News.

These are Pydantic models used within the service layer and returned
by the API.  They are separate from the SQLModel ORM models in
app/models/research.py which are used for caching.
"""
from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel


class Author(BaseModel):
    name: str
    id: Optional[str] = None
    affiliation: Optional[str] = None


class ResearchItem(BaseModel):
    """Normalized research paper from any provider."""
    id: str                        # "openalex:W1234", "arxiv:2504.02455", etc.
    source: str                    # primary source
    external_id: str               # source-native ID
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    title: str
    abstract: Optional[str] = None
    authors: list[Author] = []
    publication_date: Optional[str] = None   # YYYY-MM-DD
    updated_date: Optional[str] = None
    journal: Optional[str] = None
    publisher: Optional[str] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    citation_count: int = 0
    topics: list[str] = []
    categories: list[str] = []
    # Merged source identifiers when deduplicated
    source_ids: dict[str, str] = {}
    # Extra enrichment from secondary providers
    metadata: dict[str, Any] = {}


class NewsItem(BaseModel):
    """Normalized news article."""
    id: str                        # "gnews:<url_hash>"
    source: str
    external_id: str
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    url: str
    image_url: Optional[str] = None
    publisher: Optional[str] = None
    published_at: Optional[str] = None   # ISO datetime
    topics: list[str] = []
