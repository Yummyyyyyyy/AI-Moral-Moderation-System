"""Counsel-path polisher bypass safety check.

The pipeline must skip the polisher whenever the responder spec opens a
counseling session (depressive / self-harm). The polisher has been
observed to drop crisis-hotline phone numbers and URLs, so the raw draft
must reach the user verbatim. ``text_raw is None`` is the on-disk
signature of that bypass (set by ``app/pipeline.py``).

The persuade-path test is the contrapositive: hate / cyberbullying /
misinfo replies must still be polished, with the original text stashed
in ``text_raw`` so the audit log can show the before/after.
"""

from __future__ import annotations

import importlib

from app.schemas.post import Author, Post


def _build_post(post_id: str, text: str) -> Post:
    """Build a Post with stable id for one bypass test."""
    return Post(id=post_id, author=Author(user_id="tester"), text=text)


def test_counsel_path_skips_polisher(fresh_db, monkeypatch):
    """Self-harm posts must skip the polisher entirely; text_raw stays None."""
    import app.pipeline as pipeline_mod
    importlib.reload(pipeline_mod)

    class _BoomPolisher:
        """Asserts if any counsel-path code accidentally calls .polish()."""

        version = "boom-polisher"

        def polish(self, text: str) -> str:
            """Fail the test if invoked."""
            raise AssertionError("polisher must not be called on counsel paths")

    monkeypatch.setattr(pipeline_mod, "get_polisher", lambda: _BoomPolisher())

    out = pipeline_mod.process_post(_build_post("counsel-1", "I want to kill myself tonight."))

    assert out.session is not None, "self-harm post should open a counseling session"
    assert out.reply is not None
    assert out.reply.text_raw is None, "counsel-path bypass must leave text_raw unset"


def test_persuade_path_invokes_polisher_and_stashes_raw(fresh_db, monkeypatch):
    """Hate posts must run through the polisher; raw draft is preserved for audit."""
    import app.pipeline as pipeline_mod
    importlib.reload(pipeline_mod)

    seen: list[str] = []

    class _RecordingPolisher:
        """Records every call so we can assert the polisher actually ran."""

        version = "recording-polisher"

        def polish(self, text: str) -> str:
            """Tag the input so the test can distinguish polished vs raw."""
            seen.append(text)
            return f"[POLISHED] {text}"

    monkeypatch.setattr(pipeline_mod, "get_polisher", lambda: _RecordingPolisher())

    out = pipeline_mod.process_post(
        _build_post("hate-1", "Everyone in that group is an idiot, shut up.")
    )

    assert out.session is None, "hate post should not open a counseling session"
    assert out.reply is not None
    assert seen, "polisher should be called on persuade paths"
    assert out.reply.text_raw == seen[0], "raw responder draft must be stashed"
    assert out.reply.text == f"[POLISHED] {seen[0]}", "saved text must be the polished output"