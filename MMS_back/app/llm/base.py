"""LLMClient protocol and the prompt payload every client accepts.

The contract is deliberately provider-agnostic so Member D's RLHF model
(exposed via an OpenAI-compatible server) drops in via ``local.py`` without
touching business code.
"""

from __future__ import annotations

from typing import Literal, Protocol

from pydantic import BaseModel, Field

from app.schemas.rag import RetrievedDoc


class ChatMessage(BaseModel):
    """A message inside a multi-turn exchange."""

    role: Literal["user", "assistant", "system"]
    content: str


class PromptBundle(BaseModel):
    """Everything an LLM call needs.

    `system` and `user` are already rendered (Jinja2 / f-string / ...) by the
    responder. `retrieved_docs` is attached so the llm client can decide how
    to inject them (system prefix vs tool-style), keeping that decision out
    of responder code.
    """

    system: str
    user: str
    history: list[ChatMessage] = Field(default_factory=list)
    retrieved_docs: list[RetrievedDoc] = Field(default_factory=list)
    max_tokens: int = 512
    temperature: float = 0.7


class LLMClient(Protocol):
    """Synchronous text-in / text-out interface."""

    model_id: str

    def generate(self, prompt: PromptBundle) -> str:
        """Return a single assistant reply."""
        ...
