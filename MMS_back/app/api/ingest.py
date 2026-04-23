"""POST /ingest — accepts a Post and runs the pipeline on it."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.pipeline import process_post
from app.schemas.post import Post
from app.schemas.reply import ReplyDraft
from app.schemas.session import Session

router = APIRouter(prefix="/ingest", tags=["ingest"])


class IngestResponse(BaseModel):
    """Summary returned to the caller after ingestion."""

    post_id: str
    is_harmful: bool
    harm_type: str | None
    reply: ReplyDraft | None
    session: Session | None
    notes: list[str]


@router.post("", response_model=IngestResponse)
def ingest(post: Post) -> IngestResponse:
    """Run the pipeline synchronously and return a structured summary."""
    outcome = process_post(post)
    return IngestResponse(
        post_id=outcome.post_id,
        is_harmful=outcome.binary_label.is_harmful,
        harm_type=outcome.type_label.harm_type.value if outcome.type_label else None,
        reply=outcome.reply,
        session=outcome.session,
        notes=outcome.notes,
    )
