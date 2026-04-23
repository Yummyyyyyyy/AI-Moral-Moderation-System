"""GET /posts — feed view used by the frontend."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.schemas.post import Post
from app.schemas.reply import ReplyDraft
from app.store import classifications as classifications_store
from app.store import posts as posts_store
from app.store import replies as replies_store
from app.store import sessions as sessions_store

router = APIRouter(prefix="/posts", tags=["feed"])


class FeedItem(BaseModel):
    """A post bundled with its moderation labels and published replies."""

    post: Post
    labels: list[dict]
    replies: list[ReplyDraft]
    session_id: str | None = None


@router.get("", response_model=list[FeedItem])
def list_feed(limit: int = 50) -> list[FeedItem]:
    """Return the most recent `limit` posts along with label + reply state."""
    items = []
    for post in posts_store.list_recent(limit=limit):
        labels = classifications_store.history_for(post.id)
        replies = replies_store.list_published_for_post(post.id)
        sess = sessions_store.find_by_post(post.id)
        items.append(
            FeedItem(
                post=post,
                labels=labels,
                replies=replies,
                session_id=sess.id if sess else None,
            )
        )
    return items


@router.get("/{post_id}", response_model=FeedItem)
def get_post(post_id: str) -> FeedItem:
    """Return a single post with full label / reply / session state."""
    post = posts_store.get(post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="post not found")
    labels = classifications_store.history_for(post_id)
    replies = replies_store.list_for_post(post_id)
    sess = sessions_store.find_by_post(post_id)
    return FeedItem(
        post=post,
        labels=labels,
        replies=replies,
        session_id=sess.id if sess else None,
    )
