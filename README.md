# Papyrus

Citation integrity audit pipeline — verifies that references exist, classifies failure modes, and scores evidentiary claim alignment.

Papyrus does **not** detect AI authorship. It audits the reference layer.

## SerpApi India Hackathon 2026

| | |
|---|---|
| **Track** | [**Knowledge & Public Interest**](https://serpapi.github.io/serpapi-india-hackathon-2026/#tracks) — Scholar / research tools |
| **SerpApi role** | Core witness layer via **`google_scholar`**, **`google_scholar_cite`**, **`google_scholar_author`** (budget, cache, ledger, UI receipts, evidence bundle) |
| **Live demo** | https://papyrus-production-70fb.up.railway.app/app — opt-in **Shepherd mode** walks the UI with a real replay audit |
| **Details** | [docs/SERPAPI_INDIA_HACKATHON.md](docs/SERPAPI_INDIA_HACKATHON.md) · [docs/METHOD.md](docs/METHOD.md) · [docs/spec/PAPYRUS-FULL-SPEC.md](docs/spec/PAPYRUS-FULL-SPEC.md) |

Pre-existing project: **Yes** (tag `pre-hackathon-baseline`). Hackathon work adds meaningful, evidenced SerpApi usage — see [docs/PRE_EXISTING_WORK.md](docs/PRE_EXISTING_WORK.md).

[![Watch the video](https://img.youtube.com/vi/_FrRz0Y-tTk/maxresdefault.jpg)](https://youtu.be/_FrRz0Y-tTk)

## Audit duration (expect 10–15 minutes)

A typical PDF audit with roughly **10–15 citations** takes about **10–15 minutes** end to end. That is intentional, not a hang.

Papyrus walks each citation through multiple resolvers (CrossRef, Semantic Scholar, OpenAlex, Unpaywall, Europe PMC, arXiv, and optional Exa/Firecrawl) and applies **per-provider throttling** so we stay inside each service’s polite-use and free-tier limits. For example, the backend spaces CrossRef calls (~10/s cap), Semantic Scholar (~1/s), and arXiv (one request every 3 seconds). Citations are resolved with limited concurrency so we do not burst providers.

On **free or hobby API tiers**, those limits are tighter and audits skew toward the longer end of the range. **Paid or higher-quota keys** (Semantic Scholar, OpenAlex, Hugging Face inference, etc.) allow higher throughput; you can raise budgets in code via `backend/app/services/rate_limits.py` if your contracts permit it.

While an audit runs, the activity log streams resolver steps in real time. Status stays `running` until resolution and scoring finish. Production should use the **Celery worker** (`papyrus-worker` on Cloud Run) so work is not tied to a single browser request; see [health/detailed](https://papyrus-api-694307068650.us-central1.run.app/api/health/detailed) for `celery_worker_available` and `effective_mode: celery`.

## Stack

- **Backend:** FastAPI, Postgres, Redis (cache + Celery broker), Celery worker (`audits-production` / `audits-development` queues), GCS or local file storage for PDFs
- **Ingestion:** PyMuPDF (default); optional GROBID when enabled
- **Resolution:** CrossRef, Semantic Scholar, OpenAlex, Unpaywall, Europe PMC (REST), arXiv API, Exa (signal-only), Firecrawl (landing abstracts); optional Apify for arXiv/journal fallbacks
- **SerpApi (Scholar witness):** `google_scholar`, `google_scholar_cite`, `google_scholar_author` — receipts, monthly cap, witness matrix in UI (`backend/app/services/serpapi/`) only
- **NLI / embeddings:** Hugging Face Inference (default) or OpenRouter/OpenAI/lexical fallbacks
- **Frontend:** React + Vite + Tailwind, D3 heatmap/timeline, pdf.js paper anatomy, sample PDF on upload card

## Documentation

| Doc | Contents |
|-----|----------|
| [docs/SERPAPI_INDIA_HACKATHON.md](docs/SERPAPI_INDIA_HACKATHON.md) | Hackathon track, SerpApi engines, submission checklist |
| [docs/configuration.md](docs/configuration.md) | Env vars: PDF ingestion, LLM backends, NLI, embeddings, Celery |
| [docs/cloudrun-deployment.md](docs/cloudrun-deployment.md) | Cloud Run + Supabase/Redis/GCS (recommended for GCP) |
| [docs/gcp-deployment.md](docs/gcp-deployment.md) | Cloud SQL, VMs, cost options |
| [papyrus-spec.md](./papyrus-spec.md) | Full product architecture (some ingestion details differ from current defaults) |

## Production deployment (Google Cloud Run)

**GCP project:** `papyrus-audit` (display name *Papyrus*). The project ID `papyrus` is not available globally; use `papyrus-audit` in `deploy/cloudrun/.env`.

**External services (not on GCP):** Supabase Postgres (`DATABASE_URL`), Redis Cloud (`REDIS_URL`), optional third-party API keys (DeepSeek, Hugging Face, OpenRouter, Exa, Firecrawl, OpenAlex, Unpaywall; Apify optional for narrow fallbacks).

### Live URLs

| Service | URL | Notes |
|---------|-----|--------|
| **Web UI** | https://papyrus-web-694307068650.us-central1.run.app | Static React; `VITE_API_BASE_URL` baked at build time |
| **API** | https://papyrus-api-694307068650.us-central1.run.app | FastAPI on port 8080 |
| **Health** | https://papyrus-api-694307068650.us-central1.run.app/api/health/detailed | Postgres, Redis, Celery heartbeat/inspect, GCS |
| **Worker** | `papyrus-worker` (private) | Celery on `audits-production`; `min-instances=1`; Redis heartbeat |
| **Sample PDF** | https://papyrus-web-694307068650.us-central1.run.app/samples/2108.12837v1.pdf | Bundled arXiv example (Try sample PDF in UI) |

Cloud Run serves each service on two hostnames (hash and project-number forms). **`CORS_ORIGINS` must list every web URL you use**, comma-separated, or the browser shows “Failed to fetch”.

**Production settings:** `APP_ENV=production`, `PERSISTENCE_BACKEND=postgres`, `FILE_STORAGE_BACKEND=gcs`, `GCS_BUCKET=papyrus-data-papyrus-audit`, `GROBID_ENABLED=false`, `ENABLE_LLM_PDF_INGESTION=false`.

### Deploy from scratch

1. Copy [deploy/cloudrun/env.template](deploy/cloudrun/env.template) to `deploy/cloudrun/.env` and set `GCP_PROJECT_ID=papyrus-audit`, `DATABASE_URL`, `REDIS_URL`, API keys, and real resolver mailtos.
2. Initialize Postgres (once): `cd backend && python scripts/init_db.py` (with `DATABASE_URL` set), or `INIT_DB=1` before the deploy script on first run.
3. From repo root:

   ```powershell
   .\deploy\cloudrun\deploy.ps1
   ```

   ```bash
   chmod +x deploy/cloudrun/deploy.sh && ./deploy/cloudrun/deploy.sh
   ```

4. After the first deploy, set `CORS_ORIGINS` in `deploy/cloudrun/.env` to the **web** URL, then redeploy API + worker only:

   ```powershell
   $env:SKIP_WEB = "1"
   .\deploy\cloudrun\deploy.ps1
   ```

Deploy creates **papyrus-api**, **papyrus-worker**, and **papyrus-web** in `us-central1`; PDFs in GCS; PyMuPDF ingestion only (no GROBID container). Details: [docs/cloudrun-deployment.md](docs/cloudrun-deployment.md), [deploy/cloudrun/README.md](deploy/cloudrun/README.md).

## Configuration (summary)

Default stack (see [docs/configuration.md](docs/configuration.md) for full list):

| Area | Default | Notes |
|------|---------|--------|
| PDF parsing | PyMuPDF | `GROBID_ENABLED=false` |
| LLM on full PDF | Off | `ENABLE_LLM_PDF_INGESTION=false` (hallucination risk) |
| Intent + claims | DeepSeek API | `LLM_BACKEND=deepseek`, `DEEPSEEK_MODEL` (e.g. `deepseek-v4-flash` in `.env`; code default is `deepseek-chat`) |
| Alt LLM host | OpenRouter only | `LLM_BACKEND=openrouter` — e.g. `openrouter/owl-alpha`, `OPENROUTER_FALLBACK_MODEL` (Nemotron); not used for DeepSeek-hosted models |
| NLI | Hugging Face | `NLI_BACKEND=hf`, `HUGGINGFACE_API_KEY` |
| Embeddings | Snowflake Arctic (HF) | `EMBEDDINGS_BACKEND=snowflake` |
| Background jobs | Celery | `USE_CELERY_BACKGROUND=true`, Redis, worker on `audits-{APP_ENV}` |
| Celery queue | `audits-production` (prod) | Isolates prod from local `audits-development` on shared Redis |
| SerpApi Scholar witness | `SERPAPI_ENABLED`, `SERPAPI_API_KEY` | Engines: `google_scholar`, `google_scholar_cite`, `google_scholar_author` |
| Replay demo | `PAPYRUS_MODE=replay` | No keys; fixtures under `AUDIT_DATA_DIR/fixtures/`; `make demo` |

Copy [`.env.example`](.env.example) to `.env` and set resolver mailtos (`CROSSREF_MAILTO`, `OPENALEX_MAILTO`, `UNPAYWALL_EMAIL`). Do not point a local Celery worker at production `REDIS_URL` unless it uses `audits-development` only.

## Quick start

### 1. Environment

```bash
cp .env.example .env
# Required: contact emails for CrossRef / OpenAlex / Unpaywall
# Optional: DEEPSEEK_API_KEY, HUGGINGFACE_API_KEY, OPENROUTER_API_KEY
```

### 2. Infrastructure (optional but recommended)

```bash
docker compose up -d postgres redis
```

Full stack (API + UI + Celery worker):

```bash
docker compose up --build api worker web
```

Judge / offline demo (replay, no Postgres/Redis/Celery):

```bash
docker compose --profile lite up --build
# or: make demo
```

Pre-hackathon baseline: git tag `pre-hackathon-baseline`. SerpApi hackathon work is in commits after that tag. See [docs/PRE_EXISTING_WORK.md](docs/PRE_EXISTING_WORK.md) and [docs/spec/PAPYRUS-FULL-SPEC.md](docs/spec/PAPYRUS-FULL-SPEC.md).

`api` and `worker` load `.env` from the repo root. **GROBID is not started by default.** To enable later:

```bash
docker compose --profile grobid up -d grobid
# Set GROBID_ENABLED=true in .env
```

### Bulk ZIP jobs

`USE_CELERY_BULK` defaults to **true**. The API enqueues to Celery when Redis is up and a worker is detected (Redis heartbeat or inspect on `audits-development` locally / `audits-production` in prod). Otherwise it falls back to in-process `BackgroundTasks` (fine for local `uvicorn` without a worker; avoid for long production PDFs). Docker Compose runs `worker` on queue `audits-development`.

### 3. API

Use **Python 3.12** (3.14 lacks prebuilt wheels for some dependencies on Windows). Docker is the simplest path on Windows.

```bash
cd backend
python3.12 -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Or run everything via Docker:

```bash
docker compose up --build api
```

### 4. UI

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 and upload a PDF, or use **Try sample PDF** (bundled arXiv paper under `frontend/public/samples/`). The dev server proxies `/api` to the backend (`vite.config.ts`); production web calls the Cloud Run API URL via `VITE_API_BASE_URL` at build time.

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/audits` | Upload PDF, start audit (202) |
| `GET` | `/api/audits/{id}` | Audit result |
| `GET` | `/api/audits/{id}/events` | SSE live resolution log |
| `GET` | `/api/audits/{id}/events/history` | JSON event history (past audits) |
| `POST` | `/api/audits/doi` | Verify a single DOI |
| `GET` | `/api/audits/{id}/report.txt` | Plain-text audit summary |
| `GET` | `/api/audits/{id}/report.json` | JSON audit export |
| `GET` | `/api/audits/{id}/report.pdf` | PDF audit export |
| `POST` | `/api/audits/url` | Audit paper from arXiv/DOI/PDF URL |
| `POST` | `/api/audits/bulk` | ZIP of PDFs (async bulk job) |
| `GET` | `/api/bulk/{id}` | Bulk job status |
| `GET` | `/api/bulk/{id}/dashboard` | Bulk papers ranked by failure rate |
| `GET` | `/api/bulk/{id}/audits` | Full audit results for each paper in batch |
| `GET` | `/api/bulk/{id}/events` | SSE live log for bulk job progress |
| `GET` | `/api/bulk/{id}/events/history` | JSON event history for bulk job |
| `GET` | `/api/audits/{id}/events/log.txt` | Download resolution event log |
| `GET` | `/api/admin/rate-limits` | API usage vs daily budgets |
| `GET` | `/api/admin/config` | Integration feature flags |
| `GET` | `/api/admin/corrections` | Recent user intent/claim corrections (ground truth) |
| `GET` | `/api/health` | Basic health check |
| `GET` | `/api/health/detailed` | Postgres, Redis, GROBID (or skipped), Celery queue/heartbeat/inspect, `file_storage_backend` |
| `GET` | `/api/audits` | List all audits |
| `GET` | `/api/audits/summaries` | Indexed audit list (Postgres summaries table) |
| `PATCH` | `/api/audits/{id}/citations/{cid}/intent` | Reclassify citation intent • reruns NLI |
| `PATCH` | `/api/audits/{id}/citations/{cid}/claim` | Correct extracted claim • reruns NLI |
| `POST` | `/api/audits/{id}/citations/{cid}/rerun-nli` | Rerun claim alignment (NLI only) |
| `POST` | `/api/audits/{id}/citations/{cid}/rerun` | Re-resolve one citation |
| `POST` | `/api/audits/{id}/citations/{cid}/approve-claim` | Run NLI after claim approval |
| `DELETE` | `/api/audits/{id}` | Remove audit and indexed rows |
| `GET` | `/api/admin/corrections/export.csv` | Ground-truth corrections as CSV |
| `GET` | `/api/bulk/{id}/events/log.txt` | Bulk job event log download |
| `GET` | `/api/bulk/{id}/dashboard.json` | Bulk dashboard JSON export |
| `GET` | `/api/audits/{id}/citations/{cid}/attempts` | Resolution attempts from relational DB |
| `GET` | `/api/audits/{id}/paper.pdf` | Source PDF for paper anatomy overlay view |

## Implementation status (v1)

End-to-end flow is implemented: upload (or DOI/URL) → multi-source resolution with throttling → intent + claim extraction → heatmap and side-by-side viewer → TXT/JSON/PDF exports. Defaults match [docs/configuration.md](docs/configuration.md).

| Area | Shipped in this repo |
|------|----------------------|
| Ingestion | PyMuPDF bibliography + inline markers; optional GROBID; `ENABLE_LLM_PDF_INGESTION=false` by default |
| Resolution | CrossRef, Semantic Scholar, OpenAlex, Unpaywall, Europe PMC REST, arXiv; Exa weak signal; Firecrawl abstracts; optional Apify arXiv/ISSN fallbacks |
| Throttling | Per-provider intervals and concurrency in `rate_limits.py`; daily budgets exposed in admin API |
| Verdicts | Hallucination types 1–7, retraction, version mismatch timeline, coverage/risk, NLI with optional claim approval |
| UI | SSE activity log, D3 heatmap, paper anatomy (pdf.js), bulk ZIP dashboard, past audits, sample PDF try/download |
| Background work | Celery on `audits-production` / `audits-development`; Redis worker heartbeat; API falls back to BackgroundTasks only when no worker |
| Persistence | Postgres audit JSON + summaries; GCS (`FILE_STORAGE_BACKEND=gcs`) for uploads on Cloud Run |
| Deploy | `deploy/cloudrun/` → `papyrus-api`, `papyrus-worker`, `papyrus-web` on GCP project `papyrus-audit` |

**Not implemented (by design for v1):** Author Ghost, DOAJ Journal Phantom, circular citation analysis — see [papyrus-spec.md](./papyrus-spec.md).

Full architecture and taxonomy: [papyrus-spec.md](./papyrus-spec.md).

### Tests

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest tests/ -q
```
