"""Schemas for multi-turn counseling sessions."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class SessionStatus(StrEnum):
    """Lifecycle of a counseling session."""

    ACTIVE = "active"
    CLOSED = "closed"
    ESCALATED = "escalated"


class TurnRole(StrEnum):
    """Speaker role inside a session turn."""

    USER = "user"
    BOT = "bot"
    SYSTEM = "system"


class Turn(BaseModel):
    """One exchange in a counseling session."""

    id: str
    session_id: str
    role: TurnRole
    text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Session(BaseModel):
    """A multi-turn counseling session tied to a triggering post."""

    id: str
    post_id: str
    user_id: str
    status: SessionStatus = SessionStatus.ACTIVE
    opened_at: datetime = Field(default_factory=datetime.utcnow)
