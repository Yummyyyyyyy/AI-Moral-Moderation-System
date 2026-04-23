"""Counseling-session persistence: sessions + turns."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from app.llm.base import ChatMessage
from app.schemas.session import Session, SessionStatus, Turn, TurnRole
from app.store.db import connect


def create(post_id: str, user_id: str) -> Session:
    """Open a new counseling session and return it."""
    sess = Session(id=str(uuid4()), post_id=post_id, user_id=user_id)
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO sessions (id, post_id, user_id, status, opened_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sess.id, sess.post_id, sess.user_id, sess.status.value, sess.opened_at.isoformat()),
        )
    return sess


def get(session_id: str) -> Session | None:
    """Fetch a session by id."""
    with connect() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    return _from_row(row) if row else None


def find_by_post(post_id: str) -> Session | None:
    """Return the active session for a post, if any."""
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE post_id = ? ORDER BY opened_at DESC LIMIT 1",
            (post_id,),
        ).fetchone()
    return _from_row(row) if row else None


def set_status(session_id: str, status: SessionStatus) -> None:
    """Transition a session's status."""
    with connect() as conn:
        conn.execute("UPDATE sessions SET status = ? WHERE id = ?", (status.value, session_id))


def append_turn(session_id: str, role: TurnRole, text: str) -> Turn:
    """Append and return a new turn."""
    turn = Turn(id=str(uuid4()), session_id=session_id, role=role, text=text)
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO turns (id, session_id, role, text, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (turn.id, turn.session_id, turn.role.value, turn.text, turn.created_at.isoformat()),
        )
    return turn


def list_turns(session_id: str) -> list[Turn]:
    """Return turns in chronological order."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM turns WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,),
        ).fetchall()
    return [
        Turn(
            id=r["id"],
            session_id=r["session_id"],
            role=TurnRole(r["role"]),
            text=r["text"],
            created_at=datetime.fromisoformat(r["created_at"]),
        )
        for r in rows
    ]


def history_as_chat(session_id: str) -> list[ChatMessage]:
    """Render turns as LLM chat history (bot → assistant, user → user)."""
    mapping = {TurnRole.USER: "user", TurnRole.BOT: "assistant", TurnRole.SYSTEM: "system"}
    return [
        ChatMessage(role=mapping[t.role], content=t.text)  # type: ignore[arg-type]
        for t in list_turns(session_id)
    ]


def _from_row(row) -> Session:
    """Map a sqlite row to a Session."""
    return Session(
        id=row["id"],
        post_id=row["post_id"],
        user_id=row["user_id"],
        status=SessionStatus(row["status"]),
        opened_at=datetime.fromisoformat(row["opened_at"]),
    )
