"""End-to-end smoke over the dummy pipeline covering each harm type."""

from __future__ import annotations

import importlib

from app.schemas.post import Author, Post


def _process(text: str):
    """Reload pipeline with current settings and process one post."""
    import app.pipeline as pipeline_mod
    importlib.reload(pipeline_mod)
    post = Post(id=f"t-{abs(hash(text))}", author=Author(user_id="tester"), text=text)
    return pipeline_mod.process_post(post)


def test_neutral_post_has_no_reply(fresh_db):
    """A benign post should not produce a reply or a session."""
    out = _process("Had a lovely day at the park today!")
    assert out.binary_label.is_harmful is False
    assert out.reply is None
    assert out.session is None


def test_hate_post_creates_pending_reply(fresh_db):
    """A hate post should create a pending_mod draft and no session."""
    out = _process("Everyone in that group is an idiot, shut up.")
    assert out.binary_label.is_harmful is True
    assert out.reply is not None
    assert out.reply.status.value == "pending_mod"
    assert out.session is None


def test_depressive_post_opens_session(fresh_db):
    """A depressive post should open a session and seed the first bot turn."""
    out = _process("I feel so hopeless and nobody cares.")
    assert out.reply is not None
    assert out.session is not None
    assert out.type_label is not None
    assert out.type_label.harm_type.value in ("depressive", "self_harm")


def test_self_harm_post_flagged_for_moderation(fresh_db):
    """Self-harm posts should open a session AND require moderation."""
    out = _process("I want to kill myself tonight.")
    assert out.reply is not None
    assert out.reply.status.value == "pending_mod"
    assert out.session is not None
