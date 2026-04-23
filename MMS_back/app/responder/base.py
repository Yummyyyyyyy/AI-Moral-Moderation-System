"""Responder protocol and the context/result schemas that flow through it."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field

from app.llm.base import ChatMessage
from app.schemas.classification import BinaryLabel, TypeLabel
from app.schemas.post import Post
from app.schemas.rag import RetrievedDoc


class ResponderContext(BaseModel):
    """Everything a responder needs to produce a reply.

    `history` is empty for single-shot persuade responders; counsel responders
    fill it from the session store.
    """

    post: Post
    binary_label: BinaryLabel
    type_label: TypeLabel
    retrieved_docs: list[RetrievedDoc] = Field(default_factory=list)
    history: list[ChatMessage] = Field(default_factory=list)
    latest_user_message: str | None = None   # for counsel turns after the first


class ResponderResult(BaseModel):
    """What a responder returns."""

    text: str
    prompt_key: str
    llm_model: str


class Responder(Protocol):
    """Interface that :class:`PersuadeResponder` and :class:`CounselResponder` satisfy."""

    def respond(self, ctx: ResponderContext) -> ResponderResult:
        """Produce a reply for `ctx`."""
        ...
