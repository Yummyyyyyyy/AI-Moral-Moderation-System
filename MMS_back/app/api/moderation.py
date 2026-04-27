"""Moderator console endpoints.

  GET  /mod/queue                 → list pending drafts
  POST /mod/{reply_id}/decide     → approve / reject / edit / polish / escalate
  GET  /mod/{reply_id}/history    → audit history for a draft + its post's labels
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.polisher import get_polisher
from app.schemas.reply import ModeratorAction, ModeratorDecision, ReplyDraft, ReplyStatus
from app.store import audit as audit_store
from app.store import classifications as classifications_store
from app.store import replies as replies_store
from app.store import sessions as sessions_store
from app.schemas.session import SessionStatus

router = APIRouter(prefix="/mod", tags=["moderation"])


class DecideRequest(BaseModel):
    """Body for POST /mod/{reply_id}/decide."""

    moderator_id: str
    action: ModeratorAction
    edited_text: str | None = None
    note: str | None = None


class DecideResponse(BaseModel):
    """Result of a moderator decision."""

    reply: ReplyDraft
    decision: ModeratorDecision


class HistoryResponse(BaseModel):
    """Full audit trail plus classifier label history."""

    reply: ReplyDraft
    labels: list[dict]
    decisions: list[dict]


@router.get("/queue", response_model=list[ReplyDraft])
def list_queue() -> list[ReplyDraft]:
    """Return every draft currently awaiting moderator review."""
    return replies_store.list_pending()


@router.post("/{reply_id}/decide", response_model=DecideResponse)
def decide(reply_id: str, req: DecideRequest) -> DecideResponse:
    """Apply a moderator action to a reply and audit the transition."""
    draft = replies_store.get(reply_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="reply not found")

    before = draft.text
    after = req.edited_text

    if req.action == ModeratorAction.POLISH:
        after = get_polisher().polish(draft.text)

    status = {
        ModeratorAction.APPROVE: ReplyStatus.PUBLISHED,
        ModeratorAction.REJECT: ReplyStatus.REJECTED,
        ModeratorAction.EDIT: ReplyStatus.EDITED,
        ModeratorAction.POLISH: ReplyStatus.EDITED,
        ModeratorAction.ESCALATE: ReplyStatus.REJECTED,
    }[req.action]

    new_text = after if req.action in (ModeratorAction.EDIT, ModeratorAction.POLISH) else None
    replies_store.update_status(reply_id, status, new_text=new_text)

    if req.action == ModeratorAction.ESCALATE:
        existing = sessions_store.find_by_post(draft.post_id)
        if existing is None:
            sessions_store.create(post_id=draft.post_id, user_id="unknown")
        else:
            sessions_store.set_status(existing.id, SessionStatus.ESCALATED)

    decision = ModeratorDecision(
        reply_id=reply_id,
        moderator_id=req.moderator_id,
        action=req.action,
        before_text=before,
        after_text=after,
        note=req.note,
    )
    audit_store.record(decision)

    updated = replies_store.get(reply_id)
    assert updated is not None  # just wrote it
    return DecideResponse(reply=updated, decision=decision)


@router.get("/{reply_id}/history", response_model=HistoryResponse)
def history(reply_id: str) -> HistoryResponse:
    """Return the audit trail + classifier labels for this reply's post."""
    draft = replies_store.get(reply_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="reply not found")
    return HistoryResponse(
        reply=draft,
        labels=classifications_store.history_for(draft.post_id),
        decisions=audit_store.history_for(reply_id),
    )
