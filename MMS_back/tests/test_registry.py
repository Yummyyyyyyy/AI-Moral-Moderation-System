"""Guard the registry's policy invariants."""

from __future__ import annotations

from app.responder.registry import REGISTRY
from app.schemas.classification import HarmType


def test_every_harm_type_except_other_is_registered():
    """Every harm type the classifier can emit (except OTHER) needs a spec."""
    for ht in HarmType:
        if ht == HarmType.OTHER:
            continue
        assert ht in REGISTRY, f"missing responder for {ht}"


def test_counseling_types_open_sessions():
    """Depressive / self-harm types must spawn multi-turn sessions."""
    assert REGISTRY[HarmType.DEPRESSIVE].opens_session is True
    assert REGISTRY[HarmType.SELF_HARM].opens_session is True


def test_self_harm_requires_moderation_and_crisis_block():
    """Self-harm replies must be reviewed and include crisis resources."""
    spec = REGISTRY[HarmType.SELF_HARM]
    assert spec.require_moderation is True
    assert spec.attach_crisis_resources is True
