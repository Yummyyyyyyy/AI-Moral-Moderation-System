"""Offline polisher stand-in: returns the draft unchanged."""

from __future__ import annotations


class DummyPolisher:
    """No-op polisher used when MMS_POLISHER_IMPL is unset or 'dummy'."""

    version = "dummy-polisher-v0"

    def polish(self, text: str) -> str:
        """Return ``text`` verbatim."""
        return text