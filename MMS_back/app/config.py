"""Runtime configuration loaded from environment variables.

All components read from a single `Settings` instance created at import time so
that tests can monkey-patch `settings` before dependent modules use it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
REPO_DIR = BASE_DIR.parent
DATA_DIR = REPO_DIR / "data"
PROMPTS_DIR = BASE_DIR / "prompts"


@dataclass(frozen=True)
class Settings:
    """Typed container for every env-driven knob in the app."""

    db_path: str
    llm_provider: str              # "dummy" | "claude" | "local"
    llm_model: str
    #anthropic_api_key: str | None
    openai_api_key: str | None
    local_llm_base_url: str        # e.g. http://localhost:11434/v1
    classifier_binary_impl: str    # "dummy" | "team"
    classifier_typed_impl: str     # "dummy" | "team"
    rag_impl: str                  # "dummy" | "team"
    auto_publish_on_empty_queue: bool


def load_settings() -> Settings:
    """Read environment variables and return a frozen Settings."""
    return Settings(
        db_path=os.getenv("MMS_DB_PATH", str(DATA_DIR / "mms.db")),
        llm_provider=os.getenv("MMS_LLM_PROVIDER", "dummy"),
        llm_model=os.getenv("MMS_LLM_MODEL", "claude-sonnet-4-6"),
        #anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        local_llm_base_url=os.getenv("MMS_LOCAL_LLM_URL", "http://localhost:11434/v1"),
        classifier_binary_impl=os.getenv("MMS_C1_IMPL", "dummy"),
        classifier_typed_impl=os.getenv("MMS_C2_IMPL", "dummy"),
        rag_impl=os.getenv("MMS_RAG_IMPL", "dummy"),
        auto_publish_on_empty_queue=os.getenv("MMS_AUTO_PUBLISH", "0") == "1",
    )


settings = load_settings()
