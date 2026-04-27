"""Pipeline orchestrator.

Owns the order of operations but not their implementations: it calls the
injected classifier / retriever / LLM clients returned by their factories.

Flow for a freshly ingested post:
    1. Persist the post.
    2. Run Classifier1 (binary). Persist the label.
    3. If not harmful: stop.
    4. Run Classifier2 (typed). Persist the label.
    5. Look up ResponderSpec for the harm type.
    6. If spec.use_rag: retrieve corpus snippets.
    7. Call the responder to generate a ReplyDraft.
    8. Persist the draft as PENDING_MOD or AUTO_APPROVED per spec.
    9. If spec.opens_session: open a counseling session.

Returns a PipelineOutcome so the API can tell the frontend what happened.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from app.classifier import get_binary_classifier, get_typed_classifier
from app.polisher import get_polisher
from app.rag import get_retriever
from app.responder import REGISTRY, spec_for
from app.responder.base import ResponderContext
from app.schemas.classification import BinaryLabel, TypeLabel
from app.schemas.post import Post
from app.schemas.reply import ReplyDraft, ReplyStatus
from app.schemas.session import Session
from app.store import classifications as classifications_store
from app.store import posts as posts_store
from app.store import replies as replies_store
from app.store import sessions as sessions_store


@dataclass
class PipelineOutcome:
    """Machine-readable summary of what the pipeline did for one post."""

    post_id: str
    binary_label: BinaryLabel
    type_label: TypeLabel | None = None
    reply: ReplyDraft | None = None
    session: Session | None = None
    notes: list[str] = field(default_factory=list)


def process_post(post: Post) -> PipelineOutcome:
    """Run the full pipeline for a single post and return its outcome."""
    posts_store.upsert(post)

    binary = get_binary_classifier().classify(post)
    classifications_store.record_binary(post.id, binary)

    outcome = PipelineOutcome(post_id=post.id, binary_label=binary)
    if not binary.is_harmful:
        outcome.notes.append("post-not-harmful")
        return outcome

    typed = get_typed_classifier().categorize(post)
    classifications_store.record_typed(post.id, typed)
    outcome.type_label = typed

    spec = spec_for(typed.harm_type)
    if spec is None:
        outcome.notes.append(f"no-responder-for-{typed.harm_type}")
        return outcome

    docs = []
    if spec.use_rag:
        docs = get_retriever().retrieve(
            query=post.text, harm_type=typed.harm_type, top_k=4
        )

    ctx = ResponderContext(
        post=post,
        binary_label=binary,
        type_label=typed,
        retrieved_docs=docs,
        history=[],
    )
    result = spec.responder.respond(ctx)
    polished = get_polisher().polish(result.text)

    status = ReplyStatus.PENDING_MOD if spec.require_moderation else ReplyStatus.AUTO_APPROVED
    draft = ReplyDraft(
        id=str(uuid4()),
        post_id=post.id,
        text=polished,
        text_raw=result.text,
        status=status,
        rag_doc_ids=[d.doc_id for d in docs],
        prompt_key=result.prompt_key,
        llm_model=result.llm_model,
    )
    replies_store.insert(draft)
    outcome.reply = draft

    if spec.opens_session:
        sess = sessions_store.create(post_id=post.id, user_id=post.author.user_id)
        # Seed the session with the bot's first message so chat UI shows it.
        sessions_store.append_turn(sess.id, role=_bot_role(), text=polished)
        outcome.session = sess

    return outcome


def registered_types() -> list[str]:
    """Expose registered harm types for debugging / health endpoints."""
    return [ht.value for ht in REGISTRY.keys()]


def _bot_role():
    """Local import to avoid cycles when this module is imported early."""
    from app.schemas.session import TurnRole
    return TurnRole.BOT
