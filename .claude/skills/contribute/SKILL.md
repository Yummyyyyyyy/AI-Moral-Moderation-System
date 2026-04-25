---
name: contribute
description: How to contribute to this MMS project — module ownership, run commands, and where to write your code. Use when a teammate asks "where do I start" or "how do I plug in my model".
---

# Contributing to MMS

Two services in this repo:

- [MMS_back/](MMS_back/) — Python 3.11 + FastAPI + SQLite. Pipeline orchestrator.
- [MMS_front/](MMS_front/) — Vite + React + TS. Feed / Chat / Mod / Ingest pages.

The pipeline (`ingest → binary classify → typed classify → rag → responder → moderation`) already works end-to-end with stubs. Your job is to replace ONE stub with your real model — without touching anyone else's files.

## Run locally

```bash
# terminal 1 — backend
cd MMS_back && uv sync && uv run uvicorn app.main:app --reload

# terminal 2 — frontend
cd MMS_front && npm install && npm run dev      # http://localhost:5173

# terminal 3 — seed mock posts (optional)
cd MMS_back && uv run python scripts/seed_mock.py data/mock_posts.jsonl
```

## Where to write your code

Each member owns ONE file. Replace the stub body. Keep the class name and method signature — they match the Protocol in `base.py`, which is the contract.

| Member | File to edit | Method to fill in |
|---|---|---|
| A | [MMS_back/app/classifier/binary.py](MMS_back/app/classifier/binary.py) | `TeamBinaryClassifier.classify(post) -> BinaryLabel` |
| B | [MMS_back/app/classifier/typed.py](MMS_back/app/classifier/typed.py) | `TeamTypedClassifier.categorize(post) -> TypeLabel` |
| C | [MMS_back/app/rag/retriever.py](MMS_back/app/rag/retriever.py) | `TeamRetriever.retrieve(query, harm_type, top_k) -> list[RetrievedDoc]` |
| D | *(no file edit)* | Expose your RLHF model at an OpenAI-compatible endpoint |

Don't import other teams' files. The pipeline picks up your code via the factory once the env var below is set.

## Switch from stub to your real model

Default is `dummy` so the pipeline keeps running while you develop. Flip your own knob when ready:

```bash
export MMS_C1_IMPL=team           # Member A
export MMS_C2_IMPL=team           # Member B
export MMS_RAG_IMPL=team          # Member C
export MMS_LLM_PROVIDER=local     # Member D
export MMS_LOCAL_LLM_URL=http://<your-host>:<port>/v1
```

## Before you open a PR

```bash
cd MMS_back && uv run pytest
```

Project rules (also in [CLAUDE.md](CLAUDE.md)):

- Every function gets a docstring.
- No LLM calls inside `classifier/`, `store/`, or `api/` layers.
- No hardcoded prompts in business logic — prompts live in `app/prompts/*.yaml`.
- LLM access goes through `app.llm.base.LLMClient`; never instantiate vendor SDKs in business logic.
- Reply drafts are persisted before publishing; moderation actions are audited.
