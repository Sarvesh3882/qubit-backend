"""
Abstract base provider interface.

Every external provider must implement this interface.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional
from .models import ResearchItem


class BaseResearchProvider(ABC):
    """Common interface for all research data providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier, e.g. 'openalex'."""

    @abstractmethod
    async def search(
        self,
        query: str,
        page: int = 1,
        per_page: int = 10,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[ResearchItem]:
        """Search for papers matching a query."""

    @abstractmethod
    async def get_by_id(self, external_id: str) -> Optional[ResearchItem]:
        """Retrieve a specific paper by provider-native ID."""

    async def get_related(self, external_id: str, limit: int = 5) -> list[ResearchItem]:
        """Return related papers. Default: empty (not all providers support this)."""
        return []

    async def get_citations(self, external_id: str, limit: int = 20) -> list[ResearchItem]:
        """Return papers that cite this paper."""
        return []
