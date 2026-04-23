"""Prompt YAML loader.

Business code calls ``load_prompt("persuade/hate")`` and gets back the raw
system + user templates. No code path ever hardcodes prompt text.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel

from app.config import PROMPTS_DIR


class PromptTemplate(BaseModel):
    """One prompt's system + user templates, keyed on variable names."""

    key: str
    system: str
    user: str
    variables: list[str] = []


@lru_cache(maxsize=64)
def load_prompt(key: str) -> PromptTemplate:
    """Load a prompt by slash-separated key, e.g. ``"persuade/hate"``.

    Files live at ``app/prompts/<key>.yaml``.
    """
    path = Path(PROMPTS_DIR, *key.split("/")).with_suffix(".yaml")
    if not path.exists():
        raise FileNotFoundError(f"prompt not found: {key} (expected at {path})")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return PromptTemplate(key=key, **data)


def render(template: str, **variables: str) -> str:
    """Minimal ``{name}`` substitution; missing vars raise KeyError."""
    return template.format(**variables)
