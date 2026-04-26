# app/llm/openai.py
from __future__ import annotations

from app.config import settings
from app.llm.base import PromptBundle


def _render_context(prompt: PromptBundle) -> str:
    """Append retrieved snippets to the system prompt."""
    if not prompt.retrieved_docs:
        return prompt.system
    refs = "\n".join(
        f"[{d.doc_id}] ({d.source}) {d.text}" for d in prompt.retrieved_docs
    )
    return f"{prompt.system}\n\nRetrieved references:\n{refs}"


class OpenAIClient:
    """Thin wrapper over the OpenAI Chat Completions API."""

    def __init__(self) -> None:
        import openai

        api_key = settings.openai_api_key
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self._client = openai.OpenAI(api_key=api_key)
        self.model_id = settings.llm_model

    def generate(self, prompt: PromptBundle) -> str:
        """Call Chat Completions and return the assistant text."""
        messages = [{"role": "system", "content": _render_context(prompt)}]
        for m in prompt.history:
            if m.role in ("user", "assistant"):
                messages.append({"role": m.role, "content": m.content})
        messages.append({"role": "user", "content": prompt.user})

        resp = self._client.chat.completions.create(
            model=self.model_id,
            max_tokens=prompt.max_tokens,
            temperature=prompt.temperature,
            messages=messages,
        )
        return resp.choices[0].message.content.strip()