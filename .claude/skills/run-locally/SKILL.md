---
name: run-locally
description: How to bring this MMS prototype up on a fresh machine — backend (FastAPI + SQLite) and frontend (Vite + React). Use when a teammate or their AI assistant asks "how do I run this", "set up the dev environment", "start the server", or hits import/runtime errors during first boot.
---

# Run MMS locally

Two services in this repo. The pipeline runs end-to-end out of the box with **dummy** stubs for every ML stage, so you do **not** need any model weights to boot. Switch a teammate's stage from `dummy` to `team` only after their artifacts are present.

## Prereqs

- Python `>=3.11` (project is verified on 3.13)
- Node `>=18` for the frontend
- macOS / Linux. Windows works for the backend; Vite frontend works on all three
- `uv` is recommended for the backend (pyproject has CUDA wheel pins). Plain `pip + venv` works too

## Backend boot

```bash
cd MMS_back
cp .env.example .env                # then edit if you have an OPENAI_API_KEY
uv sync                              # or: python -m venv .venv && .venv/bin/pip install -e ".[dev]"
uv run uvicorn app.main:app --reload # serves on :8000
```

**macOS quirk:** if uvicorn segfaults at startup or during a `team` classifier call, prefix with `OMP_NUM_THREADS=1 KMP_DUPLICATE_LIB_OK=TRUE`. This is the libomp double-load issue — required on Apple Silicon when torch and faiss are both loaded.

## Frontend boot

```bash
cd MMS_front
npm install
npm run dev                          # serves on :5173, proxies /posts /ingest /mod /sessions /health to :8000
```

Open http://localhost:5173 — `/` (feed), `/mod` (moderator queue), `/ingest` (single-post demo), `/chat/:id` (counsel session).

## Smoke test

```bash
# from MMS_back/
uv run python scripts/seed_mock.py data/mock_posts.jsonl
# or directly:
curl -X POST http://localhost:8000/ingest \
  -H 'content-type: application/json' \
  -d '{"id":"smoke-1","author":{"user_id":"tester"},"text":"Everyone in that group is an idiot."}'
curl http://localhost:8000/mod/queue
```

Run the test suite before pushing:

```bash
OMP_NUM_THREADS=1 KMP_DUPLICATE_LIB_OK=TRUE uv run pytest    # 18 tests, ~3s
```

## Switching dummy → team

Defaults in `MMS_back/.env.example` are all `dummy`. Flip a single knob when that teammate's artifacts land under `MMS_back/models/<name>/`:

```bash
MMS_C1_IMPL=team                # Member A — needs models/classifier_binary/
MMS_C2_IMPL=team                # Member B — needs models/classifier_typed/
MMS_RAG_IMPL=team               # Member C — needs models/rag_index/
MMS_POLISHER_IMPL=team          # Member D — calls Siwei's Colab+ngrok service
```

If a `team` impl fails to load (missing weights, dead endpoint), the pipeline degrades stage-by-stage rather than 500ing — see the per-stage try/except in `app/pipeline.py`.

## Common first-boot errors

| Symptom | Cause | Fix |
|---|---|---|
| `cannot import name 'StrEnum' from 'enum'` | Python <3.11 active | use `python3.13` / activate the project venv |
| Segfault on first inference | libomp double-load | prefix with `OMP_NUM_THREADS=1 KMP_DUPLICATE_LIB_OK=TRUE` |
| `FileNotFoundError: ... best_model.pt` | `MMS_C1_IMPL=team` set but weights not present | revert to `dummy` or place weights under `MMS_back/models/classifier_binary/` |
| Frontend gets 404 from `/posts` | backend not on :8000 | start `uvicorn` first, or set `MMS_API_URL` if proxying elsewhere |
| `OPENAI_API_KEY not set` errors | `MMS_LLM_PROVIDER=openai` without key | put key in `.env` or revert provider to `dummy` |

## Where things live

```
MMS_back/
  app/                FastAPI + pipeline + classifier/rag/polisher/responder
  models/<name>/      ML artifacts (gitignored, populated out of band)
  data/               SQLite DB + seed JSONL
  scripts/seed_mock.py
  tests/              pytest, all-dummy
MMS_front/
  src/                React pages: feed, chat, mod, ingest
```

The **contract** between integrator and teammates is in each module's `base.py` (Protocol definition). `dummy.py` is the always-on fallback; `team.py` / `binary.py` / `typed.py` / `retriever.py` is the real implementation slot.

For deeper architecture, see `RUNNING.md` at the repo root and `CLAUDE.md` for project rules.