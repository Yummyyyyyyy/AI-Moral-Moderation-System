"""Persist classifier outputs so the moderator console can show label history."""

from __future__ import annotations

import json
from datetime import datetime

from app.schemas.classification import BinaryLabel, HarmType, TypeLabel
from app.store.db import connect


def record_binary(post_id: str, label: BinaryLabel) -> None:
    """Append a binary classification row."""
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO classifications
              (post_id, stage, is_harmful, harm_type, score, strategy_hint,
               model_details, model_version, created_at)
            VALUES (?, 'binary', ?, NULL, ?, NULL, NULL, ?, ?)
            """,
            (
                post_id,
                1 if label.is_harmful else 0,
                label.score,
                label.model_version,
                datetime.utcnow().isoformat(),
            ),
        )


def record_typed(post_id: str, label: TypeLabel) -> None:
    """Append a typed classification row."""
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO classifications
              (post_id, stage, is_harmful, harm_type, score, strategy_hint,
               model_details, model_version, created_at)
            VALUES (?, 'typed', NULL, ?, ?, ?, ?, ?, ?)
            """,
            (
                post_id,
                label.harm_type.value,
                label.score,
                label.strategy_hint,
                json.dumps(label.model_details, ensure_ascii=False) if label.model_details else None,
                label.model_version,
                datetime.utcnow().isoformat(),
            ),
        )


def history_for(post_id: str) -> list[dict]:
    """Return all classifier rows for a post, oldest first."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM classifications WHERE post_id = ? ORDER BY id ASC",
            (post_id,),
        ).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        raw_details = item.get("model_details")
        item["model_details"] = json.loads(raw_details) if raw_details else None
        items.append(item)
    return items


def latest_typed(post_id: str) -> TypeLabel | None:
    """Return the most recent typed classification for a post, if any."""
    with connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM classifications
            WHERE post_id = ? AND stage = 'typed'
            ORDER BY id DESC LIMIT 1
            """,
            (post_id,),
        ).fetchone()
    if row is None:
        return None
    return TypeLabel(
        harm_type=HarmType(row["harm_type"]),
        score=row["score"],
        strategy_hint=row["strategy_hint"],
        model_details=json.loads(row["model_details"]) if row["model_details"] else None,
        model_version=row["model_version"],
    )
