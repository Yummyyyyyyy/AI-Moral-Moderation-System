# MMS backend

Prototype moderation-and-persuasion pipeline. Python 3.11 + FastAPI + SQLite.

## Layout

```
app/
  api/          FastAPI routers: ingest, feed, chat, moderation
  classifier/   Stage-1 binary + stage-2 typed classifiers (base + dummy + team stub)
  rag/          Retriever (base + dummy + team stub)
  llm/          LLMClient + dummy/claude/local adapters
  prompts/      YAML prompt templates (persuade/*, counsel/*)
  responder/    PersuadeResponder, CounselResponder, Registry
  schemas/      Pydantic schemas shared across layers
  store/        SQLite helpers (posts, classifications, replies, sessions, audit)
  pipeline.py   Orchestrator
  main.py       FastAPI app
scripts/
  seed_mock.py  POSTs a JSONL file to /ingest
data/
  mock_posts.jsonl
tests/
```

## Environment knobs

| Var | Default | Meaning |
|---|---|---|
| `MMS_DB_PATH` | `data/mms.db` | SQLite file |
| `MMS_LLM_PROVIDER` | `dummy` | `dummy` / `openai` / `local` |
| `MMS_LLM_MODEL` | `gpt-4o-mini` | model id passed to the chosen provider |
| `OPENAI_API_KEY` | *(unset)* | required when provider=openai. Put it in `.env` (see `.env.example`); `.env` is gitignored. |
| `MMS_LOCAL_LLM_URL` | `http://localhost:11434/v1` | OpenAI-compatible base URL for local model (Ollama / vLLM / TGI) |
| `MMS_C1_IMPL` | `dummy` | `dummy` / `team` |
| `MMS_C2_IMPL` | `dummy` | `dummy` / `team` |
| `MMS_RAG_IMPL` | `dummy` | `dummy` / `team` (currently only handles `HATE` posts; other harm types degrade to empty) |

## Run

```bash
cd MMS_back
uv sync
uv run uvicorn app.main:app --reload
# in another shell
uv run python scripts/seed_mock.py data/mock_posts.jsonl
```

> **CUDA note (Windows):** `pyproject.toml` pins torch to the `cu124` wheel index
> (pytorch.org), which works for CUDA 12.4 and 12.5.
> If your driver reports a different CUDA version (`nvidia-smi` → top-right corner),
> change the index name and URL in `[tool.uv.sources]` / `[[tool.uv.index]]`:
>
> | CUDA version | index name | URL suffix |
> |---|---|---|
> | 12.4 / 12.5 | `pytorch-cu124` | `/whl/cu124` |
> | 12.1 | `pytorch-cu121` | `/whl/cu121` |
> | 11.8 | `pytorch-cu118` | `/whl/cu118` |
> | CPU only | `pytorch-cpu` | `/whl/cpu` |
>
> After changing, re-run `uv sync`.

Then hit `GET http://localhost:8000/posts`, `GET /mod/queue`, etc.

## Team contract

- Member A implements `TeamBinaryClassifier.classify` in [app/classifier/binary.py](app/classifier/binary.py).
- Member B implements `TeamTypedClassifier.categorize` in [app/classifier/typed.py](app/classifier/typed.py).
- Member C implements `TeamRetriever.retrieve` in [app/rag/retriever.py](app/rag/retriever.py).
- Member D exposes their RLHF model at an OpenAI-compatible endpoint; the integrator sets `MMS_LLM_PROVIDER=local` and `MMS_LOCAL_LLM_URL=<url>`.

No module imports any other team's internals — everything goes through the
Protocols in each package's `base.py`.
