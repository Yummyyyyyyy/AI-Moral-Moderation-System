"""Schemas for RAG retrieval results."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RetrievedDoc(BaseModel):
    """A single snippet returned by the retriever."""

    doc_id: str
    text: str
    source: str = "unknown"
    score: float = Field(ge=0.0, le=1.0, default=0.0)
