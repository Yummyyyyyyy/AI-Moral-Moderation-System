"""HarmType → Responder + policy mapping.

This is the single place to change if we want to:
  - route a harm type to a different responder,
  - toggle human moderation for a type,
  - open (or stop opening) a counseling session.

No LLM, no network IO — just a declarative dict the pipeline reads.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.responder.base import Responder
from app.responder.counsel import CounselResponder
from app.responder.persuade import PersuadeResponder
from app.schemas.classification import HarmType


@dataclass(frozen=True)
class ResponderSpec:
    """Declarative policy for one harm type."""

    responder: Responder
    use_rag: bool
    require_moderation: bool
    opens_session: bool
    attach_crisis_resources: bool = False


REGISTRY: dict[HarmType, ResponderSpec] = {
    HarmType.HATE: ResponderSpec(
        responder=PersuadeResponder("persuade/hate"),
        use_rag=True,
        require_moderation=True,
        opens_session=False,
    ),
    HarmType.CYBERBULLYING: ResponderSpec(
        responder=PersuadeResponder("persuade/cyberbullying"),
        use_rag=True,
        require_moderation=True,
        opens_session=False,
    ),
    HarmType.MISINFORMATION: ResponderSpec(
        responder=PersuadeResponder("persuade/misinfo"),
        use_rag=True,
        require_moderation=True,
        opens_session=False,
    ),
    HarmType.DEPRESSIVE: ResponderSpec(
        responder=CounselResponder("counsel/system"),
        use_rag=True,
        require_moderation=False,
        opens_session=True,
    ),
    HarmType.SELF_HARM: ResponderSpec(
        responder=CounselResponder("counsel/system", attach_crisis_resources=True),
        use_rag=True,
        require_moderation=True,
        opens_session=True,
        attach_crisis_resources=True,
    ),
}


def spec_for(harm_type: HarmType) -> ResponderSpec | None:
    """Return the policy for `harm_type`, or None if we don't handle it."""
    return REGISTRY.get(harm_type)
