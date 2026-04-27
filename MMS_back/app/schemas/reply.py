"""Schemas for reply drafts produced by responders and their moderation lifecycle."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ReplyStatus(StrEnum):
    """Lifecycle of a reply draft."""

    PENDING_MOD = "pending_mod"
    AUTO_APPROVED = "auto_approved"
    PUBLISHED = "published"
    REJECTED = "rejected"
    EDITED = "edited"


class ReplyDraft(BaseModel):
    """A bot-generated reply awaiting (or having cleared) moderation."""

    id: str
    post_id: str
    text: str
    text_raw: str | None = None  # responder draft before polisher; None == not polished
    status: ReplyStatus
    rag_doc_ids: list[str] = Field(default_factory=list)
    prompt_key: str
    llm_model: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ModeratorAction(StrEnum):
    """Actions the human reviewer can take on a draft."""

    APPROVE = "approve"
    REJECT = "reject"
    EDIT = "edit"
    POLISH = "polish"
    ESCALATE = "escalate"


class ModeratorDecision(BaseModel):
    """Audit record for a moderator's action on a draft."""

    reply_id: str
    moderator_id: str
    action: ModeratorAction
    before_text: str
    after_text: str | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
