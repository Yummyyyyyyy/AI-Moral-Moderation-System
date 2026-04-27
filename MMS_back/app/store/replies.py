"""Persist reply drafts and their moderation state transitions."""

from __future__ import annotations

import json
from datetime import datetime

from app.schemas.reply import ReplyDraft, ReplyStatus
from app.store.db import connect


def insert(draft: ReplyDraft) -> None:
    """Insert a new reply draft row."""
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO replies
              (id, post_id, text, text_raw, status, rag_doc_ids, prompt_key,
               llm_model, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                draft.id,
                draft.post_id,
                draft.text,
                draft.text_raw,
                draft.status.value,
                json.dumps(draft.rag_doc_ids),
                draft.prompt_key,
                draft.llm_model,
                draft.created_at.isoformat(),
            ),
        )


def update_status(reply_id: str, status: ReplyStatus, new_text: str | None = None) -> None:
    """Transition a reply's status, optionally overwriting its text (edited/approved)."""
    with connect() as conn:
        if new_text is not None:
            conn.execute(
                "UPDATE replies SET status = ?, text = ? WHERE id = ?",
                (status.value, new_text, reply_id),
            )
        else:
            conn.execute(
                "UPDATE replies SET status = ? WHERE id = ?",
                (status.value, reply_id),
            )


def get(reply_id: str) -> ReplyDraft | None:
    """Fetch a reply by id, or None."""
    with connect() as conn:
        row = conn.execute("SELECT * FROM replies WHERE id = ?", (reply_id,)).fetchone()
    return _from_row(row) if row else None


def list_pending() -> list[ReplyDraft]:
    """Return all drafts awaiting moderator review, oldest first."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM replies WHERE status = ? ORDER BY created_at ASC",
            (ReplyStatus.PENDING_MOD.value,),
        ).fetchall()
    return [_from_row(r) for r in rows]


def list_for_post(post_id: str) -> list[ReplyDraft]:
    """Return every reply tied to `post_id`."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM replies WHERE post_id = ? ORDER BY created_at ASC",
            (post_id,),
        ).fetchall()
    return [_from_row(r) for r in rows]


def list_published_for_post(post_id: str) -> list[ReplyDraft]:
    """Return replies visible in the feed (published, auto-approved, or edited)."""
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM replies
            WHERE post_id = ? AND status IN (?, ?, ?)
            ORDER BY created_at ASC
            """,
            (
                post_id,
                ReplyStatus.PUBLISHED.value,
                ReplyStatus.AUTO_APPROVED.value,
                ReplyStatus.EDITED.value,
            ),
        ).fetchall()
    return [_from_row(r) for r in rows]


def _from_row(row) -> ReplyDraft:
    """Map a sqlite row to a ReplyDraft."""
    return ReplyDraft(
        id=row["id"],
        post_id=row["post_id"],
        text=row["text"],
        text_raw=row["text_raw"] if "text_raw" in row.keys() else None,
        status=ReplyStatus(row["status"]),
        rag_doc_ids=json.loads(row["rag_doc_ids"]),
        prompt_key=row["prompt_key"],
        llm_model=row["llm_model"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )
