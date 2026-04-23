"""Keyword-based dummy classifiers.

These exist so the whole pipeline can be demoed before Members A and B ship
their real models. Replace by swapping `MMS_C1_IMPL` / `MMS_C2_IMPL` to
``"team"`` and pointing `factory.py` at the real modules.
"""

from __future__ import annotations

from app.schemas.classification import BinaryLabel, HarmType, TypeLabel
from app.schemas.post import Post

_HARMFUL_HINTS = (
    "idiot", "stupid", "hate", "trash", "kill", "ugly",
    "loser", "die", "worthless", "shut up",
    "傻", "垃圾", "去死", "废物", "滚",
)

_DEPRESSIVE_HINTS = (
    "hopeless", "worthless", "nobody cares", "tired of everything",
    "can't go on", "no reason", "alone",
    "活不下去", "没意思", "没人在乎", "撑不住",
)

_SELF_HARM_HINTS = (
    "end it", "kill myself", "suicide", "cut myself",
    "自杀", "结束自己",
)

_MISINFO_HINTS = ("cure cancer overnight", "5g causes", "vaccine microchip", "flat earth")
_BULLY_HINTS = ("nobody likes you", "everyone hates you", "you should quit", "loser")


class DummyBinaryClassifier:
    """Flag posts that contain any harmful or depressive keyword."""

    version = "dummy-binary-v0"

    def classify(self, post: Post) -> BinaryLabel:
        """Return a harmful label if any hint matches; score is hit density."""
        text = post.text.lower()
        bags = (
            _HARMFUL_HINTS,
            _DEPRESSIVE_HINTS,
            _SELF_HARM_HINTS,
            _MISINFO_HINTS,
            _BULLY_HINTS,
        )
        hits = sum(1 for bag in bags for kw in bag if kw in text)
        is_harmful = hits > 0
        score = min(1.0, 0.4 + 0.2 * hits) if is_harmful else 0.05
        return BinaryLabel(is_harmful=is_harmful, score=score, model_version=self.version)


class DummyTypedClassifier:
    """Pick a harm type by first-match keyword priority.

    Priority order (roughly "most severe first") is deliberate so that
    ``kill myself`` does not get filed under generic hate.
    """

    version = "dummy-typed-v0"

    def categorize(self, post: Post) -> TypeLabel:
        """Return a TypeLabel, defaulting to HATE if nothing specific matches."""
        text = post.text.lower()
        if any(kw in text for kw in _SELF_HARM_HINTS):
            return TypeLabel(
                harm_type=HarmType.SELF_HARM,
                score=0.9,
                strategy_hint="counsel/system",
                model_version=self.version,
            )
        if any(kw in text for kw in _DEPRESSIVE_HINTS):
            return TypeLabel(
                harm_type=HarmType.DEPRESSIVE,
                score=0.8,
                strategy_hint="counsel/system",
                model_version=self.version,
            )
        if any(kw in text for kw in _MISINFO_HINTS):
            return TypeLabel(
                harm_type=HarmType.MISINFORMATION,
                score=0.7,
                strategy_hint="persuade/misinfo",
                model_version=self.version,
            )
        if any(kw in text for kw in _BULLY_HINTS):
            return TypeLabel(
                harm_type=HarmType.CYBERBULLYING,
                score=0.7,
                strategy_hint="persuade/cyberbullying",
                model_version=self.version,
            )
        if any(kw in text for kw in _HARMFUL_HINTS):
            return TypeLabel(
                harm_type=HarmType.HATE,
                score=0.7,
                strategy_hint="persuade/hate",
                model_version=self.version,
            )
        return TypeLabel(
            harm_type=HarmType.OTHER,
            score=0.3,
            strategy_hint=None,
            model_version=self.version,
        )
