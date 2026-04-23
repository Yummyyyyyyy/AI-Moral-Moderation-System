"""POST /admin/reset — wipe all tables and reseed the demo corpus.

Used by the frontend "Reset demo" button so contributors can explore freely
without leaving stray state in the database.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from app.pipeline import process_post
from app.schemas.post import Post
from app.store.db import connect

router = APIRouter(prefix="/admin", tags=["admin"])

_SEED_PATH = Path(__file__).resolve().parents[2] / "data" / "mock_posts.jsonl"

_TABLES = [
    "turns",
    "sessions",
    "moderator_decisions",
    "replies",
    "classifications",
    "posts",
]


class ResetResponse(BaseModel):
    wiped_tables: list[str]
    reseeded: int


@router.post("/reset", response_model=ResetResponse)
def reset() -> ResetResponse:
    """Truncate every table, then re-run the pipeline on the mock corpus."""
    with connect() as conn:
        for t in _TABLES:
            conn.execute(f"DELETE FROM {t}")

    count = 0
    if _SEED_PATH.exists():
        for line in _SEED_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            process_post(Post.model_validate(payload))
            count += 1

    return ResetResponse(wiped_tables=_TABLES, reseeded=count)
