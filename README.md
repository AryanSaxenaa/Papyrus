# Papyrus

Citation integrity audit pipeline — verifies that references exist, classifies failure modes, and scores evidentiary claim alignment.

Papyrus does **not** detect AI authorship. It audits the reference layer.

## Stack

- **Backend:** FastAPI, Redis (cache + Celery broker), Celery (async bulk worker), PyMuPDF PDF ingestion (optional GROBID for public beta)
- **Resolution:** CrossRef, Semantic Scholar, OpenAlex, Europe PMC, Exa, Apify fallbacks
- **Frontend:** React + Vite + Tailwind + motion, D3 (heatmap/timeline), pdf.js (paper anatomy)

## Documentation

| Doc | Contents |
|-----|----------|
| [docs/configuration.md](docs/configuration.md) | Env vars: PDF ingestion, LLM backends, NLI, embeddings, Celery |
| [docs/cloudrun-deployment.md](docs/cloudrun-deployment.md) | Cloud Run + Supabase/Redis/GCS (recommended for GCP) |
| [docs/gcp-deployment.md](docs/gcp-deployment.md) | Cloud SQL, VMs, cost options |
| [papyrus-spec.md](./papyrus-spec.md) | Full product architecture (some ingestion details differ from current defaults) |

## Production deployment (Google Cloud Run)

**GCP project:** `papyrus-audit` (display name *Papyrus*). The project ID `papyrus` is not available globally; use `papyrus-audit` in `deploy/cloudrun/.env`.

**External services (not on GCP):** Supabase Postgres (`DATABASE_URL`), Redis Cloud (`REDIS_URL`), optional third-party API keys (DeepSeek, Hugging Face, OpenRouter, Exa, Firecrawl, Apify).

### Live URLs

| Service | URL | Notes |
|---------|-----|--------|
| **Web UI** | https://papyrus-web-694307068650.us-central1.run.app | Static React; `VITE_API_BASE_URL` baked at build time |
| **API** | https://papyrus-api-694307068650.us-central1.run.app | FastAPI on port 8080 |
| **Health** | https://papyrus-api-694307068650.us-central1.run.app/api/health/detailed | Postgres, Redis, Celery worker, GCS mode |
| **Worker** | `papyrus-worker` (private) | Celery; `min-instances=1`; not browser-facing |

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
| Background jobs | Celery | `USE_CELERY_BACKGROUND=true`, needs Redis + worker |

Copy [`.env.example`](.env.example) to `.env` and set resolver mailtos (`CROSSREF_MAILTO`, `OPENALEX_MAILTO`, `UNPAYWALL_EMAIL`).

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

`api` and `worker` load `.env` from the repo root. **GROBID is not started by default.** To enable later:

```bash
docker compose --profile grobid up -d grobid
# Set GROBID_ENABLED=true in .env
```

### Bulk ZIP jobs

`USE_CELERY_BULK` defaults to **true**. The API uses Celery when Redis is up and a worker is listening; otherwise it runs the job in-process via FastAPI `BackgroundTasks` (safe for bare `uvicorn` without a worker). Docker Compose starts the `worker` service automatically.

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

Open http://localhost:5173 and upload a PDF. The dev server proxies `/api` to the backend (`vite.config.ts`); production web calls the Cloud Run API URL via `frontend/src/lib/api.ts` (`VITE_API_BASE_URL`).

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
| `GET` | `/api/health/detailed` | Postgres, Redis, GROBID (or skipped), Celery worker probe, `file_storage_backend` |
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

## Implementation status (v1 slice)

- [x] PDF ingestion — **PyMuPDF default**; optional GROBID (`GROBID_ENABLED`); LLM PDF ingest gated (`ENABLE_LLM_PDF_INGESTION`)
- [x] Intent heuristics + LLM classification (`LLM_BACKEND=deepseek` or `openrouter`)
- [x] Multi-source resolution (CrossRef → S2 → OpenAlex)
- [x] Unpaywall OA lookup, arXiv metadata, Exa weak-signal (never a verdict)
- [x] Types 1, 2, 5, 6, 7 (NLI claim alignment), retraction, version mismatch (preprint vs published)
- [x] Evidence passage retrieval (lexical + Snowflake/OpenAI/OpenRouter embeddings)
- [x] Coverage + risk scoring, JSON/TXT reports; persistence via Postgres + JSON artifacts (`FILE_STORAGE_BACKEND` local or GCS)
- [x] SSE live panel + D3 heatmap (verdict color transitions, filters, claim rerun)
- [x] Side-by-side claim viewer (context / verdict / evidence drawer)
- [x] Coverage summary chips + heatmap legend + contradiction filter
- [x] Dual-column live panel (event log + resolving stack, citation search)
- [x] D3 version mismatch timeline (arXiv preprint vs published)
- [x] PubMed/PMC URL → PDF via Firecrawl landing scrape
- [x] Europe PMC biomedical lookup
- [x] NLI via Hugging Face Inference API (fallback: lexical heuristic)
- [x] Bulk ZIP queue, URL ingestion (arXiv + direct PDF)
- [x] PDF export report
- [x] PostgreSQL persistence (`PERSISTENCE_BACKEND=json|postgres|both`)
- [x] Firecrawl landing-page abstract fallback
- [x] Open-access full-text PDF fetch for Tier 1 evidence
- [x] CrossRef DOI content negotiation
- [x] Bulk dashboard + paper anatomy view
- [x] Apify actor fallback layer (arxiv, OpenAlex, Europe PMC scrapers)
- [x] Rate-limit tracking + admin dashboard endpoint
- [x] CrossRef journal ISSN check for Type 5 (date impossible)
- [x] Type 6 embedding semantic gate (OpenAI) + edit-distance gate
- [x] arXiv revision history + Apify version enrichment for timelines
- [x] DOI URL → Unpaywall open-access PDF before Firecrawl fallback
- [x] Apify CrossRef journals fallback for Type 5
- [x] Spec-aligned TXT report (coverage confidence, claim breakdown, version timeline)
- [x] Coverage bar with confidence note; clickable paper anatomy markers
- [x] Bulk dashboard inline heatmap expand + resolution log; Celery bulk with BackgroundTasks fallback
- [x] Semantic Scholar DOI lookup + abstract enrichment
- [x] SSRN URL ingestion via Firecrawl
- [x] Bulk job ETA (`estimated_seconds_remaining`)
- [x] D3 force-layout citation heatmap (collision + grid targets)
- [x] Celery bulk default on with auto-fallback to BackgroundTasks when no worker/Redis
- [x] User correction ground-truth log (Postgres table or `corrections.jsonl`)
- [x] Audit limitations panel (coverage bias, NLI caveats, out-of-scope list)
- [x] Medium-confidence review flag in claim viewer
- [x] OpenAlex DOI lookup + abstract enrichment
- [x] Local NLI via Ollama or sentence-transformers (`NLI_BACKEND`, optional deps)
- [x] Audit summaries index table (Postgres) for fast listing
- [x] Claim approval gate before NLI (`NLI_REQUIRES_CLAIM_APPROVAL`, default true)
- [x] Per-citation resolution rerun API
- [x] Risk confidence scoring + detailed health check
- [x] Citation-level Postgres index (`citation_index` table) for analytics
- [x] Past audits panel, heatmap verdict badges, Tier 2 / unresolvable evidence drawers
- [x] Live panel event-type filter; evidence sentence highlight
- [x] Basic pytest suite (`backend/tests/`, `requirements-dev.txt`)
- [x] Delete audit API + past-audits panel with removal
- [x] Bulk dashboard pending-paper progress + ETA display
- [x] Evidence provenance chain in claim viewer (tier, source, retrieved time)
- [x] Admin panel (rate limits, integration flags, corrections export)
- [x] Intent reclassification reruns claim alignment when set to evidentiary
- [x] TXT/PDF reports include evidence provenance and per-source resolution trail
- [x] Apify academic-research MCP actor in title-search fallback chain
- [x] Admin corrections log in UI; Docker Compose `web` service for frontend
- [x] D3 coverage bar (tiers + confirmed failures + unresolvable)
- [x] Resolution trail in claim viewer centre column; bulk job SSE + failure-type columns
- [x] Bulk log/JSON export; admin corrections CSV export
- [x] Claim approval before NLI (default on, per spec live panel)
- [x] Snowflake Arctic embedding backend option (`EMBEDDINGS_BACKEND=snowflake`)
- [x] PDF paper anatomy with pdf.js citation badge overlays (`PaperAnatomyView`)
- [x] Type 2 DOI redirect via title drift and exact author-list comparison
- [x] Apify secondary actors: `openclawmara/arxiv-paper-scraper`, `shahidirfan/openalex-scraper`
- [x] Celery bulk queue (`USE_CELERY_BULK=true` in Docker Compose)
- [x] Type 5 volume/year checks (CrossRef DOI metadata + journal volume filter)
- [x] Semantic Scholar arXiv version linking for version mismatch
- [x] OpenAlex ISSN journal catalog verification
- [x] GROBID volume/issue/pages/URL extraction when enabled; three-sentence claim context
- [x] Cloud Run deploy on `papyrus-audit` (`deploy/cloudrun/deploy.ps1` / `deploy.sh`; GCS; no GROBID)
- [x] Celery for single audits and bulk ZIP (`USE_CELERY_BACKGROUND`); Cloud Run worker `min-instances=1`
- [x] Firecrawl + Europe PMC rate limits; `ryanclinton/europe-pmc-search` Apify fallback
- [x] SSE named-event consumer; event history API; bulk expand with resolution log
- [x] Limitations panel always visible; abstract-only + human-review fields in reports

See [papyrus-spec.md](./papyrus-spec.md) for the full architecture.

### Excluded per spec (not implemented)

- **Author Ghost** — high false-positive rate on legitimate first publications and non-Western names.
- **Journal Phantom (DOAJ)** — replaced by CrossRef ISSN + OpenAlex verification.
- **Circular citation analysis** — documented as v2 in spec; excluded from v1.

### Tests

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest tests/ -q
```
