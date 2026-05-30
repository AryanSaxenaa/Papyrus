# Papyrus

Citation integrity audit pipeline — verifies that references exist, classifies failure modes, and scores evidentiary claim alignment.

Papyrus does **not** detect AI authorship. It audits the reference layer.

## Stack

- **Backend:** FastAPI, Redis cache, Celery (bulk stub), GROBID + PyMuPDF ingestion
- **Resolution:** CrossRef, Semantic Scholar, OpenAlex, Europe PMC, Exa, Apify fallbacks
- **Frontend:** React + Vite + Tailwind (live SSE panel + heatmap)

## Quick start

### 1. Environment

```bash
cp .env.example .env
# Set CROSSREF_MAILTO and OPENALEX_MAILTO to your email
```

### 2. Infrastructure (optional but recommended)

```bash
docker compose up -d postgres redis grobid
```

Full stack (API + UI + worker):

```bash
docker compose up --build api web
```

GROBID needs several GB RAM. Without it, the API falls back to PyMuPDF parsing.

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

Open http://localhost:5173 and upload a PDF.

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/audits` | Upload PDF, start audit (202) |
| `GET` | `/api/audits/{id}` | Audit result |
| `GET` | `/api/audits/{id}/events` | SSE live resolution log |
| `POST` | `/api/audits/doi` | Verify a single DOI |
| `GET` | `/api/audits/{id}/report.txt` | Plain-text audit summary |
| `GET` | `/api/audits/{id}/report.json` | JSON audit export |
| `GET` | `/api/audits/{id}/report.pdf` | PDF audit export |
| `POST` | `/api/audits/url` | Audit paper from arXiv/DOI/PDF URL |
| `POST` | `/api/audits/bulk` | ZIP of PDFs (async bulk job) |
| `GET` | `/api/bulk/{id}` | Bulk job status |
| `GET` | `/api/bulk/{id}/dashboard` | Bulk papers ranked by failure rate |
| `GET` | `/api/bulk/{id}/events` | SSE live log for bulk job progress |
| `GET` | `/api/audits/{id}/events/log.txt` | Download resolution event log |
| `GET` | `/api/admin/rate-limits` | API usage vs daily budgets |
| `GET` | `/api/admin/config` | Integration feature flags |
| `GET` | `/api/admin/corrections` | Recent user intent/claim corrections (ground truth) |
| `GET` | `/api/health/detailed` | Postgres, Redis, GROBID connectivity |
| `GET` | `/api/audits/summaries` | Indexed audit list (Postgres summaries table) |
| `POST` | `/api/audits/{id}/citations/{cid}/rerun` | Re-resolve one citation |
| `POST` | `/api/audits/{id}/citations/{cid}/approve-claim` | Run NLI after claim approval |
| `DELETE` | `/api/audits/{id}` | Remove audit and indexed rows |
| `GET` | `/api/admin/citations/stats` | Cross-audit citation failure rates |
| `POST` | `/api/admin/citations/reindex` | Rebuild citation index from completed audits |

## Implementation status (v1 slice)

- [x] PDF ingestion (GROBID + PyMuPDF fallback)
- [x] Intent heuristics + optional DeepSeek classification
- [x] Multi-source resolution (CrossRef → S2 → OpenAlex)
- [x] Unpaywall OA lookup, arXiv metadata, Exa weak-signal (never a verdict)
- [x] Types 1, 2, 5, 6, 7 (NLI claim alignment), retraction, version mismatch (preprint vs published)
- [x] Evidence passage retrieval (lexical + optional OpenAI embeddings)
- [x] Coverage + risk scoring, JSON/TXT reports, disk persistence
- [x] SSE live panel + heatmap UI (DOI verify, filters, claim rerun)
- [x] Side-by-side claim viewer (context / verdict / evidence drawer)
- [x] Coverage summary chips + heatmap legend + contradiction filter
- [x] Dual-column live panel (event log + resolving stack, citation search)
- [x] Version mismatch timeline (arXiv preprint vs published)
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
- [x] Bulk dashboard inline heatmap expand; optional Celery bulk (`USE_CELERY_BULK=true`)
- [x] Semantic Scholar DOI lookup + abstract enrichment
- [x] SSRN URL ingestion via Firecrawl
- [x] Bulk job ETA (`estimated_seconds_remaining`)
- [x] User correction ground-truth log (Postgres table or `corrections.jsonl`)
- [x] Audit limitations panel (coverage bias, NLI caveats, out-of-scope list)
- [x] Medium-confidence review flag in claim viewer
- [x] OpenAlex DOI lookup + abstract enrichment
- [x] Local NLI via Ollama or sentence-transformers (`NLI_BACKEND`, optional deps)
- [x] Audit summaries index table (Postgres) for fast listing
- [x] Optional claim approval gate before NLI (`NLI_REQUIRES_CLAIM_APPROVAL`)
- [x] Per-citation resolution rerun API
- [x] Risk confidence scoring + detailed health check
- [x] Citation-level Postgres index (`citation_index` table) for analytics
- [x] Past audits panel, heatmap verdict badges, Tier 2 / unresolvable evidence drawers
- [x] Live panel event-type filter; evidence sentence highlight
- [x] Basic pytest suite (`backend/tests/`, `requirements-dev.txt`)
- [x] Delete audit API + past-audits panel with removal
- [x] Cross-audit citation failure analytics (`GET /api/admin/citations/stats`)
- [x] Bulk dashboard pending-paper progress + ETA display
- [x] Evidence provenance chain in claim viewer (tier, source, retrieved time)
- [x] Admin panel (rate limits, integration flags, citation reindex)
- [x] Intent reclassification reruns claim alignment when set to evidentiary
- [x] TXT/PDF reports include evidence provenance and per-source resolution trail
- [x] Apify academic-research MCP actor in title-search fallback chain
- [x] Admin corrections log in UI; Docker Compose `web` service for frontend
- [x] Spec-aligned coverage bar (tiers + confirmed failures + unresolvable)
- [x] Resolution trail in claim viewer centre column; bulk job SSE + failure-type columns

See [papyrus-spec.md](./papyrus-spec.md) for the full architecture.

### Still out of scope / v2

- Full relational audit schema (audit bodies remain JSON blobs; citations indexed separately)
- Circular citation detection (spec § excluded from v1)

### Tests

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest tests/ -q
```
