"""Team Member A's binary classifier hook-in point.

This file is intentionally a thin wrapper: the integrator imports
``get_team_binary_classifier`` in :mod:`app.classifier.factory`. Member A
replaces the body of :class:`TeamBinaryClassifier` with their real model.
"""

from __future__ import annotations

from app.schemas.classification import BinaryLabel
from app.schemas.post import Post


class TeamBinaryClassifier:
    """Stub that matches the Protocol; Member A will fill in real inference."""

    version = "team-binary-v0"

    def __init__(self) -> None:
        """Load model weights / tokenizer here."""
        # TODO(member-A): load model.
        pass

    def classify(self, post: Post) -> BinaryLabel:
        """Return a BinaryLabel. Currently a conservative always-false stub."""
        # TODO(member-A): replace with real inference.
        return BinaryLabel(is_harmful=False, score=0.0, model_version=self.version)
