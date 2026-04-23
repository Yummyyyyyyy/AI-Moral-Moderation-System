"""Shared test fixtures. Points the DB at a temporary file per test."""

from __future__ import annotations

import importlib
import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def fresh_db(monkeypatch):
    """Point settings.db_path at a temp file and re-init the schema."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db_path = tmp.name
    monkeypatch.setenv("MMS_DB_PATH", db_path)
    monkeypatch.setenv("MMS_LLM_PROVIDER", "dummy")
    monkeypatch.setenv("MMS_C1_IMPL", "dummy")
    monkeypatch.setenv("MMS_C2_IMPL", "dummy")
    monkeypatch.setenv("MMS_RAG_IMPL", "dummy")

    # Reload modules that captured settings at import time.
    import app.config as config_mod
    importlib.reload(config_mod)
    import app.store.db as db_mod
    importlib.reload(db_mod)
    db_mod.init_db()
    yield db_path
    Path(db_path).unlink(missing_ok=True)
