"""Runtime configuration loaded from environment variables.

All components read from a single `Settings` instance created at import time so
that tests can monkey-patch `settings` before dependent modules use it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
REPO_DIR = BASE_DIR.parent
DATA_DIR = REPO_DIR / "data"
MODELS_DIR = REPO_DIR / "models"
PROMPTS_DIR = BASE_DIR / "prompts"


def model_dir(name: str) -> Path:
    """Resolve a per-module model artifact directory.

    Looks up ``MMS_<NAME>_DIR`` (uppercase) for an explicit override,
    otherwise falls back to ``MODELS_DIR / name``. Used by the binary /
    typed classifiers and the RAG retriever so artifact locations are
    declared in one place.
    """
    override = os.environ.get(f"MMS_{name.upper()}_DIR")
    return Path(override) if override else MODELS_DIR / name


@dataclass(frozen=True)
class Settings:
    """Typed container for every env-driven knob in the app."""

    db_path: str
    llm_provider: str              # "dummy" | "openai" | "local"
    llm_model: str
    openai_api_key: str | None
    local_llm_base_url: str        # e.g. http://localhost:11434/v1
    classifier_binary_impl: str    # "dummy" | "team"
    classifier_typed_impl: str     # "dummy" | "team"
    rag_impl: str                  # "dummy" | "team"
    polisher_impl: str             # "dummy" | "team"
    polisher_url: str              # explicit override; empty means fetch from Drive
    polisher_timeout: float        # seconds for both URL fetch and inference call
    auto_publish_on_empty_queue: bool


def load_settings() -> Settings:
    """Read environment variables and return a frozen Settings."""
    return Settings(
        db_path=os.getenv("MMS_DB_PATH", str(DATA_DIR / "mms.db")),
        llm_provider=os.getenv("MMS_LLM_PROVIDER", "dummy"),
        llm_model=os.getenv("MMS_LLM_MODEL", "gpt-4o-mini"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        local_llm_base_url=os.getenv("MMS_LOCAL_LLM_URL", "http://localhost:11434/v1"),
        classifier_binary_impl=os.getenv("MMS_C1_IMPL", "dummy"),
        classifier_typed_impl=os.getenv("MMS_C2_IMPL", "dummy"),
        rag_impl=os.getenv("MMS_RAG_IMPL", "dummy"),
        polisher_impl=os.getenv("MMS_POLISHER_IMPL", "dummy"),
        polisher_url=os.getenv("MMS_POLISHER_URL", ""),
        polisher_timeout=float(os.getenv("MMS_POLISHER_TIMEOUT", "15")),
        auto_publish_on_empty_queue=os.getenv("MMS_AUTO_PUBLISH", "0") == "1",
    )


settings = load_settings()