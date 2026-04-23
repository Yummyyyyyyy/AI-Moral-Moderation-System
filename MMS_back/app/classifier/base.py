"""Protocols that team members A and B implement.

Keeping the interface tiny (one method each) lets real-model implementations
wrap whatever loaders / tokenizers / remote calls they need without leaking
into the rest of the pipeline.
"""

from __future__ import annotations

from typing import Protocol

from app.schemas.classification import BinaryLabel, TypeLabel
from app.schemas.post import Post


class BinaryClassifier(Protocol):
    """Stage-1 classifier: harmful or not."""

    def classify(self, post: Post) -> BinaryLabel:
        """Return a BinaryLabel for `post`."""
        ...


class TypedClassifier(Protocol):
    """Stage-2 classifier: pick a harm category.

    Only invoked when stage-1 decided the post is harmful.
    """

    def categorize(self, post: Post) -> TypeLabel:
        """Return a TypeLabel for `post`."""
        ...
