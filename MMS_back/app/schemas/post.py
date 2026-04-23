"""Schemas for inbound posts and their authors."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Author(BaseModel):
    """Minimum identity fields attached to a post."""

    user_id: str
    display_name: str | None = None


class Post(BaseModel):
    """A social-media post being ingested for moderation."""

    id: str
    author: Author
    text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    source: str = "mock"
