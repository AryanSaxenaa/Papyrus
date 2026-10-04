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

Replay-only demos: set `PAPYRUS_MODE=replay`, `PERSISTENCE_BACKEND=json`, ship fixtures under `AUDIT_DATA_DIR/fixtures/` (Dockerfile.railway copies `backend/tests/fixtures/replay/`). SerpApi and LLM API keys are optional in production when mode is replay.

Smoke / E2E:

```bash
# API (set LIVE_ACCESS_CODE for live ingest checks)
python backend/scripts/api_smoke_remote.py --base https://your-app.up.railway.app --access-code "$LIVE_ACCESS_CODE" --live-doi

# Playwright UI
cd e2e && npm ci && npx playwright install chromium && PAPYRUS_E2E_BASE_URL=https://your-app.up.railway.app npm test
```

## Full profile

Add `REDIS_URL`, `USE_CELERY_BACKGROUND=true`, and a second service running:

`celery -A app.worker.celery_app worker -Q audits-production -c 1 --loglevel=info`

Match `CELERY_AUDIT_QUEUE` / `APP_ENV` to the queue name your worker listens on.
