"""Pick a Polisher implementation based on settings."""

from __future__ import annotations

from app.config import settings
from app.polisher.base import Polisher


def get_polisher() -> Polisher:
    """Return the polisher chosen by ``MMS_POLISHER_IMPL``."""
    if settings.polisher_impl == "team":
        from app.polisher.team import TeamPolisher
        return TeamPolisher()
    from app.polisher.dummy import DummyPolisher
    return DummyPolisher()