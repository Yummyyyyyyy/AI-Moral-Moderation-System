"""Chat endpoints for multi-turn counseling sessions.

  GET  /sessions/{id}             → session metadata
  GET  /sessions/{id}/messages    → full history (turns)
  POST /sessions/{id}/messages    → post a user turn, get back the bot's reply
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.classifier import get_binary_classifier, get_typed_classifier
from app.rag import get_retriever
from app.responder import spec_for
from app.responder.base import ResponderContext
from app.schemas.classification import BinaryLabel, HarmType, TypeLabel
from app.schemas.post import Author, Post
from app.schemas.session import Session, Turn, TurnRole
from app.store import classifications as classifications_store
from app.store import posts as posts_store
from app.store import sessions as sessions_store

router = APIRouter(prefix="/sessions", tags=["chat"])


class UserTurnRequest(BaseModel):
    """Body for POST /sessions/{id}/messages."""

    text: str


class ChatTurnResponse(BaseModel):
    """Returned after a user turn is processed."""

    user_turn: Turn
    bot_turn: Turn
    safety_trip: bool = False


@router.get("/{session_id}", response_model=Session)
def get_session(session_id: str) -> Session:
    """Return a session record by id."""
    sess = sessions_store.get(session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="session not found")
    return sess


@router.get("/{session_id}/messages", response_model=list[Turn])
def list_messages(session_id: str) -> list[Turn]:
    """Return chronological turns for a session."""
    sess = sessions_store.get(session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="session not found")
    return sessions_store.list_turns(session_id)


@router.post("/{session_id}/messages", response_model=ChatTurnResponse)
def post_message(session_id: str, req: UserTurnRequest) -> ChatTurnResponse:
    """Append the user's turn, run a counsel round, append the bot's turn."""
    sess = sessions_store.get(session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="session not found")

    user_turn = sessions_store.append_turn(session_id, role=TurnRole.USER, text=req.text)

    # Per-turn safety: re-run classifiers on the latest user message so a
    # conversation can escalate to SELF_HARM even if the triggering post wasn't.
    probe = Post(
        id=f"probe-{user_turn.id}",
        author=Author(user_id=sess.user_id),
        text=req.text,
    )
    binary = get_binary_classifier().classify(probe)
    typed = (
        get_typed_classifier().categorize(probe)
        if binary.is_harmful
        else TypeLabel(harm_type=HarmType.DEPRESSIVE, score=0.5)
    )
    # Classifier output on probe turns is not persisted (it isn't a real post)
    # but we keep the flag to drive routing here.

    # Pick the spec for the type on this turn so SELF_HARM escalates tone.
    spec = spec_for(typed.harm_type) or spec_for(HarmType.DEPRESSIVE)
    assert spec is not None  # DEPRESSIVE is always registered

    docs = get_retriever().retrieve(probe.text, typed.harm_type, top_k=3) if spec.use_rag else []

    original_post = posts_store.get(sess.post_id)
    if original_post is None:
        # Session outlived its post; construct a stand-in so context is still valid.
        original_post = Post(
            id=sess.post_id,
            author=Author(user_id=sess.user_id),
            text="(original post not found)",
        )

    ctx = ResponderContext(
        post=original_post,
        binary_label=binary if binary.is_harmful else BinaryLabel(is_harmful=True, score=0.5),
        type_label=typed,
        retrieved_docs=docs,
        history=sessions_store.history_as_chat(session_id)[:-1],  # exclude just-added user turn
        latest_user_message=req.text,
    )
    result = spec.responder.respond(ctx)
    bot_turn = sessions_store.append_turn(session_id, role=TurnRole.BOT, text=result.text)

    safety = typed.harm_type == HarmType.SELF_HARM
    return ChatTurnResponse(user_turn=user_turn, bot_turn=bot_turn, safety_trip=safety)


# Auxiliary endpoint: label a probe turn into classifications store if needed.
# Kept out to avoid polluting the main post's label history; moderator console
# pulls label history from classifications_store.history_for(post_id).
_ = classifications_store  # silence unused-import warnings in some linters
