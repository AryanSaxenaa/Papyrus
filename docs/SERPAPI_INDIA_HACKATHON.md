# SerpApi India Hackathon 2026 — Papyrus submission notes

**Deadline:** 10 October 2026, 23:59 IST  
**Hackathon site:** [SerpApi India Hackathon 2026](https://serpapi.github.io/serpapi-india-hackathon-2026/)

## Track

**Knowledge & Public Interest** (Track 05 — Scholar, research, education)

Papyrus is a **citation integrity** tool for manuscripts: it checks whether references exist, whether they match what the paper claims, and whether evidentiary citations support their claims. SerpApi is **central**, not decorative:

| SerpApi engine | Role in Papyrus |
|----------------|-----------------|
| `google_scholar` | Independent witness: does a similar title exist? |
| `google_scholar_cite` | Canonical citation string vs bibliography (authors/year/venue) |
| `google_scholar_author` | Positive-only: does the author’s Scholar profile list this work? |

All traffic goes through `backend/app/services/serpapi/` (budget, cache, ledger, redaction). The UI shows a **witness matrix**, **per-call receipts**, and an exportable **`papyrus.evidence/1` bundle** with offline `verify.py`.

**One-sided rules:** Scholar hits can corroborate or prevent false “DOI not found” outcomes; misses are **unknown**, never proof of fabrication.

## Hosted demo

- **App:** https://papyrus-production-70fb.up.railway.app/app  
- **Replay / Shepherd mode:** opt-in guided tour loads a real `POST /api/audits/replay/demo-a` audit (recorded fixture + SerpApi-shaped events).  
- **Live mode:** PDF/DOI/URL audits use live Scholar witness when `PAPYRUS_MODE=live` and `SERPAPI_API_KEY` are set (public demo may require `X-Access-Code`).

## Submission checklist (form)

| Field | Suggested answer |
|-------|------------------|
| **Track** | Knowledge & Public Interest |
| **Project existed before hackathon?** | Yes — see [PRE_EXISTING_WORK.md](./PRE_EXISTING_WORK.md); SerpApi Scholar witness, receipts, replay, and Railway deploy are hackathon scope (`git tag pre-hackathon-baseline`). |
| **SerpApi usage** | Scholar engines above; ledger + UI receipts + evidence bundle; eval/replay fixtures in `backend/tests/fixtures/replay/`. |
| **Demo video** | Under 3 minutes, local `make demo` or Railway; show witness matrix, receipt, bundle export, and one live or replay Scholar call path. |

## Why not other tracks?

| Track | Fit |
|-------|-----|
| AI Agents | Papyrus is a pipeline + UI, not a general agent framework. |
| Open-Source Integrations | We integrate SerpApi into an app, not a reusable SDK/plugin. |
| Travel / Commerce | Not the domain. |
| Open Innovation | Possible, but **Scholar + research integrity** matches Knowledge & Public Interest more closely. |
