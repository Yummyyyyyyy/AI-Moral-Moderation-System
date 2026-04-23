"""Team Member C's RAG retriever hook-in point."""

from __future__ import annotations

from app.schemas.classification import HarmType
from app.schemas.rag import RetrievedDoc


class TeamRetriever:
    """Stub that matches the Protocol; Member C plugs in their real index here."""

    version = "team-rag-v0"

    def __init__(self) -> None:
        """Load the vector index / embedding model."""
        # TODO(member-C): load index.
        pass

    def retrieve(
        self,
        query: str,
        harm_type: HarmType,
        top_k: int = 4,
    ) -> list[RetrievedDoc]:
        """Return top-k most relevant snippets. Returns empty list in the stub."""
        # TODO(member-C): real retrieval.
        return []
