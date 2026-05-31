# Configuration

Copy [`.env.example`](../.env.example) to `.env` at the repo root. Docker Compose `api` and `worker` load this file via `env_file`.

## PDF ingestion (default stack)

| Variable | Default | Purpose |
|----------|---------|---------|
| `GROBID_ENABLED` | `false` | When `true`, try GROBID first; otherwise PyMuPDF only |
| `GROBID_URL` | `http://localhost:8070` | GROBID HTTP API (local profile or external VM) |
| `ENABLE_LLM_PDF_INGESTION` | `false` | LLM full-PDF bibliography parse — **off** until prompts are hardened (hallucination risk) |

**Current production path:** `parse_pdf_fallback` (PyMuPDF) extracts bibliography, inline citations, title, and authors. No LLM is used for PDF structure.

**GROBID later (public beta):** `docker compose --profile grobid up -d grobid`, set `GROBID_ENABLED=true`, point `GROBID_URL` at the service. Cloud Run needs a separate high-memory service (~4 GiB) if you enable it there.

## LLM providers (intent + claims only)

LLMs classify citation intent and extract evidentiary claims. They do **not** replace PyMuPDF for bibliography extraction unless you explicitly enable `ENABLE_LLM_PDF_INGESTION`.

| Backend | Env | Provider | Example models |
|---------|-----|----------|----------------|
| `deepseek` | `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`, `DEEPSEEK_BASE_URL` | [api.deepseek.com](https://api.deepseek.com) | `deepseek-v4-flash`, `deepseek-chat` |
| `openrouter` | `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `OPENROUTER_FALLBACK_MODEL` | [openrouter.ai](https://openrouter.ai) | `openrouter/owl-alpha`, `nvidia/nemotron-3-super-120b-a12b:free` |

Set exactly one active routing path:

```env
LLM_BACKEND=deepseek
DEEPSEEK_API_KEY=...
DEEPSEEK_MODEL=deepseek-v4-flash
ENABLE_DEEPSEEK=true
```

or

```env
LLM_BACKEND=openrouter
OPENROUTER_API_KEY=...
OPENROUTER_MODEL=openrouter/owl-alpha
```

Do **not** assume DeepSeek-hosted models run on OpenRouter unless you set `LLM_BACKEND=openrouter` and pick an OpenRouter model slug.

## NLI and embeddings (Hugging Face)

| Variable | Default | Purpose |
|----------|---------|---------|
| `HUGGINGFACE_API_KEY` | — | Inference API for NLI and Snowflake embeddings |
| `NLI_BACKEND` | `hf` | `hf` \| `auto` \| `ollama` \| `local` \| `lexical` |
| `EMBEDDINGS_BACKEND` | `snowflake` | `snowflake` (HF) \| `openrouter` \| `openai` \| `lexical` |
| `NLI_REQUIRES_CLAIM_APPROVAL` | `true` | Human approval before NLI runs |

## Persistence and background jobs

| Variable | Typical local | Typical Cloud Run |
|----------|---------------|-------------------|
| `DATABASE_URL` | Docker Postgres or Supabase | Supabase / Neon with `?sslmode=require` |
| `PERSISTENCE_BACKEND` | `both` | `postgres` |
| `REDIS_URL` | `redis://localhost:6379/0` or Redis Cloud | Redis Cloud / Upstash |
| `USE_CELERY_BACKGROUND` | `true` | `true` |
| `USE_CELERY_BULK` | `true` | `true` |
| `FILE_STORAGE_BACKEND` | `local` | `gcs` |
| `GCS_BUCKET` | — | Required when `FILE_STORAGE_BACKEND=gcs` |

Initialize Postgres tables once:

```bash
cd backend
python -c "from app.storage.db import init_db; init_db()"
```

## Resolution APIs (direct REST; optional Apify)

| Variable | Purpose |
|----------|---------|
| `CROSSREF_MAILTO` | Polite pool for CrossRef API |
| `OPENALEX_MAILTO` | Polite pool for OpenAlex API |
| `OPENALEX_API_KEY` | Free daily budget on [openalex.org/settings/api](https://openalex.org/settings/api) — use direct `api.openalex.org`, not Apify |
| `UNPAYWALL_EMAIL` | Unpaywall API |
| `EXA_API_KEY` | Optional semantic web search (signal-only; not a sole verdict basis) |
| `FIRECRAWL_API_KEY` | Optional publisher landing-page scrape when DOI metadata lacks abstract |
| `APIFY_API_TOKEN` | Optional; **arXiv metadata and journal ISSN fallbacks only** (no OpenAlex/Europe PMC/MCP actors) |

Europe PMC uses the public REST API at `ebi.ac.uk/europepmc/webservices/rest` (no Apify, no key). arXiv uses `export.arxiv.org`.

## Production (`APP_ENV=production`)

Cloud Run sets `APP_ENV=production`. The app then requires:

- Real `CROSSREF_MAILTO`, `OPENALEX_MAILTO`, `UNPAYWALL_EMAIL` (not `example.com`)
- `GCS_BUCKET` when `FILE_STORAGE_BACKEND=gcs`
- `PERSISTENCE_BACKEND=postgres` or `both` (not `json` alone)
- `DEEPSEEK_API_KEY` if `LLM_BACKEND=deepseek`, or `OPENROUTER_API_KEY` if `openrouter`
- `HUGGINGFACE_API_KEY` if `NLI_BACKEND=hf`

Use `AUDIT_DATA_DIR=/tmp/papyrus-data` on Cloud Run for ephemeral fulltext/correction file cache.

## Docker Compose vs `.env`

Compose still sets **in-container** `DATABASE_URL` and `REDIS_URL` to the bundled `postgres` and `redis` services unless you override them in `.env` (Compose merges `env_file` with `environment`; later keys win depending on version — for remote Supabase/Redis, set those URLs in `.env` and remove or override the compose `environment` block if you need the remote DB exclusively).

Minimal local stack (no GROBID):

```bash
docker compose up -d postgres redis
docker compose up --build api worker web
```

## Health checks

`GET /api/health/detailed` reports Postgres, Redis, and GROBID reachability. With `GROBID_ENABLED=false`, GROBID may show as skipped or unreachable without affecting audits.
