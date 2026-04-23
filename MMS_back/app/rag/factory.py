"""Pick a Retriever implementation."""

from __future__ import annotations

from app.config import settings
from app.rag.base import Retriever
from app.rag.dummy import DummyRetriever
from app.rag.retriever import TeamRetriever


def get_retriever() -> Retriever:
    """Return the retriever chosen by ``MMS_RAG_IMPL``."""
    if settings.rag_impl == "team":
        return TeamRetriever()
    return DummyRetriever()
