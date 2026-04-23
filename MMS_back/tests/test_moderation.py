"""Cover the moderator queue + decision audit."""

from __future__ import annotations

import importlib

from app.schemas.post import Author, Post
from app.schemas.reply import ModeratorAction


def _ingest(text: str):
    """Run the pipeline for a fresh post."""
    import app.pipeline as pipeline_mod
    importlib.reload(pipeline_mod)
    post = Post(id=f"mod-{abs(hash(text))}", author=Author(user_id="mod-tester"), text=text)
    return pipeline_mod.process_post(post)


def test_queue_and_approve(fresh_db):
    """A pending draft shows up in the queue; approve publishes it."""
    from app.store import replies as replies_store
    from app.store import audit as audit_store
    from app.schemas.reply import ReplyStatus, ModeratorDecision

    out = _ingest("Everyone in that group is an idiot, shut up.")
    assert out.reply is not None
    pending = replies_store.list_pending()
    assert any(r.id == out.reply.id for r in pending)

    # simulate the API layer
    replies_store.update_status(out.reply.id, ReplyStatus.PUBLISHED, new_text=None)
    audit_store.record(
        ModeratorDecision(
            reply_id=out.reply.id,
            moderator_id="alice",
            action=ModeratorAction.APPROVE,
            before_text=out.reply.text,
        )
    )
    assert replies_store.get(out.reply.id).status == ReplyStatus.PUBLISHED
    assert audit_store.history_for(out.reply.id)
