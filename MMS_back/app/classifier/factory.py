"""Picks between dummy and team implementations based on settings."""

from __future__ import annotations

from app.classifier.base import BinaryClassifier, TypedClassifier
from app.classifier.binary import TeamBinaryClassifier
from app.classifier.dummy import DummyBinaryClassifier, DummyTypedClassifier
from app.classifier.typed import TeamTypedClassifier
from app.config import settings


def get_binary_classifier() -> BinaryClassifier:
    """Return the stage-1 classifier chosen by ``MMS_C1_IMPL``."""
    if settings.classifier_binary_impl == "team":
        return TeamBinaryClassifier()
    return DummyBinaryClassifier()


def get_typed_classifier() -> TypedClassifier:
    """Return the stage-2 classifier chosen by ``MMS_C2_IMPL``."""
    if settings.classifier_typed_impl == "team":
        return TeamTypedClassifier()
    return DummyTypedClassifier()
