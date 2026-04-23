"""Offline LLM stand-in.

Produces a natural-sounding canned reply based on which prompt template the
responder passed in. The picker looks at keywords inside ``prompt.system``
so the dummy stays decoupled from HarmType while still matching the right
tone per category. Swap ``MMS_LLM_PROVIDER=claude`` (or ``local``) to use a
real model.
"""

from __future__ import annotations

import random
from typing import Callable

from app.llm.base import PromptBundle

_HATE_REPLIES = [
    "Sounds like something really got under your skin. Would you be open to rephrasing this without aiming it at a whole group? A specific frustration usually lands better than a sweeping judgment.",
    "It's clear you're fed up, and that's fair — but calling out a whole group tends to shut the conversation down. What would it look like to name the actual behavior that bothered you?",
    "Strong feelings, for sure. One thing worth trying: swap the labels for what actually happened. That usually invites a reply instead of a fight.",
]

_BULLY_REPLIES = [
    "Reading this back, it's aimed pretty squarely at one person. Is there a way to say what's bothering you about the situation without going at them personally?",
    "It sounds like something frustrated you in that game or group. Venting here is fine, but this phrasing could really hurt — want to try putting it another way?",
    "I hear the frustration. Pile-ons tend to stick with people for a long time though. Could you say what went wrong without telling them to quit?",
]

_MISINFO_REPLIES = [
    "Just a heads up — the claim about microchips in vaccines has been reviewed by regulators and independent labs and there's no evidence for it. If you're curious about what's actually in a vaccine, the WHO has a plain-language breakdown.",
    "I get the instinct to share this, but this specific claim has been investigated and debunked repeatedly. Happy to point you to primary sources if you want to dig deeper.",
    "This one's circulated a lot but doesn't hold up to the evidence. If something in the rollout felt off to you, that's worth talking about — just not through this claim.",
]

_COUNSEL_OPENERS = [
    "That sounds really heavy, and I'm glad you said it out loud. You don't have to carry the whole thing at once — what's weighing on you the most right now?",
    "Thank you for writing this. What you're describing sounds exhausting. Can I ask what today has looked like for you?",
    "I hear you. Feeling invisible like that is brutal, and it's not a sign something is wrong with you. Is there one part of this you'd want to start with?",
]

_COUNSEL_FOLLOWUPS = [
    "That makes sense. It's okay if the answer isn't tidy — can you tell me a little more about what that's been like day to day?",
    "Thank you for sharing that. It sounds like a lot has been stacking up. Is there someone in your life who knows any of this, or has it mostly stayed with you?",
    "I'm still here. What you're feeling isn't small, and you don't have to resolve it in one conversation. What would feel like even a tiny bit of relief right now?",
    "That's a lot to sit with. If it helps, we can slow down — is there one thing from today that felt heaviest?",
]

_GENERIC_REPLIES = [
    "Thanks for sharing this. Is there something specific you'd like to talk through?",
]


def _pick(seed: str, options: list[str]) -> str:
    """Deterministic choice so the same prompt yields the same reply."""
    rnd = random.Random(seed)
    return rnd.choice(options)


class DummyLLMClient:
    """Return a category-appropriate canned reply."""

    model_id = "dummy-llm-v0"

    def generate(self, prompt: PromptBundle) -> str:
        """Pick a reply family from the system prompt, then a line from it."""
        system = prompt.system.lower()
        user = prompt.user or ""
        history = prompt.history

        picker: Callable[[list[str]], str] = lambda opts: _pick(user[:200], opts)

        if "hateful" in system:
            return picker(_HATE_REPLIES)
        if "cyberbullying" in system or "bullying" in system:
            return picker(_BULLY_REPLIES)
        if "misinformation" in system or "misinfo" in system:
            return picker(_MISINFO_REPLIES)
        if "depression" in system or "distress" in system or "counsel" in system:
            if history:
                seed = (history[-1].content if history else user)[:200]
                return _pick(seed, _COUNSEL_FOLLOWUPS)
            return picker(_COUNSEL_OPENERS)
        return picker(_GENERIC_REPLIES)
