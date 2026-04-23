"""Responder package: generates reply drafts given a classified post."""

from app.responder.base import Responder, ResponderContext, ResponderResult
from app.responder.registry import REGISTRY, ResponderSpec, spec_for

__all__ = [
    "Responder",
    "ResponderContext",
    "ResponderResult",
    "ResponderSpec",
    "REGISTRY",
    "spec_for",
]
