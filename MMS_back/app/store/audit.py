"""Append-only log of moderator decisions."""

from __future__ import annotations

from app.schemas.reply import ModeratorDecision
from app.store.db import connect


def record(decision: ModeratorDecision) -> None:
    """Append a ModeratorDecision row."""
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO moderator_decisions
              (reply_id, moderator_id, action, before_text, after_text, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decision.reply_id,
                decision.moderator_id,
                decision.action.value,
                decision.before_text,
                decision.after_text,
                decision.note,
                decision.created_at.isoformat(),
            ),
        )


def history_for(reply_id: str) -> list[dict]:
    """Return decisions on a reply, oldest first."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM moderator_decisions WHERE reply_id = ? ORDER BY id ASC",
            (reply_id,),
        ).fetchall()
    return [dict(r) for r in rows]
