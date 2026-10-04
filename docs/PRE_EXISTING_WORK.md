# Pre-existing work disclosure

Papyrus existed as a public repository **before** the SerpApi India Hackathon submission window. The baseline for hackathon-related changes is tagged locally as **`pre-hackathon-baseline`** (commit `f4909d4` at the time this document was written).

## What was already built

- PDF / DOI / URL / bulk audit pipeline (CrossRef, Unpaywall, Semantic Scholar, OpenAlex, arXiv, Europe PMC, optional Exa/Firecrawl/Apify)
- Claim extraction, evidence passage retrieval, and NLI-based claim alignment
- FastAPI backend, Celery worker, Postgres + Redis persistence, Cloud Run deployment scripts
- React 19 frontend with heatmap, side-by-side drawer, live SSE feed, and report export

## What this hackathon work adds

- Google Scholar witness layer via SerpApi (`google_scholar`, `google_scholar_cite`, `google_scholar_author`)
- SerpApi credit governor, cache, ledger, and UI receipts
- Replay / lite demo mode with recorded cassettes
- Evidence bundle export (`papyrus.evidence/1`) and evaluation harness
- Railway deployment profile and UI “evidence ledger” refresh

## Submission form

**Did this project exist before the hackathon?** Yes.
