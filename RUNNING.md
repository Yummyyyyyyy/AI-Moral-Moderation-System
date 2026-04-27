# Running MMS end-to-end

This runbook covers everything needed to bring the prototype up on a fresh machine, exercise the full pipeline, and switch from dummy stubs to real teammate models. Read it linearly the first time; afterwards the table of contents is the index you actually use.

- [What you're booting](#what-youre-booting)
- [Prerequisites](#prerequisites)
- [Repository layout](#repository-layout)
- [First-time setup](#first-time-setup)
- [Day-to-day commands](#day-to-day-commands)
- [Configuration reference](#configuration-reference)
- [Switching from dummy to team models](#switching-from-dummy-to-team-models)
- [Verifying the pipeline works](#verifying-the-pipeline-works)
- [Tests](#tests)
- [Troubleshooting](#troubleshooting)

---

## What you're booting

Two services that talk to each other on localhost:

```
┌──────────────────────────┐         ┌──────────────────────────────────────┐
│ MMS_front (Vite + React) │  HTTP   │ MMS_back (FastAPI + SQLite)          │
│ http://localhost:5173    │ ──────▶ │ http://localhost:8000                │
│ Pages: feed, chat, mod,  │         │ Routes: /ingest /posts /mod /chat   │
│        ingest            │         │         /sessions /health            │
└──────────────────────────┘         └──────────────────────────────────────┘
                                                     │
                                                     ▼
                                    ┌────────────────────────────────────┐
                                    │ Pipeline (app/pipeline.py)         │
                                    │ ingest → C1 binary → C2 typed →    │
                                    │ RAG → responder → polisher → mod   │
                                    └────────────────────────────────────┘
```

Each ML stage is pluggable: a Protocol in `base.py`, a `dummy.py` working stub, and a team-owned real implementation. The pipeline boots end-to-end with all dummies even if no ML weights exist on disk — that is the design goal so a teammate can develop their stage without blocking everyone else.

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | `>=3.11` | Verified on 3.13. `StrEnum` is required, so 3.10 will not work. |
| Node | `>=18` | Vite 5 / React 18. |
| `uv` | latest | Recommended; the backend `pyproject.toml` pins a CUDA torch wheel index when present. Plain `pip + venv` works as a fallback. |
| Git | any | |

Optional, for `team` stages:

| Stage | Requirement |
|---|---|
| Member A binary classifier | `MMS_back/models/classifier_binary/best_model.pt` + `tokenizer/` + `results.json` |
| Member B typed classifier | `MMS_back/models/classifier_typed/best_model.pt` + tokenizer files |
| Member C RAG retriever | `MMS_back/models/rag_index/{faiss.index,meta.pkl,knowledge.faiss,knowledge_meta.pkl}` |
| Member D polisher | Either `MMS_POLISHER_URL` pinned to a reachable endpoint, or a Google Drive file id baked into `app/polisher/team.py` |
| OpenAI responder | `OPENAI_API_KEY` in `.env` |

The `models/` directory is gitignored; weights are distributed out of band.

## Repository layout

```
MMS/
├── CLAUDE.md                   project rules + module ownership
├── RUNNING.md                  this file
├── MMS_back/
│   ├── app/
│   │   ├── api/                FastAPI routers
│   │   ├── classifier/         binary + typed stage (base / dummy / team)
│   │   ├── rag/                retriever (base / dummy / team)
│   │   ├── llm/                LLMClient + dummy / openai / local adapters
│   │   ├── polisher/           post-responder rewriter (base / dummy / team)
│   │   ├── responder/          PersuadeResponder, CounselResponder, registry
│   │   ├── prompts/            YAML prompt templates
│   │   ├── schemas/            Pydantic v2 models shared across layers
│   │   ├── store/              SQLite helpers (posts/classifications/replies/sessions/audit)
│   │   ├── pipeline.py         orchestrator
│   │   ├── config.py           env-driven settings + model_dir(name) resolver
│   │   └── main.py             FastAPI app
│   ├── data/
│   │   ├── mock_posts.jsonl    seed fixture
│   │   └── mms.db              SQLite (created on first run)
│   ├── models/                 ML artifacts, gitignored
│   │   ├── classifier_binary/  Member A
│   │   ├── classifier_typed/   Member B
│   │   └── rag_index/          Member C
│   ├── scripts/seed_mock.py    posts a JSONL file into /ingest
│   ├── tests/                  pytest; runs all-dummy in <5s
│   ├── .env.example            template; copy to .env (gitignored)
│   └── pyproject.toml
└── MMS_front/
    ├── src/                    feed / chat / mod / ingest pages
    ├── package.json
    └── vite.config.ts          dev proxy to :8000
```

## First-time setup

### Backend

```bash
cd MMS_back
cp .env.example .env                              # edit only if you need a real OpenAI key
uv sync                                           # creates .venv, resolves deps
# fallback if you don't have uv:
#   python3.13 -m venv .venv
#   .venv/bin/pip install -e ".[dev]"
```

The default `.env` keeps every stage on `dummy`, so the pipeline boots with no model files present.

### Frontend

```bash
cd MMS_front
npm install
```

## Day-to-day commands

Three terminals during development:

```bash
# terminal 1 — backend (auto-reloads on file change)
cd MMS_back
OMP_NUM_THREADS=1 KMP_DUPLICATE_LIB_OK=TRUE uv run uvicorn app.main:app --reload
# frontend
cd MMS_front && npm run dev                       # http://localhost:5173

# terminal 3 — drive traffic into the pipeline
cd MMS_back
uv run python scripts/seed_mock.py data/mock_posts.jsonl
```

The two `OMP_NUM_THREADS=1 KMP_DUPLICATE_LIB_OK=TRUE` env vars are an Apple-Silicon libomp workaround. Always-on for `team` stages. Linux + CUDA does not need them.

## Configuration reference

Every knob the backend reads. Defaults are in `MMS_back/app/config.py`; override via `.env` or shell env.

| Variable | Default | Purpose |
|---|---|---|
| `MMS_DB_PATH` | `data/mms.db` | SQLite file location |
| `MMS_LLM_PROVIDER` | `dummy` | `dummy` / `openai` / `local` — picks the responder LLM |
| `MMS_LLM_MODEL` | `gpt-4o-mini` | Model id for the chosen provider |
| `OPENAI_API_KEY` | *(unset)* | Required when `MMS_LLM_PROVIDER=openai`. Put in `.env`. |
| `MMS_LOCAL_LLM_URL` | `http://localhost:11434/v1` | OpenAI-compatible base URL for a local responder LLM |
| `MMS_C1_IMPL` | `dummy` | `dummy` / `team` — Member A binary classifier |
| `MMS_C2_IMPL` | `dummy` | `dummy` / `team` — Member B typed classifier |
| `MMS_RAG_IMPL` | `dummy` | `dummy` / `team` — Member C retriever (HATE only when team) |
| `MMS_POLISHER_IMPL` | `dummy` | `dummy` / `team` — Member D draft polisher |
| `MMS_POLISHER_URL` | *(empty)* | Pin polisher endpoint; otherwise auto-fetched from Drive |
| `MMS_POLISHER_TIMEOUT` | `15` | Seconds; applies to both URL fetch and inference call |
| `MMS_AUTO_PUBLISH` | `0` | `1` bypasses moderator queue (demo only) |
| `MMS_CLASSIFIER_BINARY_DIR` | `models/classifier_binary` | Override Member A artifact path |
| `MMS_CLASSIFIER_TYPED_DIR` | `models/classifier_typed` | Override Member B artifact path |
| `MMS_RAG_INDEX_DIR` | `models/rag_index` | Override Member C artifact path |
| `MMS_TYPED_DEVICE` | *(auto)* | Force `cpu` / `cuda` / `mps` for the typed classifier |

## Switching from dummy to team models

Each teammate owns one stage. Their artifacts must be on disk before flipping the impl knob.

```bash
# Member A — binary classifier
ls MMS_back/models/classifier_binary/best_model.pt    # must exist
export MMS_C1_IMPL=team

# Member B — typed classifier
ls MMS_back/models/classifier_typed/best_model.pt
export MMS_C2_IMPL=team

# Member C — RAG retriever (HATE-only when team)
ls MMS_back/models/rag_index/faiss.index
export MMS_RAG_IMPL=team

# Member D — polisher (Siwei's Colab+ngrok service)
export MMS_POLISHER_IMPL=team
# either pin the URL:
export MMS_POLISHER_URL=https://abc-123.ngrok.io
# or let the polisher auto-resolve from the shared Drive file
```

Each stage has independent fallback. If `team` fails to load or raises at call time, the pipeline records an error note and continues to the next stage rather than 500ing. The counsel path (depressive / self-harm) deliberately **skips** the polisher to preserve crisis-hotline content verbatim — see `pipeline.py` and `tests/test_polisher_bypass.py`.

## Verifying the pipeline works

After `uvicorn` is up, hit a few endpoints:

```bash
# liveness
curl http://localhost:8000/health

# push one post through the full pipeline
curl -X POST http://localhost:8000/ingest \
  -H 'content-type: application/json' \
  -d '{"id":"hate-1","author":{"user_id":"tester"},
       "text":"Everyone in that group is an idiot, shut up."}'

# moderator queue (should now contain a pending reply)
curl http://localhost:8000/mod/queue

# trigger a counsel session
curl -X POST http://localhost:8000/ingest \
  -H 'content-type: application/json' \
  -d '{"id":"sh-1","author":{"user_id":"tester"},
       "text":"I want to kill myself tonight."}'
# returned payload includes session.id; chat at /chat/<session.id> in the frontend
```

Or skip curl and visit the frontend:
- `/ingest` — single-post demo with the response inline
- `/` — feed view
- `/mod` — moderator queue
- `/chat/:id` — multi-turn counsel session

## Tests

```bash
cd MMS_back
OMP_NUM_THREADS=1 KMP_DUPLICATE_LIB_OK=TRUE uv run pytest
```

The suite is **all-dummy** by design: it does not load any team weights, runs in a few seconds, and is what CI will gate on. Coverage today:

- `tests/test_pipeline.py` — neutral, hate, depressive, self-harm post flows
- `tests/test_factory_contract.py` — every dummy factory returns the expected class and its protocol method works; team classes still expose `classify` / `categorize` / `retrieve` / `polish` (introspection only)
- `tests/test_polisher_bypass.py` — counsel paths skip the polisher; persuade paths still polish and stash the raw draft
- `tests/test_moderation.py` — moderator queue and approval round-trip
- `tests/test_registry.py` — responder spec wiring per harm type

When adding a team implementation, do not modify the existing dummy tests — add new tests under a `team_` prefix and gate them with `pytest.importorskip(...)` for any heavy ML dependency.

## Troubleshooting

### `ImportError: cannot import name 'StrEnum' from 'enum'`
You're on Python <3.11. Activate the project venv (`MMS_back/.venv`) or invoke `python3.13` directly.

### Segfault during first `team` inference on macOS
PyTorch and faiss both ship libomp; the second one to load crashes the process. Always start the backend with:
```bash
OMP_NUM_THREADS=1 KMP_DUPLICATE_LIB_OK=TRUE uv run uvicorn ...
```

### `FileNotFoundError: ... best_model.pt`
You set `MMS_C1_IMPL=team` (or `C2`) without placing weights under `models/<name>/`. Either drop the weights in or revert to `dummy`.

### Frontend shows network errors / blank pages
Backend is not on :8000. Start `uvicorn` first. Vite proxy assumes the FastAPI port is fixed.

### `OPENAI_API_KEY not set` at startup
You set `MMS_LLM_PROVIDER=openai` but `.env` is missing the key. Either fill it in or revert provider to `dummy` (`MMS_LLM_PROVIDER=dummy`).

### Polisher times out / hangs the request
Member D's Colab session probably died. Either set `MMS_POLISHER_IMPL=dummy` to bypass for now, or refresh `MMS_POLISHER_URL` from Siwei.

### `ModuleNotFoundError: No module named 'app'`
You ran pytest from the repo root. The pyproject pins `pythonpath = ["."]` relative to `MMS_back/`, so run pytest from inside `MMS_back/`.

### CUDA wheel index errors during `uv sync` on macOS
The pyproject pins a `cu124` torch index. macOS doesn't have CUDA; uv will still resolve a CPU/MPS-compatible wheel because `torch` itself doesn't gate on the index. If it errors, replace the `[[tool.uv.index]]` block in `pyproject.toml` with the CPU URL (`https://download.pytorch.org/whl/cpu`) for your local checkout.

---

For module-level architecture and contribution rules see `CLAUDE.md`. For per-service detail see `MMS_back/README.md` and `MMS_front/README.md`.