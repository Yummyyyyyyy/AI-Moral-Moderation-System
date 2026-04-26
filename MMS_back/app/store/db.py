"""SQLite helpers: schema bootstrap + per-request connection.

Using stdlib ``sqlite3`` directly (no ORM) to keep the prototype dependency
footprint small. Every row in every table is a flat mapping we construct
manually in the per-table modules.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.config import settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    id          TEXT PRIMARY KEY,
    author_id   TEXT NOT NULL,
    author_name TEXT,
    text        TEXT NOT NULL,
    source      TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS classifications (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id         TEXT NOT NULL,
    stage           TEXT NOT NULL,          -- 'binary' | 'typed'
    is_harmful      INTEGER,                -- nullable for typed rows
    harm_type       TEXT,
    score           REAL NOT NULL,
    strategy_hint   TEXT,
    model_details   TEXT,
    model_version   TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    FOREIGN KEY (post_id) REFERENCES posts(id)
);

CREATE TABLE IF NOT EXISTS replies (
    id            TEXT PRIMARY KEY,
    post_id       TEXT NOT NULL,
    text          TEXT NOT NULL,
    status        TEXT NOT NULL,
    rag_doc_ids   TEXT NOT NULL,             -- JSON list of ids
    prompt_key    TEXT NOT NULL,
    llm_model     TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    FOREIGN KEY (post_id) REFERENCES posts(id)
);

CREATE TABLE IF NOT EXISTS moderator_decisions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    reply_id      TEXT NOT NULL,
    moderator_id  TEXT NOT NULL,
    action        TEXT NOT NULL,
    before_text   TEXT NOT NULL,
    after_text    TEXT,
    note          TEXT,
    created_at    TEXT NOT NULL,
    FOREIGN KEY (reply_id) REFERENCES replies(id)
);

CREATE TABLE IF NOT EXISTS sessions (
    id         TEXT PRIMARY KEY,
    post_id    TEXT NOT NULL,
    user_id    TEXT NOT NULL,
    status     TEXT NOT NULL,
    opened_at  TEXT NOT NULL,
    FOREIGN KEY (post_id) REFERENCES posts(id)
);

CREATE TABLE IF NOT EXISTS turns (
    id          TEXT PRIMARY KEY,
    session_id  TEXT NOT NULL,
    role        TEXT NOT NULL,              -- 'user' | 'bot' | 'system'
    text        TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_classifications_post ON classifications(post_id);
CREATE INDEX IF NOT EXISTS idx_replies_post ON replies(post_id);
CREATE INDEX IF NOT EXISTS idx_turns_session ON turns(session_id);
"""


def init_db() -> None:
    """Create tables if they don't exist. Call once at app startup."""
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(_SCHEMA)
        _ensure_column(conn, "classifications", "model_details", "TEXT")


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, column_type: str) -> None:
    """Add a missing column to an existing SQLite table."""
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    existing = {row["name"] for row in rows}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Yield a row-dict connection with foreign keys on, committing on success."""
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
