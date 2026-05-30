# Papyrus

Citation integrity audit pipeline — verifies that references exist, classifies failure modes, and scores evidentiary claim alignment.

Papyrus does **not** detect AI authorship. It audits the reference layer.

## Stack

- **Backend:** FastAPI, Redis cache, Celery (bulk stub), GROBID + PyMuPDF ingestion
- **Resolution:** CrossRef, Semantic Scholar, OpenAlex (Exa/Apify hooks planned)
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

## Implementation status (v1 slice)

- [x] PDF ingestion (GROBID + PyMuPDF fallback)
- [x] Intent heuristics + optional DeepSeek classification
- [x] Multi-source resolution (CrossRef → S2 → OpenAlex)
- [x] Unpaywall OA lookup, arXiv metadata, Exa weak-signal (never a verdict)
- [x] Types 1, 2, 5, 6, 7 stub, retraction, version mismatch (preprint vs published)
- [x] Evidence passage retrieval (lexical + optional OpenAI embeddings)
- [x] Coverage + risk scoring, JSON/TXT reports, disk persistence
- [x] SSE live panel + heatmap UI (DOI verify, filters, claim rerun)
- [x] Europe PMC biomedical lookup
- [x] NLI via Hugging Face Inference API (fallback: lexical heuristic)
- [x] Bulk ZIP queue, URL ingestion (arXiv + direct PDF)
- [x] PDF export report
- [x] PostgreSQL persistence (`PERSISTENCE_BACKEND=json|postgres|both`)
- [x] Firecrawl landing-page abstract fallback
- [x] Open-access full-text PDF fetch for Tier 1 evidence
- [x] CrossRef DOI content negotiation
- [x] Bulk dashboard + paper anatomy view
- [ ] Apify actors (arXiv, OpenAlex bulk, Europe PMC scrapers)

See [papyrus-spec.md](./papyrus-spec.md) for the full architecture.
