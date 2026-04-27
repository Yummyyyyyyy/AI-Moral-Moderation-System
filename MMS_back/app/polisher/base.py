"""Polisher protocol that Member D implements."""

from __future__ import annotations

from typing import Protocol


class Polisher(Protocol):
    """Rewrite a reply draft to be more polite/natural while preserving meaning."""

    version: str

    def polish(self, text: str) -> str:
        """Return a polished version of ``text``. Must never raise."""
        ...