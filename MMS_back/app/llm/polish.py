"""RLHF-style polish pass.

Member D's RLHF-aligned model is a post-processor that takes a draft reply
and rewrites it to sound warmer, more conversational, and less "bot-y"
without changing the core meaning. This module defines the Protocol and
ships a dummy implementation so the moderator flow is demo-able before
the real model is plugged in. Swap ``get_polish_client`` to return a
real model (OpenAI-compatible endpoint) when Member D hands off.
"""

from __future__ import annotations

import random
import re
from typing import Protocol


class PolishClient(Protocol):
    """Takes a raw bot draft and returns a more human-sounding rewrite."""

    model_id: str

    def polish(self, draft: str) -> str:
        """Return a rewritten version. Must preserve meaning."""
        ...


_OPENERS = [
    "Hey — ",
    "Hey, ",
    "I hear you. ",
    "Thanks for posting this. ",
]

_SOFTEN = [
    (re.compile(r"\byou should\b", re.I), "it might help to"),
    (re.compile(r"\byou need to\b", re.I), "it could help to"),
    (re.compile(r"\bdo not\b", re.I), "try not to"),
    (re.compile(r"\bshut the conversation down\b", re.I), "make people defensive"),
    (re.compile(r"\bwrong\b", re.I), "off"),
]

_CLOSERS = [
    " Take care of yourself out there.",
    " Hope that lands okay.",
    " No pressure — just a thought.",
    " You've got more room to respond than it feels like.",
]


class DummyPolishClient:
    """Deterministic warm-up / soften pass. Stand-in until the RLHF model arrives."""

    model_id = "polish-dummy-v0"

    def polish(self, draft: str) -> str:
        """Prepend a warm opener, soften a few imperatives, append a closer."""
        rnd = random.Random(draft[:120])
        text = draft.strip()
        for pattern, replacement in _SOFTEN:
            text = pattern.sub(replacement, text)
        opener = rnd.choice(_OPENERS)
        closer = rnd.choice(_CLOSERS)
        if text and not text[0].isupper():
            text = text[0].upper() + text[1:]
        return f"{opener}{text}{closer}"


_client: PolishClient | None = None


def get_polish_client() -> PolishClient:
    """Singleton accessor so the moderation endpoint doesn't re-instantiate."""
    global _client
    if _client is None:
        _client = DummyPolishClient()
    return _client
