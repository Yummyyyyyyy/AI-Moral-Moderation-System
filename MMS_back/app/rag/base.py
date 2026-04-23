"""Retriever protocol that Member C implements."""

from __future__ import annotations

from typing import Protocol

from app.schemas.classification import HarmType
from app.schemas.rag import RetrievedDoc


class Retriever(Protocol):
    """Return the top-k most relevant corpus snippets for a query."""

    def retrieve(
        self,
        query: str,
        harm_type: HarmType,
        top_k: int = 4,
    ) -> list[RetrievedDoc]:
        """Return up to `top_k` snippets filtered by `harm_type`."""
        ...
