"""OpenAI-compatible local-model adapter (Ollama / vLLM / TGI / ...).

Member D's RLHF checkpoint just needs to expose an OpenAI ``/v1/chat/completions``
endpoint at ``settings.local_llm_base_url``; no other code in the app changes.
"""

from __future__ import annotations

import httpx

from app.config import settings
from app.llm.base import PromptBundle


class LocalLLMClient:
    """POST to an OpenAI-compatible chat completions endpoint."""

    def __init__(self) -> None:
        """Capture URL and model from settings."""
        self._url = settings.local_llm_base_url.rstrip("/") + "/chat/completions"
        self.model_id = settings.llm_model
        self._client = httpx.Client(timeout=60.0)

    def generate(self, prompt: PromptBundle) -> str:
        """POST the prompt and return the first choice's message content."""
        messages = [{"role": "system", "content": _render_system(prompt)}]
        messages.extend(
            {"role": m.role, "content": m.content}
            for m in prompt.history
            if m.role in ("user", "assistant", "system")
        )
        messages.append({"role": "user", "content": prompt.user})
        payload = {
            "model": self.model_id,
            "messages": messages,
            "temperature": prompt.temperature,
            "max_tokens": prompt.max_tokens,
        }
        resp = self._client.post(self._url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()


def _render_system(prompt: PromptBundle) -> str:
    """Inline retrieved docs into the system prompt."""
    if not prompt.retrieved_docs:
        return prompt.system
    refs = "\n".join(
        f"[{d.doc_id}] ({d.source}) {d.text}" for d in prompt.retrieved_docs
    )
    return f"{prompt.system}\n\nRetrieved references:\n{refs}"
