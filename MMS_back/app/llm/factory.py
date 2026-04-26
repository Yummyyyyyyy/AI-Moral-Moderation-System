"""Pick an LLMClient implementation based on settings."""

from __future__ import annotations

from app.config import settings
from app.llm.base import LLMClient


def get_llm_client() -> LLMClient:
    """Return the LLM client chosen by ``MMS_LLM_PROVIDER``.

    Imports are local so unused providers don't force their deps to load.
    """
    provider = settings.llm_provider
    if provider == "claude":
        from app.llm.claude import ClaudeClient
        return ClaudeClient()
    if provider == "local":
        from app.llm.local import LocalLLMClient
        return LocalLLMClient()
    if settings.llm_provider == "openai":  # 加这两行
        from app.llm.openai import OpenAIClient
        return OpenAIClient()
    from app.llm.dummy import DummyLLMClient
    return DummyLLMClient()
