"""Schemas for classifier outputs.

Two stages:
    1. BinaryClassifier    -> BinaryLabel  (is this post harmful at all?)
    2. TypedClassifier     -> TypeLabel    (if yes, which harm category?)
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class HarmType(StrEnum):
    """Canonical harm categories the downstream responders understand."""

    HATE = "hate"
    CYBERBULLYING = "cyberbullying"
    MISINFORMATION = "misinformation"
    DEPRESSIVE = "depressive"
    SELF_HARM = "self_harm"
    OTHER = "other"


class BinaryLabel(BaseModel):
    """Output of the stage-1 classifier."""

    is_harmful: bool
    score: float = Field(ge=0.0, le=1.0)
    model_version: str = "dummy-v0"


class TypeLabel(BaseModel):
    """Output of the stage-2 classifier.

    `strategy_hint` lets Member B suggest a prompt template key (e.g.
    ``"persuade/hate_sarcastic"``) without the integrator having to guess.
    """

    harm_type: HarmType
    score: float = Field(ge=0.0, le=1.0)
    strategy_hint: str | None = None
    model_details: dict | None = None
    model_version: str = "dummy-v0"
