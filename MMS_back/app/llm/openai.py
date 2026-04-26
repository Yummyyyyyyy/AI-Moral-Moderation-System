"""Anthropic Claude adapter.

Vendor SDK usage is isolated here so that no other file in the app imports
``anthropic`` directly.
"""

from __future__ import annotations

from app.config import settings
from app.llm.base import PromptBundle


def _render_context(prompt: PromptBundle) -> str:
    """Append retrieved snippets to the system prompt as a structured block."""
    if not prompt.retrieved_docs:
        return prompt.system
    refs = "\n".join(
        f"[{d.doc_id}] ({d.source}) {d.text}" for d in prompt.retrieved_docs
    )
    return f"{prompt.system}\n\nRetrieved references:\n{refs}"


class ClaudeClient:
    """Thin wrapper over the Anthropic Messages API."""

    def __init__(self) -> None:
        """Import the SDK lazily so the dependency isn't required for dummy mode."""
        import anthropic  # local import keeps import-time light

        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model_id = settings.llm_model

    def generate(self, prompt: PromptBundle) -> str:
        """Call the Messages API and return the assistant text."""
        messages = [
            {"role": m.role, "content": m.content}
            for m in prompt.history
            if m.role in ("user", "assistant")
        ]
        messages.append({"role": "user", "content": prompt.user})
        resp = self._client.messages.create(
            model=self.model_id,
            max_tokens=prompt.max_tokens,
            temperature=prompt.temperature,
            system=_render_context(prompt),
            messages=messages,
        )
        parts = [block.text for block in resp.content if getattr(block, "text", None)]
        return "".join(parts).strip()
