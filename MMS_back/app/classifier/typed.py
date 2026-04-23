"""Team Member B's multi-class harm-type classifier hook-in point."""

from __future__ import annotations

from app.schemas.classification import HarmType, TypeLabel
from app.schemas.post import Post


class TeamTypedClassifier:
    """Stub that matches the Protocol; Member B will fill in real inference."""

    version = "team-typed-v0"

    def __init__(self) -> None:
        """Load model weights / label mapping here."""
        # TODO(member-B): load model.
        pass

    def categorize(self, post: Post) -> TypeLabel:
        """Return a TypeLabel. Currently returns OTHER as a safe default."""
        # TODO(member-B): replace with real inference.
        return TypeLabel(
            harm_type=HarmType.OTHER,
            score=0.0,
            strategy_hint=None,
            model_version=self.version,
        )
