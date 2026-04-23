"""CRUD helpers for posts."""

from __future__ import annotations

from datetime import datetime

from app.schemas.post import Author, Post
from app.store.db import connect


def upsert(post: Post) -> None:
    """Insert or replace a post row."""
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO posts (id, author_id, author_name, text, source, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                post.id,
                post.author.user_id,
                post.author.display_name,
                post.text,
                post.source,
                post.created_at.isoformat(),
            ),
        )


def get(post_id: str) -> Post | None:
    """Return a Post by id or None."""
    with connect() as conn:
        row = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    return _from_row(row) if row else None


def list_recent(limit: int = 50) -> list[Post]:
    """Return up to `limit` most recent posts, newest first."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM posts ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [_from_row(r) for r in rows]


def _from_row(row) -> Post:
    """Map a sqlite row to a Post."""
    return Post(
        id=row["id"],
        author=Author(user_id=row["author_id"], display_name=row["author_name"]),
        text=row["text"],
        source=row["source"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )
