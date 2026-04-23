# MMS frontend

Vite + React + TypeScript. Three pages:

- `/`            — Feed (posts, labels, bot replies, link to session chat)
- `/chat/:id`    — Multi-turn counseling chat
- `/mod`         — Moderator queue (approve / edit / reject / log-only / escalate)
- `/ingest`      — Push a single post through the pipeline for demos

## Run

```bash
cd MMS_front
npm install
npm run dev              # http://localhost:5173
```

Vite dev server proxies `/posts`, `/ingest`, `/sessions`, `/mod`, `/health` to
`http://localhost:8000` (the FastAPI backend), so no CORS config needed during
development.
