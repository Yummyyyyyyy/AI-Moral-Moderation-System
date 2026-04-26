"""Team Member C's RAG retriever hook-in point."""

from __future__ import annotations

import pickle

import faiss
from sentence_transformers import SentenceTransformer

from app.config import DATA_DIR
from app.schemas.classification import HarmType
from app.schemas.rag import RetrievedDoc

SIMILARITY_THRESHOLD = 0.55
INDEX_PATH = DATA_DIR / "index/faiss.index"
META_PATH = DATA_DIR / "index/meta.pkl"
KN_INDEX_PATH = DATA_DIR / "index/knowledge.faiss"
KN_META_PATH = DATA_DIR / "index/knowledge_meta.pkl"

HATE_SPEECH_FRAMEWORK = (
    "Research shows exclusionary language causes psychological harm including "
    "rejection, shame, and reduced belonging. Constructive counter-speech that "
    "appeals to shared humanity is more effective than direct confrontation."
)

class TeamRetriever:
    """FAISS-backed retriever. Currently only HATE harm type is supported.

    Other harm types fall back to an empty list so the responder degrades to
    the base prompt instead of receiving hate-speech framework text by
    mistake. Adding per-type case/framework data is a follow-up for Member C.
    """

    version = "team-rag-v1"

    def __init__(self) -> None:
        """Load case index and knowledge index."""
        self._model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
        self._index = faiss.read_index(str(INDEX_PATH))
        with META_PATH.open("rb") as f:
            self._meta = pickle.load(f)
        self._kn_index = faiss.read_index(str(KN_INDEX_PATH))
        with KN_META_PATH.open("rb") as f:
            self._kn_meta = pickle.load(f)

    def retrieve(self, query: str, harm_type: HarmType, top_k: int = 4) -> list[RetrievedDoc]:
        """High-similarity: return case docs. Low-similarity: return Wikipedia docs."""
        if harm_type != HarmType.HATE:
            return []
        emb = self._model.encode([query], normalize_embeddings=True).astype("float32")
        scores, indices = self._index.search(emb, 50)

        results, seen = [], set()
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            item = self._meta[idx]
            if item["query_text"] in seen:
                continue
            seen.add(item["query_text"])
            results.append((float(score), item))
            if len(results) >= top_k:
                break

        # 高相似度：返回案例库
        if results and results[0][0] >= SIMILARITY_THRESHOLD:
            return [
                RetrievedDoc(
                    doc_id=f"case-{i}",
                    text=(
                        f"Implication: {item.get('implication', '')} "
                        f"Emotional impact: {item.get('emotional_reaction', '')} "
                        f"Example response: {item['response_text']}"
                    ),
                    source="IntentCONANv2",
                    score=round(score, 4),
                )
                for i, (score, item) in enumerate(results)
            ]

        # 低相似度：固定框架 + Wikipedia top-1
        kn_query = f"{query} prejudice discrimination psychological impact belonging dignity"
        kn_emb = self._model.encode([kn_query], normalize_embeddings=True).astype("float32")
        kn_scores, kn_indices = self._kn_index.search(kn_emb, 10)

        docs = [RetrievedDoc(
            doc_id="framework-001",
            text=HATE_SPEECH_FRAMEWORK,
            source="research-framework",
            score=1.0,
        )]
        seen_titles = set()
        for score, idx in zip(kn_scores[0], kn_indices[0]):
            if idx < 0:
                continue
            item = self._kn_meta[idx]
            if item["title"] in seen_titles:
                continue
            seen_titles.add(item["title"])
            docs.append(RetrievedDoc(
                doc_id=f"wiki-{idx}",
                text=item["chunk"],
                source=item["title"],
                score=round(float(score), 4),
            ))
            break  # 只取1个

        return docs
