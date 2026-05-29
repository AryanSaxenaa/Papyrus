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
| `GET` | `/api/audits/{id}/report.txt` | Plain-text audit summary |

## Implementation status (v1 slice)

- [x] PDF ingestion (GROBID + PyMuPDF fallback)
- [x] Intent heuristics (DeepSeek integration point reserved)
- [x] Multi-source resolution (CrossRef → S2 → OpenAlex)
- [x] Types 1, 2, 5, 6, retraction detection
- [x] Coverage + risk scoring
- [x] SSE live panel + heatmap UI
- [ ] Production NLI model + embeddings retrieval
- [ ] Unpaywall / Europe PMC / Exa (signal-only) / Apify actors
- [ ] PostgreSQL persistence + bulk ZIP queue
- [ ] PDF export report

See [papyrus-spec.md](./papyrus-spec.md) for the full architecture.
