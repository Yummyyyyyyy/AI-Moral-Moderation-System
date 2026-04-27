# MMS backend

Prototype moderation-and-persuasion pipeline. Python 3.11 + FastAPI + SQLite.

## Layout

```
app/
  api/          FastAPI routers: ingest, feed, chat, moderation
  classifier/   Stage-1 binary + stage-2 typed classifiers (base + dummy + team stub)
  rag/          Retriever (base + dummy + team stub)
  llm/          LLMClient + dummy / openai / local adapters
  polisher/     Post-responder draft polisher (base + dummy + team)
  prompts/      YAML prompt templates (persuade/*, counsel/*)
  responder/    PersuadeResponder, CounselResponder, Registry
  schemas/      Pydantic schemas shared across layers
  store/        SQLite helpers (posts, classifications, replies, sessions, audit)
  pipeline.py   Orchestrator
  main.py       FastAPI app
scripts/
  seed_mock.py  POSTs a JSONL file to /ingest
models/         ML weights & FAISS indexes (gitignored; populated out of band)
  classifier_binary/   Member A — RoBERTa-base toxicity classifier
  classifier_typed/    Member B — multitask RoBERTa harm-type classifier
  rag_index/           Member C — FAISS case + knowledge indexes
data/
  mock_posts.jsonl     Seed fixture for the mock stream
  rag_corpus/          (optional) source docs for rebuilding the RAG index
  mms.db               Runtime SQLite (created on first run)
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
| `MMS_POLISHER_IMPL` | `dummy` | `dummy` / `team`. `team` calls Member D's Colab+ngrok service to refine every reply draft. Failures fall back to the unpolished draft. |
| `MMS_POLISHER_URL` | *(empty)* | Pin the polisher endpoint explicitly. Leave empty to auto-resolve from the shared Google Drive file Siwei publishes on each Colab boot. |
| `MMS_POLISHER_TIMEOUT` | `15` | Seconds. Applies to both URL fetch and the inference call. |
| `MMS_AUTO_PUBLISH` | `0` | `1` bypasses the moderator queue (demo only). |
| `MMS_CLASSIFIER_BINARY_DIR` | `models/classifier_binary` | Override where Member A's RoBERTa weights live. |
| `MMS_CLASSIFIER_TYPED_DIR` | `models/classifier_typed` | Override where Member B's multitask checkpoint lives. |
| `MMS_RAG_INDEX_DIR` | `models/rag_index` | Override where Member C's FAISS indexes live. |
| `MMS_TYPED_DEVICE` | *(auto)* | Force `cpu` / `cuda` / `mps` for the typed classifier. |

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

- Member A implements `TeamBinaryClassifier.classify` in [app/classifier/binary.py](app/classifier/binary.py); weights in `models/classifier_binary/`.
- Member B implements `TeamTypedClassifier.categorize` in [app/classifier/typed.py](app/classifier/typed.py); checkpoint in `models/classifier_typed/`.
- Member C implements `TeamRetriever.retrieve` in [app/rag/retriever.py](app/rag/retriever.py); FAISS indexes in `models/rag_index/`.
- Member D implements `TeamPolisher.polish` in [app/polisher/team.py](app/polisher/team.py) backed by a Colab+ngrok service; the integrator sets `MMS_POLISHER_IMPL=team`.

No module imports any other team's internals — everything goes through the
Protocols in each package's `base.py`.
