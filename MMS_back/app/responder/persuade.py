"""Single-shot persuasion responder used for hate / misinfo / bullying."""

from __future__ import annotations

from app.llm import get_llm_client
from app.llm.base import PromptBundle
from app.prompts import load_prompt, render
from app.responder.base import ResponderContext, ResponderResult


class PersuadeResponder:
    """Render a prompt template, call the LLM, return the reply."""

    def __init__(self, prompt_key: str) -> None:
        """Bind this responder to a specific prompt template."""
        self._prompt_key = prompt_key

    def respond(self, ctx: ResponderContext) -> ResponderResult:
        """Load the template, substitute variables, and call the LLM."""
        template = load_prompt(self._prompt_key)
        user = render(
            template.user,
            author=ctx.post.author.display_name or ctx.post.author.user_id,
            text=ctx.post.text,
        )
        llm = get_llm_client()
        bundle = PromptBundle(
            system=template.system,
            user=user,
            retrieved_docs=ctx.retrieved_docs,
        )
        text = llm.generate(bundle)
        return ResponderResult(
            text=text,
            prompt_key=self._prompt_key,
            llm_model=llm.model_id,
        )
