"""Multi-turn counseling responder for depressive / self-harm posts.

The responder itself is stateless; session persistence lives in
:mod:`app.store.sessions`. The pipeline and chat API feed `history` into the
`ResponderContext` before each call.
"""

from __future__ import annotations

from app.llm import get_llm_client
from app.llm.base import PromptBundle
from app.prompts import load_prompt, render
from app.responder.base import ResponderContext, ResponderResult

_CRISIS_BLOCK = (
    "\n\n---\n"
    "If you are in immediate danger, please reach out now:\n"
    "• United States: 988 (Suicide & Crisis Lifeline)\n"
    "• China (Beijing Crisis Hotline): 010-82951332\n"
    "• International: https://findahelpline.com"
)


class CounselResponder:
    """Keeps the tone constant across turns by re-loading the same system prompt."""

    def __init__(self, prompt_key: str, attach_crisis_resources: bool = False) -> None:
        """Bind the template and decide whether every reply appends the crisis block."""
        self._prompt_key = prompt_key
        self._attach_crisis = attach_crisis_resources

    def respond(self, ctx: ResponderContext) -> ResponderResult:
        """Generate the next counseling reply, conditioned on prior turns."""
        template = load_prompt(self._prompt_key)
        # For first turn we substitute the original post; for follow-ups we
        # substitute the latest user message so the model sees the current utterance.
        latest = ctx.latest_user_message or ctx.post.text
        user = render(template.user, text=latest)
        llm = get_llm_client()
        bundle = PromptBundle(
            system=template.system,
            user=user,
            history=ctx.history,
            retrieved_docs=ctx.retrieved_docs,
        )
        text = llm.generate(bundle)
        if self._attach_crisis:
            text = text.rstrip() + _CRISIS_BLOCK
        return ResponderResult(
            text=text,
            prompt_key=self._prompt_key,
            llm_model=llm.model_id,
        )
