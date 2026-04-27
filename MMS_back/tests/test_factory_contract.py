"""Pins the dummy↔team factory contract.

Each module's factory must return an object that satisfies its Protocol's
method shape. Dummy implementations are exercised end-to-end (cheap, no
heavy deps) while team classes are checked by introspection only --
instantiating them requires real model weights / network endpoints, which
we don't want to drag into the test suite.

If a teammate renames ``classify`` / ``categorize`` / ``retrieve`` /
``polish`` on a team class, these tests fail loudly before the change
breaks the pipeline.
"""

from __future__ import annotations

import importlib

import pytest

from app.schemas.classification import BinaryLabel, HarmType, TypeLabel
from app.schemas.post import Author, Post
from app.schemas.rag import RetrievedDoc


def _post(text: str = "hello") -> Post:
    """Build a minimal Post for protocol-method smoke calls."""
    return Post(id="contract", author=Author(user_id="tester"), text=text)


def _reload_factory(monkeypatch, env_var: str, value: str, factory_module: str):
    """Set env var, reload config + factory module, return reloaded factory."""
    monkeypatch.setenv(env_var, value)
    import app.config as config_mod
    importlib.reload(config_mod)
    mod = importlib.import_module(factory_module)
    return importlib.reload(mod)


# ---- Dummy contract: factory returns dummy AND its method works on real input ----


def test_binary_factory_dummy_returns_working_classifier(monkeypatch):
    """MMS_C1_IMPL=dummy → DummyBinaryClassifier whose .classify produces a BinaryLabel."""
    factory = _reload_factory(monkeypatch, "MMS_C1_IMPL", "dummy", "app.classifier.factory")
    clf = factory.get_binary_classifier()
    assert clf.__class__.__name__ == "DummyBinaryClassifier"
    label = clf.classify(_post("hello"))
    assert isinstance(label, BinaryLabel)


def test_typed_factory_dummy_returns_working_classifier(monkeypatch):
    """MMS_C2_IMPL=dummy → DummyTypedClassifier whose .categorize produces a TypeLabel."""
    factory = _reload_factory(monkeypatch, "MMS_C2_IMPL", "dummy", "app.classifier.factory")
    clf = factory.get_typed_classifier()
    assert clf.__class__.__name__ == "DummyTypedClassifier"
    label = clf.categorize(_post("idiot"))
    assert isinstance(label, TypeLabel)


def test_rag_factory_dummy_returns_working_retriever(monkeypatch):
    """MMS_RAG_IMPL=dummy → DummyRetriever whose .retrieve returns list[RetrievedDoc]."""
    factory = _reload_factory(monkeypatch, "MMS_RAG_IMPL", "dummy", "app.rag.factory")
    retriever = factory.get_retriever()
    assert retriever.__class__.__name__ == "DummyRetriever"
    docs = retriever.retrieve("foo", HarmType.HATE, top_k=2)
    assert isinstance(docs, list)
    for doc in docs:
        assert isinstance(doc, RetrievedDoc)


def test_polisher_factory_dummy_returns_working_polisher(monkeypatch):
    """MMS_POLISHER_IMPL=dummy → DummyPolisher whose .polish returns a string."""
    factory = _reload_factory(
        monkeypatch, "MMS_POLISHER_IMPL", "dummy", "app.polisher.factory"
    )
    pol = factory.get_polisher()
    assert pol.__class__.__name__ == "DummyPolisher"
    out = pol.polish("hello")
    assert isinstance(out, str)


# ---- Team contract: classes still expose the right method names ----
# Introspection only -- instantiating Team* requires real model weights.


def test_team_binary_class_has_classify_method():
    """TeamBinaryClassifier must keep its .classify method."""
    from app.classifier.binary import TeamBinaryClassifier
    assert callable(getattr(TeamBinaryClassifier, "classify", None))


def test_team_typed_class_has_categorize_method():
    """TeamTypedClassifier must keep its .categorize method."""
    from app.classifier.typed import TeamTypedClassifier
    assert callable(getattr(TeamTypedClassifier, "categorize", None))


def test_team_retriever_has_retrieve_method():
    """TeamRetriever must keep its .retrieve method (skip if ML deps missing)."""
    pytest.importorskip("faiss")
    pytest.importorskip("sentence_transformers")
    from app.rag.retriever import TeamRetriever
    assert callable(getattr(TeamRetriever, "retrieve", None))


def test_team_polisher_has_polish_method():
    """TeamPolisher must keep its .polish method."""
    from app.polisher.team import TeamPolisher
    assert callable(getattr(TeamPolisher, "polish", None))