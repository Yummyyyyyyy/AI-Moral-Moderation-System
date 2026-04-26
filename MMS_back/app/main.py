"""FastAPI app wiring."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, chat, feed, ingest, moderation
from app.config import settings
from app.pipeline import registered_types
from app.store.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database schema before serving."""
    init_db()
    yield


app = FastAPI(title="MMS Moderation & Persuasion Prototype", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(feed.router)
app.include_router(chat.router)
app.include_router(moderation.router)
app.include_router(admin.router)


@app.get("/health")
def health() -> dict:
    """Report which implementations are active. Useful during handover demos."""
    return {
        "status": "ok",
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "classifier_binary": settings.classifier_binary_impl,
        "classifier_typed": settings.classifier_typed_impl,
        "rag": settings.rag_impl,
        "registered_harm_types": registered_types(),
    }
