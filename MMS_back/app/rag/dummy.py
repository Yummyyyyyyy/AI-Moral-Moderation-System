"""In-memory retriever that serves canned snippets by harm type.

Enough to exercise the pipeline and visualize "which RAG doc was used?" in
the moderator console before Member C ships a real vector index.
"""

from __future__ import annotations

from app.schemas.classification import HarmType
from app.schemas.rag import RetrievedDoc

_CORPUS: dict[HarmType, list[RetrievedDoc]] = {
    HarmType.HATE: [
        RetrievedDoc(
            doc_id="hate-001",
            text="Studies of online civility show that calm, specific responses reduce escalation more than counter-insults.",
            source="dummy/hate.md",
            score=0.8,
        ),
    ],
    HarmType.CYBERBULLYING: [
        RetrievedDoc(
            doc_id="bully-001",
            text="Bystander support messages have been linked to reduced victim distress in cyberbullying research.",
            source="dummy/bullying.md",
            score=0.75,
        ),
    ],
    HarmType.MISINFORMATION: [
        RetrievedDoc(
            doc_id="misinfo-001",
            text="Corrections are most effective when paired with the reason the original claim is misleading, not mockery.",
            source="dummy/misinfo.md",
            score=0.7,
        ),
    ],
    HarmType.DEPRESSIVE: [
        RetrievedDoc(
            doc_id="depr-001",
            text="Active listening phrases ('that sounds really heavy', 'I hear you') build rapport before suggesting any action.",
            source="dummy/depressive.md",
            score=0.8,
        ),
    ],
    HarmType.SELF_HARM: [
        RetrievedDoc(
            doc_id="crisis-001",
            text="If you are in immediate danger, please contact a local crisis line. In the US: 988. In China: 010-82951332.",
            source="dummy/crisis.md",
            score=0.95,
        ),
    ],
    HarmType.OTHER: [],
}


class DummyRetriever:
    """Return the canned corpus entry for the given harm type."""

    version = "dummy-rag-v0"

    def retrieve(
        self,
        query: str,
        harm_type: HarmType,
        top_k: int = 4,
    ) -> list[RetrievedDoc]:
        """Ignore `query`, return all prefab docs for `harm_type` up to `top_k`."""
        return _CORPUS.get(harm_type, [])[:top_k]
