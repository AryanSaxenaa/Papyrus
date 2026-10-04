# Railway deployment (Papyrus)

Lean profile: one `papyrus` service + Postgres plugin. Full profile adds Redis and a Celery worker.

## Build

- Dockerfile: `Dockerfile.railway` at repo root
- Config: `railway.json` (healthcheck `/api/health`)

## Lean environment (API + SPA)

| Variable | Value |
|----------|--------|
| `APP_ENV` | `production` |
| `PAPYRUS_MODE` | `live` |
| `SERVE_FRONTEND` | `true` |
| `STATIC_DIR` | `/app/static` |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |
| `PERSISTENCE_BACKEND` | `postgres` |
| `FILE_STORAGE_BACKEND` | `postgres` |
| `USE_CELERY_BACKGROUND` | `false` |
| `PUBLIC_DEMO_MODE` | `true` |
| `LIVE_ACCESS_CODE` | (secret) |
| `SERPAPI_API_KEY` | (secret) |
| `SERPAPI_SCOPE` | `residual` |
| `NLI_BACKEND` | `lexical` |
| `EMBEDDINGS_BACKEND` | `lexical` |
| `CROSSREF_MAILTO` / `OPENALEX_MAILTO` / `UNPAYWALL_EMAIL` | real addresses |

Shepherd / recorded demo: `PAPYRUS_MODE=live` still preloads `POST /api/audits/replay/demo-a` from shipped fixtures (`Dockerfile.railway` copies `backend/tests/fixtures/replay/`). User uploads in live mode call providers directly.

Refresh `demo-a` after pipeline changes:

```bash
cd backend
python scripts/record_replay_fixture.py \
  --pdf tests/fixtures/sample-pdfs/2108.12837v1.pdf \
  --set demo-a \
  --serpapi-scope all \
  --record-transport
```

Requires network and API keys in `.env` (include `SERPAPI_API_KEY` for Scholar receipts). Rebuild and redeploy to pick up new fixtures.

Replay-only deployments: set `PAPYRUS_MODE=replay`, `PERSISTENCE_BACKEND=json`. SerpApi keys optional when mode is replay.

## Full profile

Add `REDIS_URL`, `USE_CELERY_BACKGROUND=true`, and a second service running:

`celery -A app.worker.celery_app worker -Q audits-production -c 1 --loglevel=info`

Match `CELERY_AUDIT_QUEUE` / `APP_ENV` to the queue name your worker listens on.
