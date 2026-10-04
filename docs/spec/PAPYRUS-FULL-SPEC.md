# Papyrus × SerpApi — FULL SPEC PACK

One file for the Cursor agent. Sections are the seven pack files, concatenated unchanged.

## Table of contents

1. `00-README-for-agent.md` — 00 — READ ME FIRST (Cursor agent): **Papyrus × SerpApi**
2. `01-product-spec.md` — 01 — Product Spec: **Papyrus** (existing) → **Papyrus + SerpApi Scholar witness**
3. `02-serpapi-usage.md` — 02 — SerpApi Usage: engines, parameters, credits, caching, fixtures (Papyrus)
4. `03-architecture-and-changes.md` — 03 — Architecture, Data & Change List (Papyrus)
5. `04-ui-design-spec.md` — 04 — UI & Design Spec: Papyrus "Evidence Ledger"
6. `05-readme-and-submission-checklist.md` — 05 — README Skeleton & Submission Checklist (Papyrus)
7. `06-cursor-agent-prompts.md` — 06 — Cursor Agent Prompts (Papyrus) — copy-paste, in order


---

<!-- ===== 00-README-for-agent.md ===== -->

# 00 — READ ME FIRST (Cursor agent): **Papyrus × SerpApi**

You are modifying an **existing, public** repository (`AryanSaxenaa/Papyrus`) so it can be submitted to the SerpApi India Hackathon. This spec pack tells you what the repo already is, what to change, in what order, and what you must never do. It was written from a read of the real repo (README, `papyrus-spec.md`, backend modules, frontend components, deploy files, commit list). Anything not read is marked **VERIFY**.

> Papyrus is **not** new work. It existed before the hackathon. Honesty about that is a hard requirement (see §3). The goal of this pack is to add *meaningful, central, well-evidenced SerpApi usage* and make the whole thing demo-able in under 3 minutes locally and deployable on Railway.

---

## 1. One-paragraph product (target)

**Papyrus** audits the reference list of a PDF manuscript: does each cited work exist, is it the work the manuscript says it is, and does it support the claim it is cited for. After this work, Papyrus adds **Google Scholar, through SerpApi, as an independent witness**: `google_scholar` (does the work exist; who are its authors), `google_scholar_cite` (does Scholar's canonical citation agree with the manuscript's), and `google_scholar_author` (does the named author's public Scholar profile list this work — a **positive-only** signal). Every SerpApi call leaves a receipt (`search_metadata.id`, endpoint, redacted params, credits) shown in the UI and exported in a verifiable evidence bundle. A **replay mode** serves recorded provider responses so a judge can see a complete audit in under 3 minutes with no API keys, no Postgres, no Redis.

## 2. Pack contents (read in this order)

| File | What it gives you |
|---|---|
| `00-README-for-agent.md` | This file: rules, build phases, VERIFY register |
| `01-product-spec.md` | What exists vs target, MVP/stretch, judging mapping, track |
| `02-serpapi-usage.md` | Engines, params, response fields, credits, budget, caching, fixtures |
| `03-architecture-and-changes.md` | Current + target architecture, file-level change list, data model, pipeline, prompts/schemas, tests, eval, Railway spec |
| `04-ui-design-spec.md` | UI refresh (inspiration, tokens, wireframes, components, motion) on the existing React 19 + Tailwind 4 stack |
| `05-readme-and-submission-checklist.md` | README skeleton, disclosures, form answers, judge checklist |
| `06-cursor-agent-prompts.md` | 10 copy-paste prompts with acceptance criteria |
| `PAPYRUS-FULL-SPEC.md` | All of the above in one file |

## 3. Non-negotiable rules

1. **Honest history.** Judges may read the commit history. Therefore:
   - Do **not** rewrite, squash, rebase or force-push existing history. Do **not** backdate commits (no `GIT_AUTHOR_DATE` / `GIT_COMMITTER_DATE` tricks).
   - Before touching code, tag the current head as **`pre-hackathon-baseline`** (the head when this pack was written is commit `f4909d4`, 40 commits — VERIFY it is still the head; if newer commits exist, tag the real head and record its SHA in `docs/PRE_EXISTING_WORK.md`).
   - Every new commit uses a conventional prefix and a scope that makes the new work easy to find: `feat(serpapi): …`, `feat(replay): …`, `chore(railway): …`, `docs: …`. Small commits, one concern each.
   - Commit this spec pack under `docs/spec/` as `docs: add build specification (AI-assisted)`.
2. **Disclose pre-existing work and AI use** — in the README, `docs/PRE_EXISTING_WORK.md`, `AI_USE.md`, and the submission form (texts in `05`). The form asks whether the project existed before the hackathon: the answer is **Yes**.
3. **Original code + license hygiene.** Keep the repo's licence file as is (VERIFY which licence exists; if none, add one only with the owner's decision). Anything adapted from a library or snippet goes in `NOTICE.md`.
4. **No secrets, ever.** Keys are read from environment only. Never commit `.env*`, Cloud Run env files, `deploy/cloudrun/env*` with values, HAR files, or recorded responses containing `api_key=`. Redact `api_key` from every stored URL/param (SerpApi echoes it nowhere in JSON, but your own logs/ledger must not). Run the secret scan (Prompt 1) before every push. A leaked key can disqualify.
5. **Never invent data or metrics.** Every number in README/UI comes from the eval run, the ledger or a fixture. Synthetic test data lives in `tests/fixtures/synthetic/` and carries `"synthetic": true`. The marketing demo preview (`frontend/src/data/demoAudit.ts`, hard-coded sample citations) must be visibly labelled **"Sample data"** — never presented as an audit result.
6. **One-sided evidence rule (the most important product rule).** The original Papyrus spec deliberately excluded an "Author Ghost" check because author disambiguation produces false positives. This work reintroduces it **only as positive evidence**: *"the author's Scholar profile lists this work"* may raise confidence; *"not found"* is shown as **"Unknown — not evidence of fabrication"** and **never** contributes to a failure verdict, risk score or Type-1/Type-2 classification. Same for Scholar existence: a Scholar miss never creates a failure by itself; a Scholar hit may *prevent* a false DOI_404 verdict.
7. **SerpApi budget discipline.** Free plan: 250 searches/month, 50/hour. All SerpApi traffic goes through one module (`backend/app/services/serpapi/`), which enforces a credit cap, hourly bucket, on-disk cache and ledger (spec in `02`). Tests never touch the network.
8. **Everything demoable offline.** `PAPYRUS_MODE=replay` must run the full audit UI with no keys, no network, no Postgres, no Redis, no Celery (spec in `03` §6).
9. **Do not break the live path.** The existing pipeline (CrossRef, Unpaywall, Semantic Scholar, OpenAlex, arXiv, Europe PMC, Exa, Firecrawl, DeepSeek/HF NLI) keeps working. The SerpApi layer is additive and flag-gated (`SERPAPI_ENABLED`).
10. **No dates/timelines in repo docs you write.** Describe order with phases only.

## 4. Build order (phases — do them in order; each ends with green tests and a commit)

| Phase | Name | Outcome (exit criteria in `06`) |
|---|---|---|
| 1 | Baseline & guardrails | Tag `pre-hackathon-baseline`; `PRE_EXISTING_WORK.md`, `AI_USE.md` stubs; secret-scan; spec pack committed |
| 2 | SerpApi client core | `services/serpapi/` (client, cache, ledger, budget, rate bucket, redaction); mocked-transport tests |
| 3 | Scholar witness | `google_scholar` + `google_scholar_cite` resolvers wired into `resolve_record`; schema additions; verdict "veto" rule |
| 4 | Author presence | `google_scholar_author` positive-only signal; UI-ready evidence objects |
| 5 | Cassette / replay mode | HTTP transport abstraction for all providers; `record` and `replay`; fast demo path; offline-safe config |
| 6 | Evidence trail & bundle | `serpapi_calls` table/JSON, API endpoints, `papyrus.evidence/1` bundle + offline verifier |
| 7 | Eval harness | Labelled set, ablation (baseline vs +Scholar), honest metrics page + `docs/EVAL.md` |
| 8 | UI refresh | Evidence ledger UI per `04`; sample-data labelling; replay banner; credits meter |
| 9 | Railway | Dockerfile(s), `railway.json`, volume/Postgres/Redis wiring, health, public-demo guard |
| 10 | Docs & submission | README, disclosures, form answers, final checklist (`05`) |

Stretch items (only after Phase 10 is green): retraction cross-check via `engine=google`, "cited-by" context via `cites`, Scholar `cluster` versions for preprint/published mismatch. See `01` §4.2.

## 5. Repository facts the agent must respect (read from the repo)

- **Backend:** FastAPI 0.115, Python 3.12, SQLAlchemy (sync, psycopg2), Postgres, Redis (cache, pub/sub, Celery broker), Celery 5.4, PyMuPDF, sse-starlette, fpdf2, google-cloud-storage, tiktoken, httpx, pydantic-settings. Layout: `backend/app/{api,db,domain,pipeline,services,storage,text}`, `backend/tests` (≈20 pytest files).
- **Frontend:** React 19, Vite 6, Tailwind v4 (`@tailwindcss/vite`), react-router-dom 7, d3, motion, pdfjs-dist, TypeScript 5.7. `App.tsx` (~29 KB) holds audit state, polls every 2.5 s and consumes SSE.
- **Deploy today:** Cloud Run (`papyrus-api`, `papyrus-worker`, `papyrus-web` nginx) + Supabase Postgres + Redis Cloud + GCS. Scripts in `deploy/cloudrun/`, docs in `docs/cloudrun-deployment.md`, `docs/gcp-deployment.md`. `docker-compose.yml` runs postgres, redis, optional grobid, api (8000), worker, web.
- **Pipeline:** `AuditOrchestrator.run` → parse (PyMuPDF default; GROBID optional) → classify intent → `_resolve_all` (semaphore 2) → `_align_claims` (claims → evidence passage → NLI) → `finalize_scores`. `resolve_record` walks CrossRef → Unpaywall → Semantic Scholar → OpenAlex → arXiv → Europe PMC → title searches → OA full text → Firecrawl → `detect_hallucination` → title-drift → journal/ISSN → version mismatch → Exa weak signal → Type 1 decision. Throttles in `services/rate_limits.py` are why a live audit takes 10–15 minutes **by design**.
- **Taxonomy:** `HallucinationType` (DOI_404=1, DOI_REDIRECT=2, DATE_IMPOSSIBLE=5, TITLE_DRIFT=6, CLAIM_CONTRADICTION=7, RETRACTION, VERSION_MISMATCH, NONE); evidence tiers 1–4; `NliVerdict`; `RiskLevel`.
- **Existing SerpApi use:** none found. No `SERPAPI_API_KEY` in `config.py`.
- **Persistence:** `AuditStore` mixes in-memory dict, JSON blobs in the file store, and Postgres (`PERSISTENCE_BACKEND` json|postgres|both). `get_engine()` returns `None` unless postgres/both.

## 6. VERIFY register (resolve each; record the answer in `docs/DEV_NOTES.md`)

| # | Item | How to resolve |
|---|---|---|
| V1 | Is `f4909d4` still the head of the default branch? | `git log -1` before tagging |
| V2 | Repo licence file present/kind | Look at repo root |
| V3 | Relationship of private `Papyrus-1` to public `Papyrus` (it has an earlier-looking history incl. Cloud Run commits) — was **not** inspected beyond its last commits | Owner decision; do not copy from it without checking licence/secrets |
| V4 | `google_scholar_author` response field names (docs page did not show a sample) | First real call in feasibility test; save the response as a fixture |
| V5 | `author_id` present for which fraction of Scholar results (many authors have no profile) | Feasibility test (`02` §8) |
| V6 | Scholar `result_id` → `google_scholar_cite` works for books/theses | Feasibility test |
| V7 | Whether `google_scholar` returns `publication_info.authors[]` with `author_id` for multi-author lists truncated with "…" | Feasibility test; handle truncation |
| V8 | Hugging Face NLI URL `api-inference.huggingface.co` still serves `cross-encoder/nli-deberta-v3-base` | Hit `/api/health/detailed`; if dead, use `NLI_BACKEND=lexical`/`local` in demos and record outputs in cassettes |
| V9 | `tiktoken` needs a one-time vocabulary download — fails offline | Set `TIKTOKEN_CACHE_DIR` to a committed/baked path or replace with a char-based estimator in replay mode |
| V10 | `relational_audit` / `sync_relational_audits` behaviour when `get_engine()` is `None` | Read the code; add test for json-only mode |
| V11 | Railway: object storage option for PDFs shared by api+worker (volumes can't be shared) | Use Postgres blob store (spec in `03` §3 and §12) unless Railway docs show a bucket product |
| V12 | Railway Postgres/Redis `DATABASE_URL` scheme (`postgresql://` vs `postgres://`) | Normalise in `config.py` (spec in `03` §3 and §12) |
| V13 | Hackathon form: exact wording of the "existed before" and AI-tools fields | Open the dashboard form; adjust `05` §5 |
| V14 | Whether SerpApi grants extra credits for the hackathon | Email draft in `05` §8 (parent routes it; never auto-sent) |
| V15 | `google_scholar` coverage of Indian-journal / non-English references | Eval stratum "regional journals" (`03` §9) |
| V16 | Any large binaries (`frontend/public/images` ≈2.8 MB PNGs) to compress | Optional |
| V17 | Does the event bus / Redis cache degrade gracefully when Redis is absent (needed for lite/replay)? | Read `services/events.py`, `services/cache.py`; add in-memory fallback + test (`test_lite_mode.py`) |
| V18 | Real module paths for the ASGI app (`app.main:app`?) and Celery app (`app.services.worker`?) | Read repo; fix start commands in `03` §12 |

## 7. Definition of done (whole project)

- `docker compose --profile lite up` **or** `make demo` serves the UI; the "Replay a recorded audit" button finishes in under 3 minutes with the SerpApi evidence visible; no keys required.
- A live audit with a key shows SerpApi receipts for each Scholar/cite/author call and respects the credit cap.
- `pytest` green offline; `npm run build` green; eval report generated from fixtures.
- Railway deployment works from `railway.json` + env table in `03` §12; public instance protected from credit drain.
- README, disclosures and `docs/PRE_EXISTING_WORK.md` are accurate; the secret scan is clean.


---

<!-- ===== 01-product-spec.md ===== -->

# 01 — Product Spec: **Papyrus** (existing) → **Papyrus + SerpApi Scholar witness**

## 1. Problem

Reference lists are now routinely polluted by citations that do not exist, point to a different paper than claimed, carry invented authors, or do not support the sentence they are attached to. Reviewers, supervisors and journal editors cannot check dozens of references by hand, and the free scholarly APIs have gaps (books, theses, regional journals, non-DOI references), so naive checkers either miss fakes or raise false alarms on real-but-obscure works.

## 2. What Papyrus is today (from the repo)

| Aspect | Today (baseline) |
|---|---|
| Input | PDF upload, DOI, URL, bulk ZIP |
| Output | Per-citation verdict (hallucination type, evidence tier, NLI verdict, risk), coverage bar, heatmap, side-by-side drawer, report as txt/json/pdf |
| Resolution | CrossRef, Unpaywall, Semantic Scholar, OpenAlex, arXiv, Europe PMC (+ optional Exa, Firecrawl, Apify) with provider throttles |
| Claim alignment | DeepSeek (or OpenRouter) extracts claims; evidence passage by chunking + embeddings or lexical; NLI via Hugging Face (or lexical fallback); human claim approval (`NLI_REQUIRES_CLAIM_APPROVAL=true`) |
| Taxonomy | DOI_404 (1), DOI_REDIRECT (2), DATE_IMPOSSIBLE (5), TITLE_DRIFT (6), CLAIM_CONTRADICTION (7), RETRACTION, VERSION_MISMATCH |
| Honesty features | `AuditLimitations` (unresolvable ≠ failure), tier model, out-of-scope list, "this tool does not detect AI authorship" |
| Infra | FastAPI + Celery worker + Postgres + Redis + GCS on Cloud Run; docker-compose for local |
| Live audit time | 10–15 minutes, by design (rate limits) |
| Known gap | "Author Ghost" excluded in `papyrus-spec.md` because author disambiguation gave false positives |
| SerpApi | none |

## 3. Target product

> **Papyrus checks every citation against several independent witnesses — now including Google Scholar via SerpApi — shows each witness's receipt, and refuses to call something fake on the strength of a missing record.**

### Principles
1. **Witnesses, not oracles.** Each source is a witness with a stated coverage; the UI shows who testified and who was silent.
2. **Silence is not guilt.** Missing in one index → "unknown". A failure verdict needs an affirmative contradiction (e.g. DOI resolves to a different title) or no witness at all *and* explicit Scholar miss, labelled with its limits.
3. **Every claim has a receipt.** `search_metadata.id`, endpoint, redacted params, credits and a raw-response hash for each SerpApi call; archive-link "Verify now" while retained; self-contained export afterwards.
4. **Honest metrics.** Precision/recall/unresolved-rate measured on a labelled set and published with intervals; synthetic fabrications are labelled as synthetic.
5. **Fast to see, slow to be sure.** Replay mode shows a full recorded audit in under 3 minutes; live mode keeps the careful throttled path.

## 4. Features

### 4.1 MVP (P0 = demo-critical)

| ID | Feature | Priority | Notes |
|---|---|---|---|
| F1 | **Scholar existence witness** (`google_scholar`) | P0 | Title(+first-author) query; fuzzy match top-3; stores `result_id`, `cites_id`, cited-by total, authors with `author_id`; can upgrade Tier 4→3; can veto a false DOI_404 |
| F2 | **Citation-string concordance** (`google_scholar_cite`) | P0 | Only for ambiguous matches (title ok, author/year/venue disagree). Compares manuscript reference vs Scholar's canonical APA/MLA string; outputs field-level diff |
| F3 | **Author presence** (`google_scholar_author`) | P0 | Positive-only. If an author profile lists the work (title match) → "Author confirmed on own profile". Else "Unknown". Per-audit author cache |
| F4 | **SerpApi receipts** in the drawer and report | P0 | Badge with `search_metadata.id`, engine, params, credits, cache-hit flag, "open archived search" while ≤31 days |
| F5 | **Credit governor** | P0 | Per-audit cap, monthly hard cap, hourly bucket, live balance from Account API, cost preview before a live run |
| F6 | **Replay mode / fast path** | P0 | Recorded provider responses + recorded LLM/NLI outputs; no throttling; runs lite (no Postgres/Redis/Celery); clearly bannered "Replay of a recorded audit" |
| F7 | **Evidence bundle** `papyrus.evidence/1` | P0 | ZIP with verdicts, raw (redacted) SerpApi JSON, cassette excerpts, manifest, offline `verify` script |
| F8 | **Eval page + `docs/EVAL.md`** | P0 | Ablation: baseline resolvers vs +Scholar on labelled set, with CIs |
| F9 | **UI refresh: evidence ledger** | P0 | Witness matrix, receipts, sample-data labelling (see `04`) |
| F10 | **Railway deployment** | P0 | Lean profile (1 service + Postgres) and Full profile (api+worker+Postgres+Redis) |
| F11 | Public-demo guard | P0 | Live audits behind an access code on the public instance; replay always open |

### 4.2 Stretch (strict order, only after MVP is frozen)

| ID | Feature | SerpApi | Notes |
|---|---|---|---|
| S1 | Retraction cross-check | `engine=google`, `q="<title>" retraction`, organic results from publisher/retraction-database domains | One-sided: a hit raises a "possible retraction — verify" flag, linked; never auto-verdict |
| S2 | Version cluster | `google_scholar` with `cluster=<versions.cluster_id>` | Lists preprint/published versions → feeds existing VERSION_MISMATCH logic with an independent witness |
| S3 | Citing-context | `google_scholar` with `cites=<cites_id>` + `q=` | "Who cites this and in what words" — evidence for contested works |
| S4 | Bulk quota planner | — | Predict credits for a ZIP before running |
| S5 | Reusable module | — | Package `serpapi_scholar_witness` as a standalone Python lib (→ Open-Source Integrations track alt.) |

## 5. User flows

1. **Reviewer, replay** (judge demo): open site → "Replay a recorded audit" → watch citations resolve (events replayed with compressed timing, banner explains) → open citation #N → witness matrix shows CrossRef ✓, OpenAlex ✗, Scholar ✓ (receipt), author profile ✓ → export evidence bundle.
2. **Researcher, live**: upload PDF → cost preview ("~34 SerpApi credits; balance 212") → run → live feed → report with "Unknown" kept distinct from "Failed".
3. **Skeptic**: open a receipt → "Verify now" (archive, if retained) or run `verify` on the bundle offline.

## 6. Success metrics (reported, not promised)

| Metric | Definition | Where |
|---|---|---|
| Unresolved reduction | % of *real* reference entries in the labelled set left at Tier 4 by baseline vs by baseline+Scholar | EVAL |
| False-failure rate | Real citations flagged as failures by baseline vs +Scholar (target: not higher) | EVAL |
| Fabrication catch rate | Synthetic fabricated entries flagged or left unresolved-with-Scholar-miss | EVAL (synthetic, labelled) |
| Author-confirmation rate | % of citations where author presence = confirmed | EVAL |
| Credits per citation | Mean/max SerpApi credits per citation | ledger |
| Replay duration | Wall-clock for the recorded demo audit | measured |
| Live duration | Wall-clock of a live run of the same paper | measured |

## 7. Non-goals

- Detecting AI-written text. Judging scientific correctness. Replacing human review.
- Declaring authorship fraud. Treating Scholar as ground truth.
- Reproducing Google Scholar rankings.

## 8. Originality (be honest)

Citation checkers exist. What is distinctive here: (1) the **witness-matrix model with one-sided rules** (silence ≠ guilt); (2) using **Scholar's canonical citation strings** (`google_scholar_cite`) as a field-level cross-check; (3) a **positive-only author-profile check** that fixes the reason the original spec rejected Author Ghost; (4) **receipts + offline-verifiable bundles** for each SerpApi call; (5) **cassette replay** so a 10–15 minute pipeline is demonstrable in under 3 minutes without hiding the live cost.

## 9. Safety, ethics, legal

- Wording: "could not be corroborated", never "fake" / "fraud" / "fabricated" for a person-facing statement. The internal enum may keep technical names; the UI maps them to neutral phrases.
- A flagged citation is a prompt for human checking. Authors are named only as they appear in the manuscript/Scholar.
- Uploaded PDFs may be unpublished manuscripts → public instance: retention limit, delete button, no PDF text sent to SerpApi (only bibliographic strings: title/author/year). LLM and NLI providers receive manuscript snippets — disclose in README and UI.
- SerpApi/Google content in fixtures is minimal research excerpts of bibliographic metadata; strip thumbnails and long snippets.

## 10. Judging-criteria mapping

| Criterion | How Papyrus answers |
|---|---|
| Idea strength | Fabricated/misattributed citations are a visible, growing integrity problem; clear insight: "missing ≠ fake" |
| Originality | Witness matrix with one-sided rules; Scholar-cite concordance; positive-only author presence; replayable receipts |
| Technical complexity | Multi-provider async pipeline with throttling, NLI, evidence tiers; plus new credit governor, cassette replay, evidence bundle, ablation harness |
| Usefulness | Researchers, reviewers, students; works on a real PDF; honest limits; export report |
| Meaningful SerpApi usage | Three Scholar engines in the core verdict logic (existence veto, field concordance, author presence); not cosmetic: removing SerpApi measurably raises unresolved/false-failure rate (ablation) |

## 11. Track recommendation

- **Primary: Knowledge & Public Interest** (research integrity; public-good framing).
- **Alternative: Open-Source Integrations**, if Phase-10 stretch S5 (standalone `serpapi_scholar_witness` package + adapter docs) is done — but the app is the real value, so prefer Knowledge & Public Interest.
- AI Agents is a poor fit (the pipeline is deterministic with LLM sub-steps, not an agent).

## 12. Product acceptance checklist

- [ ] Replay audit completes in under 3 minutes locally with no keys.
- [ ] Every SerpApi call appears in the UI with its `search_metadata.id`.
- [ ] No verdict in the codebase depends on "author not found" or "Scholar miss" alone.
- [ ] Ablation table exists and is generated by a script from fixtures.
- [ ] Sample/demo data is labelled "Sample data" wherever it appears.
- [ ] README discloses pre-existing work, AI use, and what changed (tag `pre-hackathon-baseline` → HEAD).


---

<!-- ===== 02-serpapi-usage.md ===== -->

# 02 — SerpApi Usage: engines, parameters, credits, caching, fixtures (Papyrus)

Facts below were read from SerpApi's public documentation while writing this pack. Anything not shown on a doc page is marked **VERIFY** — confirm it with the first real call and save that response as a fixture.

## 1. Platform mechanics (apply to every call)

| Topic | Fact |
|---|---|
| Endpoint | `GET https://serpapi.com/search(.json)` with `engine`, engine params and `api_key` |
| Official clients | Python: PyPI **`serpapi`** (official client; Python ≥ 3.6). Node: npm `serpapi`. Older `google-search-results` package also exists. Agent helper: `serpapi-search-tools` (recommended by organisers for agent track). Papyrus is Python → use `serpapi` behind a thin wrapper, with `httpx` fallback if a feature is missing (note in `DEV_NOTES.md`) |
| Credits | Only **successful, non-cached** searches count. Cached repeats (SerpApi cache lifetime 1 hour) are free. `no_cache=true` forces a live fetch and bypasses the free cache. `async` cannot be combined with `no_cache` |
| Free plan | **250 searches/month**, **50/hour** |
| Account API | `GET /account?api_key=…` — free; use for live balance |
| `search_metadata` | `id`, `status`, `json_endpoint`, `created_at`, `processed_at`, `raw_html_file`, `total_time_taken` — store `id` and `json_endpoint` for every call |
| Archive API | `GET /searches/{search_metadata.id}.json?api_key=…` — retained **31 days**; expired → HTTP 410 |
| Output | `output=json` (default) / `html` / `md`; `json_restrictor` trims fields (syntax: see Mirror pack `02` §1 or SerpApi docs) |
| Errors | 401 invalid key; 429 hourly limit or out of searches (distinguish by message — VERIFY exact text); 5xx transient → one backoff retry; other 4xx → never retry |
| Hackathon | Each valid submission receives 1,000 credits **after** judging — it does not help during development. Contact for credits: hackathon organiser (see `05` §8) |

## 2. Engines used

### 2.1 `google_scholar` — existence witness (MVP, F1)

| Item | Value |
|---|---|
| Params used | `engine=google_scholar`, `q`, `hl=en`, `num=5` (range 1–20), `as_sdt=0` (excludes patents; `7` includes patents, `4` case law), optional `as_ylo`/`as_yhi` (year window = cited year ±1), optional `author:` operator inside `q` |
| Query templates | **T1** `"<title>"` (quoted, truncated to 200 chars); **T2** `"<title>" author:"<first author surname>"` when T1 returns > 3 near ties; **T3** DOI string as `q` when no title (Scholar often indexes DOI text — VERIFY) |
| Response fields used | `organic_results[]`: `title`, `result_id`, `type`, `link`, `snippet`, `publication_info.summary`, `publication_info.authors[]{name, link, author_id, serpapi_scholar_link}`, `inline_links.serpapi_cite_link`, `inline_links.cited_by{total, cites_id}`, `inline_links.versions{total, cluster_id}`, `inline_links.related_pages_link`; `search_information.total_results` |
| Credits | 1 per uncached call |
| Notes | `publication_info.summary` is a single string like "A Author, B Author - Venue, Year - publisher" → parse authors/year/venue defensively (**VERIFY** format variants incl. truncation with "…"). `link` may be absent for citation-only entries (`type` field) |

**Match rule (deterministic, `scholar_match/1`)**: normalise titles (casefold, strip punctuation/markup, collapse spaces). `title_sim` = max(token-set ratio, normalised edit ratio). Candidate is a **match** if `title_sim ≥ 0.92`; **near** if `0.80 ≤ title_sim < 0.92`; else **miss**. Year tolerance ±1. Author check = surname overlap with parsed `publication_info`. LLM adjudication (`03` §5.2) only when ≥ 2 candidates are `near`/`match` and author/year conflict. Thresholds are starting points → tune on the labelled set and record in `docs/EVAL.md`.

### 2.2 `google_scholar_cite` — canonical citation concordance (MVP, F2)

| Item | Value |
|---|---|
| Params | `engine=google_scholar_cite`, `q=<result_id>` |
| Returns | `citations[]` (MLA, APA, Chicago, Harvard, Vancouver; each `{title, snippet}`) and `links[]` (BibTeX, EndNote, RefMan, RefWorks) |
| Caveat | The export `links` **expire shortly after the search** (docs). Use only the formatted `citations[].snippet` strings; do not store or follow the link URLs |
| Use | Parse the APA (or MLA) snippet → authors, year, title, venue; compare with the manuscript entry **field by field**: `authors_ok`, `year_ok`, `venue_ok`. Output is a concordance object, not a verdict |
| When called | Only for `near` matches or `match` with author/year disagreement; max 1 per citation → budget ≈ 25 % of citations |
| Credits | 1 |

### 2.3 `google_scholar_author` — author presence (MVP, F3, positive-only)

| Item | Value |
|---|---|
| Params | `engine=google_scholar_author`, `author_id` (required; **from the `google_scholar` result's `publication_info.authors[].author_id`**), `hl=en`, `sort=pubdate`, `num=100` (max 100), optional `start` |
| Returns | Author's article list, citation totals, cited-by table, co-authors. Exact response keys were **not shown on the doc page → VERIFY (V4)**; wrap in an adapter `parse_author_articles()` with a defensive key search (`articles`, `cited_by`, `co_authors`) and fixture-driven tests |
| Use | Does the profile list a work with `title_sim ≥ 0.90` to the cited title? → `author_presence = confirmed` (with the profile's matching entry as evidence). Otherwise `unknown` |
| Rule | **Never** emit a negative. `unknown` = "profile absent, private, truncated, or work not listed". The author list is capped at `num=100` per call; additional pages only in stretch |
| Which author | First author with an `author_id`; at most 1 author per citation; per-audit cache keyed by `author_id` (same author across citations = 1 credit) |
| Credits | 1 per distinct author per audit |

### 2.4 `google_scholar_profiles` — **DISCONTINUED. Do not use.**

SerpApi's documentation states: "Recent changes by Google Scholar require users to log in" and marks the engine discontinued. Author discovery in Papyrus therefore relies on `author_id` values returned inside `google_scholar` results (or an `author:"Name"` query in `google_scholar`). Mention this in the README so judges see it was a deliberate, researched choice.

### 2.5 Stretch engines

| ID | Engine / params | Purpose | Credits |
|---|---|---|---|
| S1 | `engine=google`, `q="<title>" retraction OR retracted`, `gl=us`, `hl=en`, `num=10` | Retraction hint; look for domains in a retraction-source list (publisher notices, retraction databases — maintain `data/retraction-domains.yaml`; **VERIFY** list) | 1 / citation, only for Tier-1/2 resolved works the user selects |
| S2 | `engine=google_scholar`, `cluster=<cluster_id>` | Versions of the same work (preprint vs published) | 1 |
| S3 | `engine=google_scholar`, `cites=<cites_id>`, `q=<keyword>` | Search within citing papers | 1 |

## 3. Where SerpApi sits in `resolve_record` (summary; detail in `03` §4)

```
free resolvers (CrossRef/S2/OpenAlex/arXiv/EuropePMC …)  → ResolvedRecord R0
        │
        ├─ if R0 resolved Tier 1–2 and no mismatch ─────────► (optional) author presence only if enabled-for-all
        │
        └─ if unresolved | Tier 3–4 | mismatch | DOI_404 candidate
                 ▼
          SerpApi google_scholar (T1/T2)  → ScholarEvidence
                 ▼
          if near-match or field disagreement → google_scholar_cite → concordance
                 ▼
          if match → google_scholar_author (first author w/ author_id) → author_presence
                 ▼
          verdict rules (one-sided): Scholar hit may veto DOI_404, upgrade Tier 4→3; Scholar miss never fails
```

Mode switch `SERPAPI_SCOPE`: `residual` (default; only the unresolved/ambiguous set) | `all` (every citation; used for the demo fixtures and eval so the witness matrix is complete) | `off`.

## 4. Credit budget (plan for 250 in a month; hourly cap 50)

Assumptions: demo paper ≈ 25 references; labelled eval set ≈ 60 references. Real counts will differ → the ledger is the truth.

| Purpose | Calls | Credits |
|---|---|---|
| Feasibility test (`§8`): 8 refs × (scholar + cite + author) | ≤ 24 | 24 |
| Record **demo fixture A** (public sample paper `2108.12837v1.pdf`, scope `all`): 25 scholar + ~8 cite + ~12 distinct authors | ≈ 45 | 45 |
| Record **demo fixture B** (a second short paper with 2–3 planted bad refs, scope `all`) | ≈ 30 | 30 |
| **Eval set** (60 refs, scope `all`): 60 scholar + ~15 cite + ~30 authors | ≈ 105 | 105 |
| Retries / re-records / UI screenshots live | — | 20 |
| Stretch S1 on 10 refs | 10 | 10 |
| **Planned total** | | **≈ 234** |
| Reserve | | ≈ 16 |

Hourly cap: 50/hour → record fixtures in several sessions; the client's token bucket (`SERPAPI_MAX_PER_HOUR=40`) sleeps and reports `resume_at` in the UI.
If a month's budget is exhausted, finish with fixtures only — never drop below the reserve in code (`SERPAPI_MONTHLY_HARD_CAP=240`).

**Live-run cost preview** (UI + CLI) = `n_citations × per_citation_estimate` where estimate = 1.0 (scholar) + 0.25 (cite) + 0.5 (author) for `all`; for `residual` it uses last-run residual ratio (default 0.4). Show both expected and worst-case (3 × n).

## 5. Caching

| Layer | Key | Store | TTL |
|---|---|---|---|
| Raw response cache | `sha256(engine + canonical sorted params without api_key)` | `FILE_STORAGE_ROOT/serpapi/raw/<key>.json` (or Postgres `file_blobs`) | infinite for fixtures/eval; 7 days live default (`SERPAPI_CACHE_TTL_HOURS=168`) |
| Author cache | `author_id` | same | per audit + reuse across audits within TTL |
| In-flight dedupe | same key | in-process dict / Redis `SETNX` | duration of call |
| SerpApi-side cache | — | SerpApi | 1 hour, free. Do **not** use `no_cache=true` except for the feasibility test and fixture recording where fresh output is wanted |

Redaction: before writing anything, remove `api_key` from `search_parameters`/URLs. Assert in tests that no stored file contains the key value or the string `api_key=`.

## 6. Ledger (every call, including cache hits)

`serpapi_calls` row/JSONL fields: `call_id`, `audit_id`, `citation_id`, `engine`, `params_redacted`, `search_metadata_id`, `json_endpoint`, `status`, `http_status`, `credits` (0 for cache hit), `cache_hit`, `latency_ms`, `created_at`, `raw_ref`, `sha256_raw`. Totals feed the credits meter (`/api/serpapi/budget`).

## 7. Fixtures and replay

| Item | Rule |
|---|---|
| Layout | `fixtures/<set>/manifest.json`, `fixtures/<set>/serpapi/*.json` (redacted), `fixtures/<set>/providers/*.json` (CrossRef/S2/OpenAlex/… cassettes), `fixtures/<set>/llm/*.json` (recorded DeepSeek/NLI outputs), `fixtures/<set>/events.jsonl` (original pipeline events with relative timings) |
| Freeze script | `python -m scripts.freeze_fixtures --audit <id> --set demo-a` → sanitises (drops `api_key`, thumbnails, long snippets > 300 chars, tracking params), computes SHA-256, writes manifest (`credits_spent`, `recorded_with`: library versions; **no dates** in names) |
| Replay | `PAPYRUS_MODE=replay` → every provider client reads cassettes through the transport layer; unknown request → clear error ("not in fixture"), never a network call |
| Truthfulness | UI banner: "Replay of a recorded audit. The original live run took {{recorded_duration}}; this replay compresses waiting." Show recorded duration from manifest, not an invented one |
| Legal/ethics | Fixtures contain bibliographic metadata and short snippets only; no full-text; no thumbnails |

## 8. Feasibility test (run before building F1–F3 in earnest; ≤ 24 credits)

Pick 8 references from the public sample paper: 3 with DOIs and common venues, 2 books/theses, 1 non-English or regional-journal reference, 2 planted bad references (title one word off; fake author).
For each: run T1 (`google_scholar`), if a candidate exists run `google_scholar_cite`, and if `author_id` exists run `google_scholar_author`.
Record in `docs/FEASIBILITY.md` (real outcomes, no dates):

| Question | Pass | Partial | Fail → action |
|---|---|---|---|
| Does T1 return the correct work in top 3 for ≥ 5/6 real refs? | ≥ 5 | 3–4 → keep, tune thresholds | ≤ 2 → demote Scholar to enrichment; re-scope story |
| Does ≥ 50 % of matches expose an `author_id`? (V5) | yes | 25–50 % → author check stays "bonus" | < 25 % → drop F3 from MVP, keep F1–F2 |
| Does `google_scholar_cite` return all five formats for matches? (V6) | yes | partial → use APA/MLA only | none → drop F2 |
| Do planted bad refs produce `miss` or `near` (not confident false matches)? | yes | 1 false match → raise threshold | both match → reconsider `near` handling |
| Are `google_scholar_author` keys as assumed? (V4) | yes | adapt parser | — |

## 9. Rate limiting & error handling behaviours the UI must show

| Situation | Behaviour |
|---|---|
| Budget cap reached | Remaining citations skip SerpApi; report says "Scholar witness skipped for N citations (credit cap)"; verdicts unchanged from baseline |
| Hourly limit (429) | Pause; show `resume_at`; continue |
| Out of monthly searches (429) | Stop SerpApi; banner; continue baseline |
| 5xx / timeout | One retry with backoff; then mark `fetch_error` for that witness (never a failure verdict) |
| Empty results | `scholar_miss` (neutral) |
| Archive 410 | "Archive expired — use the bundle" |

## 10. What to say in the README endpoint table

See `05` §1. Keep it truthful: list only engines the code actually calls (S1–S3 only if shipped).


---

<!-- ===== 03-architecture-and-changes.md ===== -->

# 03 — Architecture, Data & Change List (Papyrus)

Everything about the **current** system is from reading the repo at commit `f4909d4` (VERIFY it is still head). Paths are relative to the repo root. **Keep what works; add the SerpApi layer behind flags.**

## 1. Current architecture (baseline)

```
Browser (React 19, Vite 6, Tailwind 4)
  App.tsx — upload, poll /api/audits/{id} every 2.5 s, SSE /api/audits/{id}/events
        │
FastAPI (backend/app/api/routes.py, reports.py, admin.py)
  POST /api/audits (pdf | doi | url | bulk zip)   GET /api/audits/{id}[/events|/report.*]
  PATCH citation / rerun   GET /api/health, /api/health/detailed   /admin/*
        │ background_dispatch.py
        ├── USE_CELERY_BACKGROUND=true  → Celery task (Redis broker, queue audits-{APP_ENV}) → worker.py (+ celery_heartbeat.py)
        └── false                       → FastAPI BackgroundTasks (in-process)
        ▼
AuditOrchestrator.run  (backend/app/pipeline/orchestrator.py)
  parse PDF (GROBID optional | PyMuPDF fallback_parser) → records
  classify intent (DeepSeek | heuristic + negation override)
  _resolve_all (Semaphore(2)) → resolve_record(...)
  _align_claims (claim extraction LLM → evidence passage (chunk+embeddings|lexical) → NLI)
  finalize_scores (scoring.py: coverage, failure rate; risk >5/10/20 %)
        │
Services (backend/app/services): crossref, unpaywall, semantic_scholar, openalex, arxiv, europepmc, exa, firecrawl, apify,
  deepseek, openrouter, embeddings, cache (Redis), events (Redis pub/sub + Redis list + Postgres), rate_limits (per-provider ThrottlePolicy + Redis counters),
  http_retry.get_with_throttle (retries 429/5xx ×4), relational_audit, audit_jobs
Storage: store.py AuditStore (in-memory dict + JSON blob in file store + Postgres AuditRecord/summary/relational rows),
         storage/files.py LocalFileStore | GcsFileStore
Postgres tables (db/models.py): audits, audit_metadata, citations, resolution_attempts, audit_events, bulk_jobs, audit_summaries, citation_index, citation_corrections
Deploy: Cloud Run ×3 (api, worker min-instances=1, web nginx) + Supabase PG + Redis Cloud + GCS; docker-compose for local
```

**Why audits are slow:** `rate_limits.py` policies (CrossRef ≈ 0.12 s/call, Semantic Scholar ≈ 1.0 s, arXiv ≈ 3.0 s, plus daily budgets), `Semaphore(2)`, retries, and per-claim NLI network calls.

**Quirks relevant to this work (all VERIFY by reading the code before editing):** `get_engine()` returns `None` unless persistence includes postgres; production config validation requires real mailtos, GCS bucket (if gcs), postgres persistence, LLM key, HF key; `NLI_REQUIRES_CLAIM_APPROVAL=true` pauses before NLI; `tiktoken` used for token counting (network download of vocab on first use); HF inference URL may be legacy.

## 2. Target architecture

```
                  ┌──────────────────────────── Railway project ─────────────────────────────┐
Browser ───────►  │  papyrus (web+api)  FastAPI + built SPA (StaticFiles)   /api/health      │
                  │     │ PAPYRUS_MODE=live|replay|record                                    │
                  │     ├─ AuditOrchestrator (unchanged shape)                               │
                  │     │     └─ resolve_record → [free resolvers] → ScholarWitness (NEW)    │
                  │     ├─ Transport layer (NEW): live | record | replay (cassettes)         │
                  │     ├─ serpapi/ (NEW): client, cache, ledger, budget, bucket, redaction  │
                  │     └─ Evidence API (NEW): /api/audits/{id}/evidence, /bundle, /budget   │
                  │  papyrus-worker (Full profile only) — Celery, same image                 │
                  │  Postgres (plugin) — audits, serpapi_calls, file_blobs …                 │
                  │  Redis (plugin, Full profile only) — Celery broker, cache, pub/sub       │
                  └──────────────────────────────────────────────────────────────────────────┘
Local judge run:  PAPYRUS_MODE=replay, PERSISTENCE_BACKEND=json, USE_CELERY_BACKGROUND=false, no Redis, no keys
```

Design decisions:
1. **One service serves API + SPA** (Starlette `StaticFiles` + SPA fallback) → removes the separate nginx `papyrus-web` service and CORS configuration in the Railway deployment. (Keep the old nginx Dockerfile for the Cloud Run legacy path.)
2. **Two Railway profiles.** *Lean* (default; 1 app service + Postgres; in-process background tasks) and *Full* (adds worker + Redis; Celery as today). Same image, different env/start command.
3. **No shared volume dependency.** Railway volumes attach to a single service and cannot be shared by replicas/other services, but api and worker both need the uploaded PDF → add `PostgresFileStore` (bytea in `file_blobs`) as a third `FILE_STORAGE_BACKEND` (`local|gcs|postgres`). Lean profile may use `local` + a volume instead (VERIFY trade-off: a volume causes brief downtime on redeploy).
4. **SerpApi is a witness, not a gate.** Additive, flag-gated, one-sided.
5. **Transport abstraction** wraps `httpx` for *all* providers so record/replay is uniform (SerpApi, CrossRef, S2, OpenAlex, arXiv, Europe PMC, Unpaywall, Exa, Firecrawl, DeepSeek/OpenRouter, HF NLI/embeddings).

## 3. File-level change list

Legend: **N** new, **M** modify, **R** remove/retire (only in a clearly labelled commit; never rewrite history), **D** docs.

### 3.1 Backend

| Path | Action | Change |
|---|---|---|
| `backend/app/config.py` | M | Add `papyrus_mode`, `serpapi_*` settings (§8), `file_storage_backend` literal gains `postgres`, `database_url` normaliser (`postgres://`/`postgresql://` → `postgresql+psycopg2://`), production validator: SerpApi key required only if `serpapi_enabled and mode=="live"`; `public_demo_mode`, `live_access_code` |
| `backend/app/services/serpapi/__init__.py` | N | Public API: `SerpApiClient`, `ScholarClient` |
| `backend/app/services/serpapi/client.py` | N | `search(engine, params)`; official `serpapi` package behind `Transport`; injects key; redacts; records ledger; handles errors (§02 §9) |
| `backend/app/services/serpapi/budget.py` | N | per-audit cap, monthly hard cap (from ledger + Account API), hourly token bucket, preview |
| `backend/app/services/serpapi/cache.py` | N | raw-response cache (file store / Postgres), key function, TTL |
| `backend/app/services/serpapi/ledger.py` | N | append + query `serpapi_calls` (JSONL fallback in json mode) |
| `backend/app/services/serpapi/scholar.py` | N | `find_work()`, `canonical_citation()`, `author_articles()`; parsers with defensive keys |
| `backend/app/pipeline/scholar_witness.py` | N | Orchestrates T1/T2 → match → cite → author; returns `ScholarEvidence` |
| `backend/app/pipeline/scholar_match.py` | N | deterministic normalisation + similarity + thresholds; LLM adjudication call (§7) |
| `backend/app/pipeline/orchestrator.py` | M | In `resolve_record` (or its caller `_resolve_all`) insert ScholarWitness after free resolvers & before Type-1 decision; record `ResolutionAttempt(source=SERPAPI_*)`; honour `SERPAPI_SCOPE` |
| `backend/app/pipeline/verdicts.py` | M | One-sided rules: `scholar_veto_doi404(evidence)`; `author_presence` never negative; neutral wording keys |
| `backend/app/pipeline/evidence_tier.py` | M | `tier_from_resolved` accepts `scholar_corroborated` → Tier 3 when otherwise Tier 4 (never to Tier 1/2) |
| `backend/app/pipeline/limitations.py` | M | Add notes: Scholar coverage, author-profile coverage, "unknown ≠ failure" |
| `backend/app/pipeline/scoring.py` | M | Report `scholar_witness` counters; ensure unknown/skip do not enter failure rate |
| `backend/app/domain/enums.py` | M | `ResolutionSource` += `SERPAPI_SCHOLAR`, `SERPAPI_SCHOLAR_CITE`, `SERPAPI_SCHOLAR_AUTHOR`; new `WitnessState`, `AuthorPresence` |
| `backend/app/domain/models.py` | M | Add `ScholarEvidence`, `ConcordanceReport`, `SerpApiReceipt`, fields on `CitationRecord` (`scholar`, `receipts[]`) |
| `backend/app/db/models.py` | M | Tables `serpapi_calls`, `file_blobs`; JSON columns on `citations` or reuse payload (VERIFY how payload stored) |
| `backend/app/db/session.py` | M | No change in logic; add `init_db()` call at startup in lite mode (already creates tables) |
| `backend/app/services/transport.py` | N | `Transport` protocol; `LiveTransport(httpx)`, `RecordTransport`, `ReplayTransport`; request fingerprint = method + URL + sorted params + body hash, minus secrets |
| `backend/app/services/http_retry.py` | M | Route through `Transport`; in replay mode skip waits |
| `backend/app/services/rate_limits.py` | M | In replay mode `wait()` is a no-op and counters are not touched |
| `backend/app/services/{crossref,unpaywall,semantic_scholar,openalex,arxiv,europepmc,exa,firecrawl,apify,deepseek,openrouter,embeddings}.py` | M | Replace direct `httpx` use with injected transport (mechanical) |
| `backend/app/pipeline/nli.py` | M | NLI HTTP via transport; `NLI_BACKEND=lexical` for offline (already exists) |
| `backend/app/pipeline/evidence.py` | M | Token counting: guard `tiktoken` (V9) → fallback char/4 estimator in replay |
| `backend/app/services/replay/` | N | `runner.py` (replays `events.jsonl` with compressed timing; emits through the normal event bus), `manifest.py` |
| `backend/app/api/routes.py` | M | `POST /api/audits/replay/{set}`; add `mode` & `credits` to `/api/config` (new route); guard live creation by `public_demo_mode`/access code; static mount |
| `backend/app/api/evidence.py` | N | `GET /api/audits/{id}/serpapi`, `GET /api/audits/{id}/bundle`, `GET /api/serpapi/budget`, `POST /api/serpapi/estimate` |
| `backend/app/api/health.py` (or in routes) | M | Add `serpapi` block to `/api/health/detailed` (enabled, mode, remaining, no key shown) |
| `backend/app/storage/files.py` | M | Add `PostgresFileStore`; keep `LocalFileStore`, `GcsFileStore` (GCS import lazy so `google-cloud-storage` can be optional) |
| `backend/requirements*.txt` / `pyproject` | M | Add `serpapi`; make `google-cloud-storage` optional extra; keep pinned versions |
| `backend/app/main.py` (VERIFY name) | M | Mount SPA static when `SERVE_FRONTEND=true`; startup `init_db` when postgres |
| `backend/scripts/freeze_fixtures.py` | N | Sanitise + write fixtures from a recorded audit |
| `backend/scripts/serpapi_budget.py` | N | Print ledger totals (+ Account API balance when key present) |
| `backend/scripts/secret_scan.py` | N | Regex scan of tracked files, fixtures and bundles |
| `backend/eval/` | N | `labels.jsonl`, `run_eval.py`, `metrics.py`, `README.md` (see §9) |
| `backend/tests/…` | N/M | See §10 |

### 3.2 Frontend

| Path | Action | Change |
|---|---|---|
| `frontend/src/types.ts` | M | `ScholarEvidence`, `SerpApiReceipt`, `WitnessState`, `AuthorPresence` |
| `frontend/src/lib/api.ts` (VERIFY name) | M | Use relative `/api` by default; new endpoints |
| `frontend/src/components/WitnessMatrix.tsx` | N | Per-citation witness dots (see `04`) |
| `frontend/src/components/ReceiptCard.tsx` | N | One SerpApi call receipt |
| `frontend/src/components/CreditsMeter.tsx` | N | Balance, per-audit spend, hourly bucket |
| `frontend/src/components/ReplayBanner.tsx` | N | Shown when `mode=replay` |
| `frontend/src/components/SideBySideDrawer.tsx` | M | Add Witnesses tab + receipts; neutral wording |
| `frontend/src/components/CitationHeatmap.tsx` | M | Add witness ring/glyph; keep d3 layout |
| `frontend/src/components/LivePanel.tsx` | M | Show SerpApi events (`serpapi.call`) |
| `frontend/src/pages/EvalPage.tsx` | N | Metrics from `eval/report.json` |
| `frontend/src/pages/MethodPage.tsx` | N | Plain-language method + limits |
| `frontend/src/data/demoAudit.ts` | M | Label as sample; add `sample: true`; UI shows "Sample data" chip |
| `frontend/src/styles/*` | M | Tokens from `04` (self-hosted fonts via `@fontsource-*`; remove Google Fonts `<link>` for offline) |
| `frontend/public/images/*` | M | Compress large PNGs (optional) |

### 3.3 Deploy & docs

| Path | Action | Change |
|---|---|---|
| `Dockerfile.railway` | N | Multi-stage: node (build SPA) → python (backend + `frontend/dist`) |
| `railway.json` | N | Builder `DOCKERFILE`, `dockerfilePath`, healthcheck `/api/health`, restart policy (§12) |
| `deploy/railway/README.md` | N | Step-by-step, env table, profiles |
| `deploy/cloudrun/**`, `docs/cloudrun-deployment.md`, `docs/gcp-deployment.md` | keep | Mark "legacy path" in a header note; do not delete history |
| `docker-compose.yml` | M | Add profile `lite` (single `app` service, json persistence, replay) |
| `Makefile` | N | `make demo` (replay lite), `make test`, `make eval`, `make freeze` |
| `docs/PRE_EXISTING_WORK.md`, `AI_USE.md`, `NOTICE.md`, `docs/FEASIBILITY.md`, `docs/EVAL.md`, `docs/METHOD.md`, `docs/DEV_NOTES.md` | N | per `05` |
| `.github/workflows/test.yml` | M | Add frontend `npm run build`, secret scan, eval-in-replay |
| `.gitignore` | M | `.env*` (except `.env.example`), `data/`, `backend/.cache/`, `fixtures/**/_raw/` |
| `.env.example` | M | New vars (no values) |

## 4. Pipeline detail — `ScholarWitness`

```python
# pseudocode — pipeline/scholar_witness.py
async def run(record, ctx) -> ScholarEvidence | None:
    if not ctx.settings.serpapi_enabled or not ctx.scope_includes(record): return None
    if not ctx.budget.allow("google_scholar"): return ScholarEvidence.skipped("credit_cap")

    q = build_query(record)                       # T1 title; T2 adds author:"surname" when ties
    resp = await ctx.serpapi.scholar_search(q, year=record.year)   # receipts auto-recorded
    cands = parse_candidates(resp)                # title, result_id, authors[], summary, cited_by, versions
    best, state = match(record, cands)            # deterministic thresholds; LLM only if ambiguous (§7)

    ev = ScholarEvidence(state=state, best=best, receipts=[resp.receipt])
    if state in {"near", "match_field_conflict"} and ctx.budget.allow("google_scholar_cite"):
        cite = await ctx.serpapi.scholar_cite(best.result_id)
        ev.concordance = compare_fields(record, parse_apa_or_mla(cite))
        ev.receipts.append(cite.receipt)
    if state in {"match", "match_field_conflict"} and best.first_author_id and ctx.budget.allow("google_scholar_author"):
        art = await ctx.serpapi.scholar_author(best.first_author_id)   # per-audit cache
        ev.author_presence = "confirmed" if lists_work(art, record.title, 0.90) else "unknown"   # NEVER "absent"
        ev.receipts.append(art.receipt)
    return ev
```

**Integration rules (the one-sided rule set — implement as pure functions with tests):**
1. `scholar_state == match` ∧ baseline would raise `DOI_404` → **veto**: do not emit Type 1; emit `NONE` + note "DOI did not resolve but the work exists in Scholar" and set tier ≥ 3. (If DOI resolves to a *different* title, Type 2 is unaffected.)
2. `scholar_state == miss` ∧ baseline unresolved → keep the baseline verdict/tier; add limitation text "Scholar also returned no match; coverage of Scholar for regional/non-English works is limited". **Do not** raise severity above baseline.
3. `author_presence == confirmed` → badge + may reduce a TITLE_DRIFT "author mismatch" sub-reason into "author listed on profile", never the reverse.
4. `author_presence == unknown` → neutral; excluded from counts of failures.
5. `concordance.field_disagreement` (authors/year/venue) → shown as "Scholar's formatted citation differs in: authors" and counted in a separate `metadata_discrepancy` counter, not in the failure rate, unless it coincides with an existing TITLE_DRIFT/DATE_IMPOSSIBLE verdict.

## 5. Data model

### 5.1 Pydantic (`domain/models.py`)

```python
class SerpApiReceipt(BaseModel):
    call_id: str
    engine: Literal["google_scholar","google_scholar_cite","google_scholar_author","google"]
    params: dict[str, Any]            # redacted, no api_key
    search_metadata_id: str | None
    json_endpoint: str | None
    http_status: int
    credits: int                      # 0 if cache hit
    cache_hit: bool
    latency_ms: int
    created_at: datetime              # from search_metadata.created_at when present; else call time (UTC)
    raw_ref: str                      # path/key of stored redacted JSON
    sha256_raw: str

class ScholarCandidate(BaseModel):
    result_id: str; title: str; link: str | None; summary: str | None
    authors: list[dict]               # name, author_id?
    year: int | None; cited_by: int | None; cites_id: str | None
    versions_total: int | None; cluster_id: str | None; title_sim: float

class ConcordanceReport(BaseModel):
    source_format: Literal["APA","MLA"]
    authors: Literal["agree","disagree","unknown"]
    year: Literal["agree","disagree","unknown"]
    venue: Literal["agree","disagree","unknown"]
    scholar_string: str

class ScholarEvidence(BaseModel):
    state: Literal["match","near","miss","fetch_error","skipped","disabled"]
    skipped_reason: str | None = None
    best: ScholarCandidate | None = None
    concordance: ConcordanceReport | None = None
    author_presence: Literal["confirmed","unknown","not_checked"] = "not_checked"
    author_matched_title: str | None = None
    receipts: list[SerpApiReceipt] = []
```

### 5.2 DB (SQLAlchemy `db/models.py`)

```
serpapi_calls(id PK, audit_id FK, citation_id, engine, params_json, search_metadata_id, json_endpoint,
              http_status, credits, cache_hit, latency_ms, created_at, raw_key, sha256_raw)
file_blobs(key PK, content bytea, content_type, size, created_at)           -- PostgresFileStore
```
`created_at` columns use timezone-aware UTC (`datetime.now(timezone.utc)`) for the new tables (the baseline uses `datetime.utcnow`; do not mass-refactor).

### 5.3 Evidence bundle `papyrus.evidence/1` (ZIP)

```
manifest.json    {schema:"papyrus.evidence/1", audit_id, paper_title, pipeline_version, mode, counts, credits_spent, files:[{path, sha256}]}
verdicts.json    per-citation verdicts, tiers, witness states, rules fired
serpapi/         <call_id>.json (redacted raw)           ledger.jsonl
providers/       cassette excerpts used for verdicts (redacted)
verify.py        stdlib-only: recomputes sha256s, re-applies §4 rules to raw inputs, checks verdict parity, prints PASS/FAIL
README.txt       how to verify; archive IDs list with note: SerpApi archive retains 31 days
```

## 6. Replay / fast path

Goals: complete demo audit < 3 minutes locally without keys/network/Postgres/Redis/Celery, while being truthful that it is a recording.

1. **Recording**: `PAPYRUS_MODE=record` runs a normal live audit; `RecordTransport` stores every request/response (redacted) in `fixtures/_raw/<set>/…` and appends events to `events.jsonl` with `t_rel_ms`. Then `freeze_fixtures` sanitises into `fixtures/<set>/`.
2. **Replay**: `ReplayTransport` answers by fingerprint; LLM/NLI responses are cassette entries too (so DeepSeek/HF keys are unnecessary). Throttle waits skipped. `replay/runner.py` re-emits events through the standard bus with timing compressed by `REPLAY_SPEEDUP` (default 20×; capped so total ≤ ~120 s), flagging `event.replayed=true`.
3. **Lite runtime**: `PERSISTENCE_BACKEND=json`, `USE_CELERY_BACKGROUND=false`, `REDIS_URL` unset. Required reading before editing: how `events.py` and `cache.py` behave without Redis (V17 below) — add an in-memory event bus fallback if absent.
4. **PDF parsing in replay**: either parse the bundled sample PDF with PyMuPDF (offline-capable) or load recorded records from the cassette; choose parse-live-from-bundled-PDF when `fitz` available (demonstrates real parsing), record fallback otherwise.
5. **UI truthfulness**: banner + per-event "replayed" mark; manifest shows recorded wall time.

Add **V17** to the VERIFY register: *does `EventBus`/cache degrade gracefully with Redis absent (history list, SSE)?* (Papyrus-1's commit log mentions event-history 503 handling and Redis timeouts — check the public repo equivalent.)

## 7. LLM prompts & JSON schemas (only one new LLM step)

Existing LLM steps (intent classification, claim extraction) are unchanged; their recorded outputs go into cassettes.

### 7.1 `scholar_match_adjudicator/1` (called only when ≥ 2 candidates are `near`/`match` and author/year conflict)

Backend: the existing `llm.py` dispatcher (DeepSeek or OpenRouter), temperature 0, JSON mode.

```
SYSTEM:
You compare one bibliography entry with up to three Google Scholar result candidates.
Decide whether any candidate is the SAME work as the entry. Use only the text given.
Do not use outside knowledge. If unsure, answer "ambiguous". Never invent fields.
Return JSON only, matching the schema.

USER:
ENTRY: {"title": "...", "authors": ["..."], "year": "<int>", "venue": "..."}
CANDIDATES: [{"index":0,"title":"...","summary":"authors - venue, year - publisher"}, ...]
```

```json
{
  "$id": "scholar_match_adjudicator/1",
  "type": "object",
  "required": ["decision", "chosen_index", "field_agreement", "reasons"],
  "additionalProperties": false,
  "properties": {
    "decision": {"enum": ["same_work", "different_work", "ambiguous"]},
    "chosen_index": {"type": ["integer", "null"], "minimum": 0, "maximum": 2},
    "field_agreement": {
      "type": "object",
      "required": ["authors", "year", "venue"],
      "properties": {
        "authors": {"enum": ["agree", "disagree", "unknown"]},
        "year": {"enum": ["agree", "disagree", "unknown"]},
        "venue": {"enum": ["agree", "disagree", "unknown"]}
      }
    },
    "reasons": {"type": "array", "items": {"type": "string", "maxLength": 200}, "maxItems": 3}
  }
}
```
Validation: parse with Pydantic; on invalid JSON → treat as `ambiguous` (neutral). The deterministic matcher always runs first; the LLM can only move `near`→`match` when `same_work` and cannot create a failure.

### 7.2 No LLM for receipts or summaries
Receipt text, witness labels and limitation notes are template-generated from structured fields.

## 8. Configuration (new env vars; all optional unless stated)

| Var | Default | Meaning |
|---|---|---|
| `PAPYRUS_MODE` | `live` | `live` \| `record` \| `replay` |
| `SERPAPI_ENABLED` | `true` if key present | master switch |
| `SERPAPI_API_KEY` | — | secret; never logged |
| `SERPAPI_SCOPE` | `residual` | `residual` \| `all` \| `off` |
| `SERPAPI_MAX_CREDITS_PER_AUDIT` | `40` | hard stop per audit |
| `SERPAPI_MONTHLY_HARD_CAP` | `240` | refuse live calls above this ledger total |
| `SERPAPI_MAX_PER_HOUR` | `40` | token bucket (plan limit is 50) |
| `SERPAPI_CACHE_TTL_HOURS` | `168` | raw response cache |
| `SERPAPI_NO_CACHE` | `false` | set `no_cache=true` on calls (fixture recording only) |
| `REPLAY_SET` | `demo-a` | fixture set |
| `REPLAY_SPEEDUP` | `20` | event timing compression |
| `PUBLIC_DEMO_MODE` | `false` | `true` on public Railway instance: live audits need code |
| `LIVE_ACCESS_CODE` | — | secret; compared in constant time |
| `SERVE_FRONTEND` | `false` | `true` in Railway image |
| `FILE_STORAGE_BACKEND` | `local` | `local` \| `gcs` \| `postgres` |
| `FILE_RETENTION_DAYS` | `7` | janitor deletes uploads older than this |
| `MAX_UPLOAD_MB` | `25` | upload limit |

## 9. Evaluation (small, honest, labelled)

**Label file** `backend/eval/labels.jsonl` (one JSON per reference):
```json
{"id":"r001","source_paper":"…","raw":"…","title":"…","authors":["…"],"year":"<int>","venue":"…","doi":"…|null",
 "truth":"real|fabricated_synthetic","corruption":"none|title_word|author_swap|year_shift|doi_digit|invented",
 "stratum":"journal_doi|preprint|book_thesis|regional_or_non_english","verified_url":"…|null","verified_by":"human","synthetic":false}
```
Composition (target ≈ 60): 30 real (10 journal+DOI, 8 preprint, 6 books/theses/reports, 6 regional/non-English) — each **hand-verified** against a publisher/library page; 30 `fabricated_synthetic` made by perturbing real entries (label them synthetic everywhere; never describe them as "found in the wild").

**Arms:** A = baseline (`SERPAPI_SCOPE=off`); B = +`google_scholar`; C = B + `google_scholar_cite`; D = C + `google_scholar_author`.
**Metrics (with Wilson 95 % CIs):**
- `unresolved_rate_real` — real refs ending Tier 4 (A vs B).
- `false_failure_rate_real` — real refs with a failure verdict (A vs B; must not increase).
- `fabricated_flag_or_unresolved_rate` — fabricated refs flagged or left unresolved-with-Scholar-miss.
- `metadata_discrepancy_precision` — of refs where cite concordance says "authors disagree", fraction that are truly corrupted (C).
- `author_confirmed_rate_real` (D).
- `credits_per_citation` (ledger), plus per-stratum breakdown (V15).

`python -m eval.run --set labelled-v1 --mode replay --out eval/report.json` generates tables for README and `/eval`. Record cassettes once with live providers + `SERPAPI_SCOPE=all`. If a metric does not improve, publish it anyway and say so.

## 10. Tests

| Test | Type | Notes |
|---|---|---|
| `test_serpapi_client.py` | unit (mock transport) | success, cached (0 credits), 429 hourly, 429 monthly, 5xx retry once, 401, redaction (no key in cache/ledger/log), budget cap refuses N+1 |
| `test_scholar_match.py` | unit | table of 30 title pairs (case, punctuation, subtitle, Unicode, LaTeX) with expected state |
| `test_scholar_parsers.py` | unit | fixtures for `google_scholar`, `_cite`, `_author` (synthetic + one real recorded each); truncation "…" in authors |
| `test_verdict_rules.py` | unit | veto of DOI_404; miss never raises severity; author unknown never counts; concordance counter separate |
| `test_orchestrator_scholar.py` | integration (replay) | tiny cassette → expected verdicts/tier |
| `test_transport_replay.py` | unit | unknown request → error not network; fingerprint stable |
| `test_replay_runner.py` | integration | events emitted in order; total time under bound (with `REPLAY_SPEEDUP`) |
| `test_bundle.py` | integration | build bundle → run `verify.py` → PASS; tamper → FAIL |
| `test_secret_scan.py` | unit | detects `api_key=` and 64-hex; passes on repo fixtures |
| `test_lite_mode.py` | integration | `PERSISTENCE_BACKEND=json`, no Redis → audit completes (V10, V17) |
| `test_config.py` | unit | `postgres://` normalisation; prod validation with/without SerpApi |
| frontend | `npm run build` + `tsc --noEmit`; optional Vitest for `WitnessMatrix` states | no heavy e2e required |

CI never uses the network or secrets.

## 11. Security & abuse (public Railway instance)

- `PUBLIC_DEMO_MODE=true`: `POST /api/audits` (upload/doi/url/bulk) requires header `X-Access-Code` (constant-time compare) **unless** `mode=replay`. Replay endpoints always open.
- Per-IP rate limit (`slowapi` or simple in-memory) on upload endpoints; `MAX_UPLOAD_MB`; reject non-PDF content types and bad magic bytes.
- Redaction of `api_key` in logs; never echo env in `/api/config`; `/admin/*` requires `ADMIN_TOKEN` (VERIFY existing protection).
- CORS: same-origin in Railway image; keep env-driven list for local dev.
- Retention: janitor deletes uploads/blobs after `FILE_RETENTION_DAYS`; "Delete this audit" button.
- Do not send full manuscript text to SerpApi: only title / first-author surname / author_id / result_id.

## 12. Railway deployment spec

### 12.1 Services

| Service | Profile | Source | Start command | Notes |
|---|---|---|---|---|
| `papyrus` | Lean + Full | repo root, `Dockerfile.railway` | `uvicorn app.main:app --host 0.0.0.0 --port ${PORT}` (VERIFY module path) | Serves API + SPA; healthcheck `/api/health` |
| `papyrus-worker` | Full | same repo/image | `celery -A app.services.worker worker -Q audits-production -c 1 --loglevel=info` (VERIFY app path & queue name via `CELERY_AUDIT_QUEUE`) | No public domain; needs same env as api |
| `Postgres` | both | Railway Postgres plugin | — | `DATABASE_URL` reference |
| `Redis` | Full | Railway Redis plugin | — | `REDIS_URL` reference |
| `papyrus-janitor` | optional | same image | `python -m app.scripts.janitor` | Railway cron service (`cronSchedule`; ≥ 5 min apart; must exit when done) |

### 12.2 Build

`Dockerfile.railway` (sketch; adapt to real lockfiles):
```dockerfile
FROM node:22-alpine AS web
WORKDIR /web
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM python:3.12-slim AS app
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libmupdf-dev build-essential && rm -rf /var/lib/apt/lists/*   # VERIFY needed for PyMuPDF wheels
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=web /web/dist /app/static
ENV SERVE_FRONTEND=true STATIC_DIR=/app/static PYTHONUNBUFFERED=1
CMD ["sh","-c","uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
```
Railway builds with the Dockerfile whenever one is present at the configured path. Set `RAILWAY_DOCKERFILE_PATH=Dockerfile.railway` (or `build.dockerfilePath`).

`railway.json` (Config as Code — Railway marks this deprecated in favour of Infrastructure as Code but still supports it for existing services; VERIFY current recommendation when deploying):
```json
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": { "builder": "DOCKERFILE", "dockerfilePath": "Dockerfile.railway" },
  "deploy": {
    "healthcheckPath": "/api/health",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 5
  }
}
```
Healthcheck facts: Railway injects `PORT`; waits for any 2xx; checks only at deploy time (not continuous); healthcheck requests come from host `healthcheck.railway.app` → ensure no host allow-list blocks it.

### 12.3 Variables

Lean profile (set on `papyrus`):
```
APP_ENV=production
PAPYRUS_MODE=live
PUBLIC_DEMO_MODE=true
LIVE_ACCESS_CODE=<secret>
SERVE_FRONTEND=true
DATABASE_URL=${{Postgres.DATABASE_URL}}         # normalised in config.py
PERSISTENCE_BACKEND=postgres
FILE_STORAGE_BACKEND=postgres
USE_CELERY_BACKGROUND=false
USE_CELERY_BULK=false
SERPAPI_API_KEY=<secret>   SERPAPI_SCOPE=residual   SERPAPI_MAX_CREDITS_PER_AUDIT=40   SERPAPI_MONTHLY_HARD_CAP=240
LLM_BACKEND=deepseek  DEEPSEEK_API_KEY=<secret>  DEEPSEEK_MODEL=<model>
NLI_BACKEND=lexical            # or hf with HUGGINGFACE_API_KEY after V8
EMBEDDINGS_BACKEND=lexical     # or snowflake/openrouter with keys
CROSSREF_MAILTO=<real>  OPENALEX_MAILTO=<real>  UNPAYWALL_EMAIL=<real>   # production validator requires non-example values
AUDIT_DATA_DIR=/tmp/papyrus-data
```
Full profile adds: `REDIS_URL=${{Redis.REDIS_URL}}`, `USE_CELERY_BACKGROUND=true`, `USE_CELERY_BULK=true`, and the `papyrus-worker` service with identical variables (use a Railway *shared variable* group to avoid drift).
Railway template syntax is `${{NAMESPACE.VAR}}`, where the namespace is the service name (e.g. `Postgres`, `Redis`).
Private networking: services in the same project reach each other at `<service>.railway.internal`; Postgres/Redis references already carry the right host.

### 12.4 Volumes
Default: **none** (blob store in Postgres; `/tmp` for ephemeral caches). If you prefer disk (`FILE_STORAGE_BACKEND=local`): one volume on `papyrus` mounted at `/data`, `FILE_STORAGE_ROOT=/data/files`. Facts from Railway docs: one volume per service; replicas cannot use volumes; redeploys of a volume-attached service incur brief downtime; Docker images running as non-root may need `RAILWAY_RUN_UID=0`; volume default size is plan-dependent (Hobby 5 GB).

### 12.5 Cost-conscious setup
Railway bills usage (RAM ≈ $10/GB-month, CPU ≈ $20/vCPU-month, volume ≈ $0.15/GB-month, egress ≈ $0.05/GB; Hobby plan has a monthly fee that includes the same amount in usage — VERIFY current numbers on the pricing page). Keep: Lean profile; no GROBID; `uvicorn --workers 1`; no always-on worker; embeddings lexical/remote; image build is free. Free plan limits (0.5 GB RAM) are likely too tight for PyMuPDF + NLI — treat Hobby as the minimum (VERIFY with a trial deploy and the metrics tab).

### 12.6 Judge runs it locally (no keys)
```bash
git clone … && cd Papyrus
cp .env.example .env            # leave keys empty
make demo                       # = docker compose --profile lite up --build   (PAPYRUS_MODE=replay, json persistence)
# or without Docker:
cd backend && pip install -r requirements.txt && PAPYRUS_MODE=replay PERSISTENCE_BACKEND=json USE_CELERY_BACKGROUND=false uvicorn app.main:app --port 8000
cd frontend && npm i && npm run dev     # http://localhost:5173
```
Optional live mode: add `SERPAPI_API_KEY` (and an LLM key); the UI shows a cost preview first.

## 13. Build phases (order only)

1 Baseline & guardrails → 2 SerpApi client core → 3 Scholar witness → 4 Author presence → 5 Transport + replay → 6 Evidence trail & bundle → 7 Eval harness → 8 UI refresh → 9 Railway → 10 Docs & submission. Prompts for each phase: `06`.


---

<!-- ===== 04-ui-design-spec.md ===== -->

# 04 — UI & Design Spec: Papyrus "Evidence Ledger"

Scope: refresh the existing React 19 + Vite 6 + Tailwind v4 (`@tailwindcss/vite`) + react-router 7 + d3 + motion frontend. **No new framework.** Style inspiration only — no assets, code or text copied from the reference sites.

## 1. Inspiration sites (actually fetched while writing this pack)

### 1.1 Primary: **Distill** — https://distill.pub (the "article" layer)
What was observed in the fetched page/markup: a quiet, text-first index of long-form technical articles; each entry = small meta label (date + type such as *Peer-reviewed*, *Commentary*, *Thread*), large title, author line, one-sentence summary. Serif reading fonts declared in CSS (`Georgia`/`HoeflerText`-class stacks) with a monospace for code (`Consolas, Monaco …`); almost no chrome; generous whitespace.
**Borrow (style only):** reading-first typography; meta-label + title + summary rhythm; "figure with caption" and margin-note pattern to place **evidence beside the sentence it supports**.

### 1.2 Secondary: **scite** — https://scite.ai (the "claim ↔ evidence" concept)
Observed copy/structure of the fetched page: "Smart Citations" showing whether a finding has been *supported or contradicted* by later research; "Verifiable Evidence … every answer is grounded in real papers"; "every claim … links back to the specific sentence in the specific paper it came from. You can check the work in one click."
**Borrow (concept only):** a three-way classification vocabulary shown inline next to a citation, and the "one click to the exact sentence" promise → Papyrus' per-citation receipts and the drawer's passage highlighting. Do not copy their branding, colours or wording.

### 1.3 Concept: **"A ledger kept in a reading room."**
The page reads like a typeset manuscript (Distill) with a narrow right-hand **ledger margin** where each citation's witnesses and receipts are written down (scite-style evidence classification). Brand continuity with the current forest-green/mint identity is kept.

## 2. Design tokens

### 2.1 Colour
Existing brand colours (from the repo) are retained as primary: forest `#0a3d2e`, mint `#40916c`, mint-wash `#ecfdf3`, background `#fafafa`.

| Token | Hex | Use |
|---|---|---|
| `--paper` | `#fbfaf7` | manuscript surface |
| `--paper-2` | `#f3f1ea` | ledger margin, cards |
| `--ink` | `#16201c` | body text |
| `--ink-2` | `#4a5750` | secondary text |
| `--rule` | `#d9ddd6` | hairlines |
| `--forest` | `#0a3d2e` | primary, headings, buttons |
| `--mint` | `#40916c` | corroborated (witness filled) |
| `--mint-wash` | `#ecfdf3` | corroborated background |
| `--silent` | `#9aa59f` | witness silent / not checked (hollow ring) |
| `--conflict` | `#b45309` | witness disagrees (metadata discrepancy) |
| `--conflict-wash` | `#fff4e5` | |
| `--fail` | `#9f1239` | affirmative failure verdict (rare) |
| `--fail-wash` | `#fdecef` | |
| `--serp` | `#1d4ed8` | SerpApi receipt accent (small chips only) |
| `--serp-wash` | `#eaf0ff` | |
| `--sample` | `#6b21a8` on `#f5ebff` | "Sample data" chip |

Rules: failure red is reserved for *affirmative* contradictions; "unknown" is always grey, never red or amber. Contrast ≥ 4.5:1 for text (check `--silent` only as non-text indicator).

### 2.2 Typography (self-host via `@fontsource-variable/*`, OFL — required for offline replay)
| Role | Font | Notes |
|---|---|---|
| Display | Playfair Display (existing) | landing hero + section titles only |
| Reading | **Source Serif 4** | manuscript passages, method page, report body (serif reading à la Distill) |
| UI | Plus Jakarta Sans (existing) | buttons, labels, nav |
| Data | IBM Plex Mono (existing) | IDs, params, `search_metadata.id`, DOIs |
Scale (px): 12 / 13 / 15 / 17 (reading) / 20 / 28 / 40 / 64 (hero). Reading line-height 1.65, measure ≤ 68ch.
Remove Google Fonts `<link>`/`@import` (breaks offline). Import fontsource CSS in `main.tsx`.

### 2.3 Shape & space
Radius 6 px (chips 999 px); spacing 4-pt scale; cards: 1 px `--rule`, shadow `0 1px 0 rgba(0,0,0,.04)`; drawer shadow `-12px 0 32px rgba(10,61,46,.08)`.

### 2.4 Tailwind v4 theme (paste into `frontend/src/styles/theme.css`, imported after `@import "tailwindcss";`)
```css
@theme {
  --color-paper: #fbfaf7;
  --color-paper-2: #f3f1ea;
  --color-ink: #16201c;
  --color-ink-2: #4a5750;
  --color-rule: #d9ddd6;
  --color-forest: #0a3d2e;
  --color-mint: #40916c;
  --color-mint-wash: #ecfdf3;
  --color-silent: #9aa59f;
  --color-conflict: #b45309;
  --color-conflict-wash: #fff4e5;
  --color-fail: #9f1239;
  --color-fail-wash: #fdecef;
  --color-serp: #1d4ed8;
  --color-serp-wash: #eaf0ff;
  --font-display: "Playfair Display Variable", serif;
  --font-reading: "Source Serif 4 Variable", Georgia, serif;
  --font-ui: "Plus Jakarta Sans Variable", system-ui, sans-serif;
  --font-mono: "IBM Plex Mono", ui-monospace, monospace;
}
:root { color-scheme: light; }
body { background: var(--color-paper); color: var(--color-ink); font-family: var(--font-ui); }
.reading { font-family: var(--font-reading); font-size: 1.0625rem; line-height: 1.65; max-width: 68ch; }
@media (prefers-reduced-motion: reduce) { * { animation-duration: .01ms !important; transition-duration: .01ms !important; } }
```
(Keep existing utility classes that components use — e.g. `font-audit` — mapped to `--font-mono`; VERIFY class names before removing any style.)

## 3. Signature element: the **Witness Matrix**

A citation is a row of up to 6 "witness dots" in fixed order, each with an accessible label:

`Registry (CrossRef/DOI)` · `Index (S2/OpenAlex)` · `Preprint/PMC (arXiv/EuropePMC)` · `Scholar (SerpApi)` · `Cite concordance (SerpApi)` · `Author profile (SerpApi)`

| State | Glyph | Meaning |
|---|---|---|
| corroborated | ● filled `--mint` | witness found the work / fields agree |
| silent | ○ hollow `--silent` | not found or not checked — **not a failure** |
| conflict | ◐ half `--conflict` | found but a field disagrees |
| failure | ● `--fail` with ✕ | affirmative contradiction (DOI → different title) |
| skipped | ⌀ dashed | not run (credit cap / replay lacks data) |
| error | ⚠ small | provider error |
Hover/focus → tooltip with provider, state, one-line reason, receipt link. SerpApi dots carry a small `--serp` underline.

## 4. Pages & ASCII wireframes (desktop 1280; tablet/mobile rules in §8)

### 4.1 `/` Landing (Paper theme)
```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Papyrus            Method   Evaluation   Evidence   [Replay a recorded audit]  │
├──────────────────────────────────────────────────────────────────────────────┤
│  CITATION AUDIT                                                              │
│  Does every reference                                    ┌─ live preview ──┐ │
│  in this paper exist,                                    │ [1] ● ● ○ ● ◐ ○ │ │
│  and say what it's                                       │ [2] ● ● ● ● ● ● │ │
│  cited for?                                              │ [3] ○ ○ ○ ○ ○ ○ │ │
│                                                          │ [Sample data]   │ │
│  Papyrus asks several independent witnesses —            └─────────────────┘ │
│  including Google Scholar, via SerpApi — and keeps a receipt for each answer.│
│  [Upload a PDF]   [Replay a recorded audit · ≈2 min · no keys]               │
├──────────────────────────────────────────────────────────────────────────────┤
│  Missing ≠ fake        Every answer has a receipt        Measured, not claimed│
│  (one-sided rules)     (search_metadata.id, bundle)       (Evaluation page)   │
├──────────────────────────────────────────────────────────────────────────────┤
│  How it works — 4 steps as figures with captions (Distill-style)             │
└──────────────────────────────────────────────────────────────────────────────┘
```
The hero preview must be tagged **Sample data** (pre-existing `demoAudit.ts`).

### 4.2 `/audit/:id` Audit workspace
```
┌ Header: paper title · mode chip [LIVE|REPLAY] · Credits meter [▮▮▮▯▯ 34/40]  ┐
├───────────────────────────┬──────────────────────────────┬───────────────────┤
│ MANUSCRIPT (reading font) │ CITATION GRID (heatmap)      │ LEDGER MARGIN     │
│ …as shown in prior work   │  cells = citations, ring =   │ Coverage bar      │
│ [12]. However, …[7]       │  worst witness state         │ Witness summary   │
│ (inline chips highlight   │  filter: All · Unknown ·     │ ● 18 corroborated │
│  on hover/selection)      │  Conflict · Failure          │ ○ 5 unknown       │
│                           │                              │ ◐ 2 discrepancies │
│                           │                              │ ✕ 1 failure       │
│                           │                              │ Limitations ▾     │
│                           │                              │ [Export bundle]   │
└───────────────────────────┴──────────────────────────────┴───────────────────┘
Live feed (collapsible bottom): "Scholar · matched #7 (0.96) · receipt a1b2…"
```
Manuscript pane renders text from PyMuPDF (existing `PaperAnatomy`/pdf.js stays as a tab: "PDF view"). Selecting a chip syncs grid and drawer.

### 4.3 Citation drawer (right, 520 px; mobile = bottom sheet)
```
┌ #7  Author et al., <year> ─────────────────────────────── ✕ ┐
│ "Deep metric learning for …"        Tier 3 · Unknown-ish  │
│ ┌ Witness Matrix ─────────────────────────────────────┐   │
│ │ Registry ○  Index ●  Preprint ○  Scholar ●  Cite ◐  Author ●│
│ └─────────────────────────────────────────────────────┘   │
│ Tabs: Verdict | Witnesses | Passage & claim | Receipts    │
│ WITNESSES                                                  │
│  Scholar  match 0.96  "Deep metric learning …" · cited by 412 │
│    receipt ▸ engine google_scholar · id 66f… · 1 credit    │
│  Cite concordance  authors ✓  year ✓  venue ✗ (Scholar says "NeurIPS") │
│  Author profile  Confirmed: profile lists this title       │
│  Note: "Not found" would be shown as Unknown, never a failure. │
│ [Open archived search ↗ (while retained)] [Copy receipt]   │
└────────────────────────────────────────────────────────────┘
```
Passage & claim tab keeps the existing claim/NLI view (manuscript context / verdict / evidence passage) with scite-style labels: *supports · contradicts · neutral · not assessed*.

### 4.4 Receipts tab / `ReceiptCard`
```
┌ SerpApi · google_scholar_author ───────────── 1 credit · live ┐
│ author_id  ••••••••  sort=pubdate num=100   (api_key never shown)│
│ search_metadata.id  6a1f…  [copy] [open archive ↗]  retained: yes │
│ response sha256  9c3e…   raw file ▸ (redacted)                    │
└──────────────────────────────────────────────────────────────────┘
```
Cache hit: chip "cached · 0 credits". Archive link only if the recorded call is within retention (compute from `created_at`; otherwise show "Archive expired — bundle holds the response").

### 4.5 Credits meter (header popover)
```
SerpApi credits   this audit 34 / 40 cap   month 212 / 240 cap   hour ▮▮▮▯▯▯ 18/40
Estimate for next audit: ~30 expected · 75 worst-case          [Run with cap 40]
```
Live balance from Account API when a key exists; replay shows "Replay — no credits spent".

### 4.6 `/eval` Evaluation page
```
Evaluation — labelled set v1 (n=60: 30 real, 30 synthetic fabrications — labelled synthetic)
┌ metric                          A baseline   B +Scholar   C +cite   D +author ┐
│ Unresolved among real refs      {{x}} [CI]   {{y}} [CI]   …                  │
│ False failures among real refs  {{ }}        {{ }}                           │
│ Synthetic fabrications caught   {{ }}        {{ }}                           │
│ Credits per citation (mean/max) —            {{ }}        {{ }}      {{ }}   │
└──────────────────────────────────────────────────────────────────────────────┘
Strata breakdown (journal · preprint · book/thesis · regional) · How labels were made · Limitations
```
Values come from `eval/report.json` — render "no report yet" if absent. Never hard-code numbers.

### 4.7 `/method` (Paper theme, long-form, Distill-like)
Sections: witnesses and their coverage; the one-sided rules (with diagram); what SerpApi calls are made and why; credit policy; limits ("Scholar coverage differs by field and language"); privacy (what leaves your machine); how to verify a bundle.

### 4.8 Replay banner
`REPLAY — you are watching a recorded audit of "{{paper}}". The original live run took {{recorded_duration}}; waiting time is compressed here. No API keys were used.` Sticky, `--serp-wash` background.

## 5. Components

| Component | States | Notes |
|---|---|---|
| `WitnessMatrix` | 6 dots × 6 states, compact (row) / expanded (labelled) | `role="list"`, each dot `role="listitem"` with `aria-label="Scholar: corroborated"` |
| `ReceiptCard` | live, cached, replay, archive-expired, error | copy buttons; params redacted |
| `CreditsMeter` | unknown balance, ok, near cap, capped, replay | never shows key |
| `ReplayBanner` | visible/hidden | |
| `CitationHeatmap` (modify) | existing + witness ring | keep d3 force layout; ring colour = worst *affirmative* state; unknown stays neutral |
| `SideBySideDrawer` (modify) | tabs | keep drawer close/poll fixes |
| `CoverageBar` (modify) | add "unknown" segment distinct from "failed" | |
| `LimitationsPanel` | collapsed/expanded | includes Scholar/author coverage notes |
| `SampleChip` | — | any content from `demoAudit.ts` |
| `EvalTable` | loading, empty, ready | |
| `BundleButton` | idle, building, ready, error | `GET /api/audits/{id}/bundle` |
| `AccessCodeDialog` | closed/open/error | for live runs on the public instance |

## 6. Motion (use the existing `motion` package; CSS where simpler)

| Moment | Spec |
|---|---|
| Witness resolves | dot scale 0.6→1, 160 ms ease-out; filled colour fades in 120 ms; one 400 ms ring pulse for SerpApi dots only |
| Citation row arrives | y +6→0 and opacity 0→1, 180 ms; stagger 40 ms, cap total 600 ms |
| Drawer open/close | translateX 24→0, 200 ms; backdrop fade 150 ms |
| Receipt appears | height auto-animate 160 ms |
| Replay | events replayed at `REPLAY_SPEEDUP`; no extra theatrics |
| Reduced motion | all of the above become instant state changes |

## 7. Accessibility
- Never encode state by colour alone (glyph + label). Keyboard: arrow keys move across heatmap cells, `Enter` opens drawer, `Esc` closes, `g` toggles grid/list. Focus ring 2 px `--forest`. Drawer traps focus and restores it. Live feed has `aria-live="polite"` (throttled).
- Text alternatives for the heatmap: a table view toggle (list of citations with witness text).

## 8. Responsive
≥1280 three columns; 768–1279 manuscript becomes a tab, ledger margin below grid; <768 single column with bottom-sheet drawer; witness matrix collapses to a count chip ("4/6") with tap-to-expand.

## 9. Microcopy (plain, non-accusatory)
| Context | Copy |
|---|---|
| Silent witness | "No record found here. That tells us about this source's coverage, not about the paper." |
| Author unknown | "Unknown — the profile may not exist or may not list this work. Not evidence of a problem." |
| Veto | "The DOI did not resolve, but Google Scholar lists the work. Marked uncertain, not failed." |
| Failure | "The DOI resolves to a different paper than the one cited." |
| Concordance | "Scholar's formatted citation differs in: authors." |
| Skipped | "Scholar check skipped — credit cap reached for this audit." |
| Sample | "Sample data — not an audit result." |
Avoid: fake, fraud, fabricated, liar, hallucinated (in user-facing UI). Internal enums unchanged.

## 10. Empty / loading / error matrix
| State | Behaviour |
|---|---|
| No audits yet | Landing CTA + replay |
| Audit running | Live feed, skeleton rows, ETA text: "Live audits are throttled to respect provider limits and usually take 10–15 minutes" (existing truth) |
| SerpApi disabled | Matrix shows 3 SerpApi dots as ⌀ "not enabled"; banner link to Method |
| Credit cap | Meter red state, remaining rows ⌀ with reason |
| Network/provider error | ⚠ dot + retry affordance for that witness only |
| Replay fixture missing | Friendly error with `make demo` hint |

## 11. Asset checklist
- Fonts via `@fontsource-variable/{playfair-display,source-serif-4,plus-jakarta-sans}` and `@fontsource/ibm-plex-mono`.
- Logo: keep existing; no new third-party artwork. Compress `frontend/public/images/*`.
- Screenshots for README taken from replay mode only.

## 12. Visual QA checklist
- [ ] No Google Fonts requests (Network tab clean offline).
- [ ] Every state has glyph + text, not colour only.
- [ ] "Unknown" never red/amber.
- [ ] Sample chip on every `demoAudit` surface.
- [ ] Receipt shows `search_metadata.id` for every SerpApi dot.
- [ ] Reduced-motion verified; keyboard path works; 1280 / 768 / 390 widths checked.


---

<!-- ===== 05-readme-and-submission-checklist.md ===== -->

# 05 — README Skeleton & Submission Checklist (Papyrus)

Everything in `{{double braces}}` must be filled with **real, measured values** (from the ledger, eval run, fixtures). Never ship the braces. Never claim anything the repo does not do.

Organiser facts (hackathon site and rules, read while writing): submit through the website after signing in with GitHub; **public repository** with setup instructions; demo = screen recording **under 3 minutes** of the project **running locally** (public/unlisted link; test it in a private window); the form asks for project description + track + **SerpApi usage explanation**, participant details, whether the project **already existed**, and AI tools used; existing projects qualify "when the submitted SerpApi usage is meaningful and the work can be reviewed"; AI use is allowed and does not affect judging; one competitive award per project; up to 3 active projects per account (VERIFY in rules); a leaked API key can disqualify. Contacts: hackathon questions → adarsh@serpapi.com; API support → contact@serpapi.com.

---

## 1. README.md skeleton (replace the top of the existing README; keep its good parts)

````markdown
# Papyrus

**Does every reference in this paper exist — and is it the paper the manuscript says it is?**
Papyrus audits a PDF's citations against several independent witnesses — CrossRef, Semantic Scholar, OpenAlex, arXiv, Europe PMC and, new in this version, **Google Scholar via [SerpApi](https://serpapi.com)** — and keeps a verifiable receipt for every answer.

> Papyrus flags citations for **human review**. It does not detect AI-written text, does not judge scientific correctness, and treats "not found" as **unknown**, never as proof of fabrication.

*Built for the SerpApi India Hackathon · Track: Knowledge & Public Interest · **Pre-existing project, substantially extended — see [Pre-existing work](#pre-existing-work-and-what-is-new).***

![Witness matrix](docs/img/witness-matrix.png)  <!-- real screenshot from replay mode -->

## See it in under 3 minutes (no API keys, no Docker needed beyond one command)
```bash
git clone {{repo-url}} && cd Papyrus
make demo            # docker compose --profile lite up --build  → http://localhost:5173
# click "Replay a recorded audit"
```
Replay mode serves **recorded** provider responses (including recorded SerpApi responses) through the same pipeline and UI. A live audit of the same paper took {{recorded_duration}}; replay compresses the waiting. No keys, Postgres, Redis or Celery are required.

### Live mode (optional; spends your SerpApi credits)
```bash
cp .env.example .env     # add SERPAPI_API_KEY (+ an LLM key for claim extraction)
PAPYRUS_MODE=live SERPAPI_MAX_CREDITS_PER_AUDIT=40 make dev
```
A cost preview is shown before each live audit; a hard credit cap, an hourly limiter and an on-disk cache protect the free plan (250 searches/month, 50/hour).

## What the SerpApi layer does
| SerpApi engine | Parameters | Role in Papyrus |
|---|---|---|
| `google_scholar` | `q` (quoted title; optional `author:`), `hl=en`, `num=5`, `as_sdt=0` | **Existence witness.** Fuzzy-matched; a hit can *veto* a false "DOI not found" verdict and lift evidence tier 4→3; a miss never raises severity |
| `google_scholar_cite` | `q=<result_id>` | **Field concordance.** Compares the manuscript's reference with Scholar's formatted citation (authors/year/venue) |
| `google_scholar_author` | `author_id` (from Scholar results), `sort=pubdate`, `num=100` | **Author presence — positive-only.** "Profile lists this work" raises confidence; absence is *Unknown* |
| `search_metadata` | `id`, `json_endpoint`, `created_at` | Printed on every receipt; stored in evidence bundles |
| Search Archive API | `GET /searches/{id}.json` | "Open archived search" while retained (31 days) |
| Account API | `GET /account` | Credits meter |
| {{stretch engines if shipped: `google` retraction hint; `google_scholar` `cluster` / `cites`}} | | |

`google_scholar_profiles` is **discontinued** by SerpApi, so author discovery goes through `author_id` values in Scholar results.
Credits spent on the shipped fixtures: **{{N}} / 250** (`fixtures/*/manifest.json`).

## Results on a small labelled set (honest, with intervals)
{{table from eval/report.json: unresolved rate, false-failure rate, synthetic fabrications caught, credits per citation; A baseline vs B +Scholar vs C +cite vs D +author}}
The set has {{n_real}} hand-verified real references and {{n_syn}} **synthetic** corruptions made by us (labelled as such). Limitations: {{...}}. Method: [docs/EVAL.md](docs/EVAL.md).

## Architecture
{{paste the target diagram from 03 §2, trimmed}}

## Deploy on Railway
See [deploy/railway/README.md](deploy/railway/README.md). Lean profile: 1 service + Postgres. Full profile adds a Celery worker and Redis. Public instance runs behind an access code for live audits; replay is open.

## Pre-existing work and what is new
Papyrus existed before this hackathon. Baseline: tag `pre-hackathon-baseline` (commit `{{SHA}}`; {{n}} commits). Everything after that tag is new work for the hackathon, in clearly prefixed commits (`feat(serpapi): …`, `feat(replay): …`, `chore(railway): …`, `docs: …`). Full statement: [docs/PRE_EXISTING_WORK.md](docs/PRE_EXISTING_WORK.md). Compare: `git log pre-hackathon-baseline..HEAD --oneline`.

## AI-use disclosure
See [AI_USE.md](AI_USE.md).

## Privacy
Uploaded PDFs may contain unpublished work. SerpApi receives only bibliographic strings (title, first-author surname, ids). LLM/NLI providers, when enabled, receive short manuscript snippets. Public-instance uploads are deleted after {{FILE_RETENTION_DAYS}} days; use the delete button any time.

## Tests & reproducibility
`make test` · `make eval` (offline replay) · `make bundle-verify` · `make freeze` (sanitise a recorded audit into fixtures).

## Licences & credits
{{licence}}. Third-party notices in [NOTICE.md](NOTICE.md). Visual style inspired by Distill (reading layout) and scite (evidence-classification concept); no assets or code copied.
````

### Supporting files
- `docs/PRE_EXISTING_WORK.md` — §2.
- `AI_USE.md` — §3.
- `NOTICE.md` — third-party libs/fonts/licences, design-inspiration statement, fixture provenance.
- `docs/FEASIBILITY.md`, `docs/EVAL.md`, `docs/METHOD.md`, `docs/DEV_NOTES.md` (VERIFY answers), `docs/AI_LOG.md` (milestone → prompt → commit).
- `.env.example` — new vars from `03` §8 with **no values**.

---

## 2. `docs/PRE_EXISTING_WORK.md` (and form text)

```markdown
# Pre-existing work

**Papyrus existed before the SerpApi India Hackathon.** It is a public repository whose first commit is `a21e11c` ("Initial commit") and whose head before hackathon work is `{{SHA}}` (tag: `pre-hackathon-baseline`). At that point it was a citation-integrity audit pipeline (PDF → references → resolution against CrossRef, Unpaywall, Semantic Scholar, OpenAlex, arXiv, Europe PMC → claim alignment with NLI → report), deployed on Google Cloud Run, with no SerpApi integration.

**New for the hackathon (everything after the tag):**
- SerpApi integration: `google_scholar`, `google_scholar_cite`, `google_scholar_author` witnesses, credit governor, ledger, cache.
- Verdict rules that use Scholar evidence one-sidedly (veto of false "DOI not found"; author presence positive-only).
- Record/replay transport layer and a fast demo path that runs without keys or infrastructure.
- Evidence receipts and a verifiable evidence bundle.
- Labelled evaluation set, ablation harness and results page.
- UI refresh (witness matrix, receipts, credits meter, replay banner).
- Railway deployment (replacing the Cloud Run path for the hosted demo; the Cloud Run files remain as a legacy path).

**Not changed in spirit:** the base audit pipeline, the evidence-tier model and the claim-alignment approach.
History is unmodified: no rewriting, no backdating. Use `git log pre-hackathon-baseline..HEAD`.
```

## 3. `AI_USE.md`

```markdown
# AI-use disclosure
**Tools used:** {{Cursor + model name(s) as displayed}} for most code edits and tests; {{assistant(s)}} for research summaries, spec drafting and UI-style research (the spec pack is committed under docs/spec/).
**Runtime LLM use:** an LLM (DeepSeek or OpenRouter, configurable) performs citation-intent classification and claim extraction (pre-existing) and, newly, an optional "Scholar match adjudicator" for ambiguous matches (`scholar_match_adjudicator/1`). Outputs in fixtures are recorded.
**What I did myself:** chose the one-sided evidence rules, designed the evaluation set, hand-verified {{n}} real references, ran the feasibility test with my own SerpApi key, reviewed all AI-written changes, and decided what to include or cut.
**Pre-existing code:** the baseline was written before the hackathon (see docs/PRE_EXISTING_WORK.md); portions of it were AI-assisted as well ({{VERIFY: state honestly}}).
```

## 4. Submission form answers (draft — adapt to the live form; VERIFY field wording)

| Field | Draft answer |
|---|---|
| Project name | Papyrus |
| Track | Knowledge & Public Interest |
| One-line description | Audits a manuscript's citations with several independent witnesses — now including Google Scholar via SerpApi — and keeps a verifiable receipt for every answer; "not found" is shown as unknown, never as fake. |
| Detailed description | (≈150 words) Researchers, reviewers and students need to know whether references exist and match what is claimed. Papyrus parses a PDF, resolves each reference across scholarly registries, then escalates ambiguous or unresolved ones to Google Scholar through SerpApi: existence (`google_scholar`), canonical-citation concordance (`google_scholar_cite`) and a positive-only author-profile check (`google_scholar_author`). Verdict rules are one-sided: a Scholar hit can prevent a false "DOI not found" verdict; a miss never raises severity. Every SerpApi call produces a receipt with `search_metadata.id`; evidence bundles can be verified offline. A replay mode lets anyone see a full audit in under three minutes without keys. We report metrics on a small labelled set with intervals and say where Scholar helps and where it does not. |
| How SerpApi is used | Three Scholar engines sit in the core verdict logic (see README table). Removing SerpApi measurably changes results (ablation in `docs/EVAL.md`). `google_scholar_profiles` is discontinued, so author ids come from Scholar results. Credits: {{N}} spent on fixtures, hard-capped in code. |
| Did the project exist before the hackathon? | **Yes.** Pre-existing public repository (first commit `a21e11c`; baseline tag `pre-hackathon-baseline`). New work: SerpApi layer, replay/fast path, evidence receipts, evaluation, UI refresh, Railway deployment. See `docs/PRE_EXISTING_WORK.md` and `git log pre-hackathon-baseline..HEAD`. |
| AI tools used | {{from AI_USE.md}} |
| Repo URL | {{public URL}} |
| Demo video | {{unlisted link}} — screen recording, local replay run, plus one live SerpApi call {{if keys}} |
| Hosted demo (optional) | {{Railway URL}} — replay open; live audits behind an access code |

## 5. Demo video content (no script; just what must be visible, under 3 minutes)
1. `make demo`, open the app (non-default `PAPYRUS_MODE=replay` visible in the banner).
2. Replay audit → witness matrix filling → open a citation → Scholar receipt with `search_metadata.id`.
3. Show one "Unknown" kept distinct from "Failure", and one veto case.
4. Show credits meter + evaluation page.
5. (If time) a single live call to prove the live path.

## 6. Judge checklist (final gate before submitting)

1. [ ] Repo public; opens in a private window; README opens with the one-liner, the 3-minute run, and the SerpApi table.
2. [ ] `pre-hackathon-baseline` tag exists; no rewritten history; commit prefixes consistent; `git log` tells a coherent story.
3. [ ] Disclosures present: `docs/PRE_EXISTING_WORK.md`, `AI_USE.md`, README sections, form answers.
4. [ ] No secrets: `make secret-scan` clean; `.env*` ignored; fixtures contain no `api_key`; GitHub history grep for key prefixes clean.
5. [ ] Every SerpApi engine in the README table is actually called in code; every listed engine has a fixture or test.
6. [ ] `search_metadata.id` visible in UI for each SerpApi dot.
7. [ ] Non-default parameters visible (`author_id`, `sort=pubdate`, `as_sdt=0`, `num`).
8. [ ] Errors, rate limits and credit cap handled visibly (screens exist).
9. [ ] `pytest` + frontend build green in CI; tests do not need network.
10. [ ] Eval numbers in README match `eval/report.json`; synthetic items labelled; limitations listed.
11. [ ] "Sample data" label on any hard-coded demo content.
12. [ ] Railway instance: healthcheck passes; live audits gated; replay works; retention configured.
13. [ ] Demo video < 3 minutes, shows local run, link tested in private window.
14. [ ] Third-party licences/credits in `NOTICE.md`; design inspiration stated; no copied assets.
15. [ ] Private `Papyrus-1` not referenced in a way that leaks anything; no code copied from it unchecked.

## 7. Risk register for the submission
| Risk | Mitigation |
|---|---|
| Judges see "pre-existing, bolted-on SerpApi" | Make SerpApi change verdicts (veto, concordance) and prove it via ablation; keep disclosure prominent |
| Scholar coverage poor for regional works | Report per-stratum honestly; keep one-sided rules |
| Demo >3 minutes | Replay path, recorded duration disclosed, trimmed fixture (≈25 refs) |
| Credit exhaustion | Hard caps, fixtures, replay |
| Public instance abuse | Access code, rate limits, retention |

## 8. Draft email to organisers (NOT sent — parent must route it through the approval flow)

**To:** adarsh@serpapi.com  **Subject:** Credits question — Papyrus (citation audit, Google Scholar engines)
Hello — I'm entering Papyrus, an existing project I'm extending for the hackathon (disclosed as pre-existing). It will make heavy but cached use of `google_scholar`, `google_scholar_cite` and `google_scholar_author` to build recorded fixtures and a small evaluation set. The free plan's 250 searches/month is tight for this; is it possible to receive additional credits for development, or is post-submission credit the only option? I have a hard cap in code and cache every response. Thank you — Aryan Saxena.


---

<!-- ===== 06-cursor-agent-prompts.md ===== -->

# 06 — Cursor Agent Prompts (Papyrus) — copy-paste, in order

How to use: copy this pack to `docs/spec/` in the Papyrus repo (commit it as "docs: add build specification (AI-assisted)"). Open the repo root in Cursor. Paste **one prompt per session**; let it finish; run the acceptance checks yourself; commit; continue. Each prompt begins with the **Common preamble**.

---

## Common preamble (prepend to every prompt)

```
You are modifying the EXISTING repository "Papyrus" for the SerpApi India Hackathon. The spec pack is in docs/spec/. Read docs/spec/00-README-for-agent.md first, then the files named in this task.

Hard rules:
1. This is pre-existing work. Never rewrite history, never backdate, never squash. Small commits with prefixes: feat(serpapi), feat(replay), feat(eval), feat(ui), chore(railway), test, docs.
2. Never write API keys or tokens into any file. Keys come only from environment via backend/app/config.py. Never log keys. Redact api_key from every stored URL/param. Do not commit .env*, recorded files containing api_key, or deploy env files with values.
3. SerpApi traffic goes ONLY through backend/app/services/serpapi/. Tests never use the network; use the mock/replay transport.
4. One-sided evidence rule: "not found", "author unknown" and "Scholar miss" must never raise severity or count as a failure. Scholar may veto a false DOI_404 and lift evidence tier 4 to 3 only.
5. Do not break the live pipeline. SerpApi is flag-gated (SERPAPI_ENABLED / SERPAPI_SCOPE). Existing tests must keep passing.
6. Do NOT invent data or metrics. Synthetic fixtures live in tests/fixtures/synthetic/ with "synthetic": true. Hard-coded demo content must be labelled "Sample data".
7. Where the spec says VERIFY, read the code or the first real response, implement defensively, and record the answer in docs/DEV_NOTES.md.
8. No dates, deadlines or day-by-day plans in any file you write.
9. After the task: run backend tests (pytest) and frontend build/typecheck, summarise changes, list deviations from the spec and any VERIFY items resolved or still open.
```

---

## Prompt 1 — Baseline, guardrails, secret scan
**Read:** 00 (all), 05 §1–3, 03 §3.3.
**Task:** (1) Confirm the current head and create the annotated tag `pre-hackathon-baseline` locally (do not push tags unless the owner asks; document the command). (2) Create `docs/PRE_EXISTING_WORK.md`, `AI_USE.md`, `NOTICE.md`, `docs/DEV_NOTES.md` (VERIFY register copied from 00 §6), `docs/spec/` copy of the pack. (3) Add `backend/scripts/secret_scan.py` (regexes: `api_key=`, `Bearer `, 32–64 char hex strings, `sk-` prefixes, `SERPAPI_API_KEY=` with a value) scanning tracked files, `fixtures/`, `docs/`; wire into CI and a `make secret-scan` target; update `.gitignore` per 03 §3.3. (4) Add `Makefile` with `test`, `secret-scan`, `demo` (placeholder), `eval` (placeholder). (5) Answer V1, V2, V3, V10, V17, V18 by reading the code and recording findings.
**Acceptance:** secret scan passes on the repo and fails on a deliberately bad temp file (unit test); `pytest` unchanged-green; `docs/DEV_NOTES.md` has answers for the listed VERIFY items; tag exists locally.

---

## Prompt 2 — SerpApi client core
**Read:** 02 §1, §4–§6, §9; 03 §3.1 (serpapi rows), §8, §10.
**Task:** Implement `backend/app/services/serpapi/` (client, cache, ledger, budget, bucket, redaction) using the official PyPI package `serpapi` behind a `Transport` protocol (stub the transport file now if Prompt 5 is not done: define the protocol in `services/transport.py` with a `LiveTransport` only). Features: `search(engine, params)` returns parsed JSON + `SerpApiReceipt`; always stores `search_metadata.id`, `json_endpoint`, status, credits (0 on cache hit), latency, `sha256_raw`; raw-response cache keyed by `sha256(engine+canonical params without api_key)`; ledger (Postgres table `serpapi_calls` when engine exists, else JSONL under `AUDIT_DATA_DIR`); budget gate (per-audit cap, monthly hard cap computed from ledger and optionally the free Account API), hourly token bucket with `resume_at`; error handling per 02 §9 (429 hourly vs monthly by message — VERIFY, one retry for 5xx/timeouts, never retry other 4xx). Add settings to `config.py` (03 §8), `.env.example` entries without values. Add `/api/serpapi/budget` and `/api/serpapi/estimate`.
**Acceptance (mocked transport only):** tests for success, cache hit (0 credits), 429 hourly pause, 429 monthly stop, 5xx single retry, 401, cap refuses call N+1, redaction (assert no stored file/log contains the key or `api_key=`), concurrent identical requests deduped. `ruff`/lint clean. No behaviour change to existing audits when `SERPAPI_ENABLED=false`.

---

## Prompt 3 — Scholar witness (existence + concordance)
**Read:** 02 §2.1–2.2, §3; 03 §3.1, §4, §5.1, §7; 01 §4.1 F1–F2.
**Task:** Implement `services/serpapi/scholar.py` (`find_work`, `canonical_citation`), `pipeline/scholar_match.py` (normalisation, similarity, thresholds from 02 §2.1, deterministic states `match|near|miss`), `pipeline/scholar_witness.py` and the pydantic models (03 §5.1). Wire into `resolve_record` after the free resolvers and before the Type-1 decision, honouring `SERPAPI_SCOPE` and budgets; record a `ResolutionAttempt` with the new `ResolutionSource` values. Implement the one-sided rules in `verdicts.py`/`evidence_tier.py` (03 §4 rules 1, 2, 5). Add `scholar_match_adjudicator/1` (03 §7.1) behind the existing `llm.py` dispatcher; invalid JSON → `ambiguous`. Parsers must tolerate truncated author lists ("…") and missing `link`.
**Acceptance:** `test_scholar_match.py` (≥ 30 title pairs), `test_scholar_parsers.py` (synthetic fixtures, labelled), `test_verdict_rules.py` (veto DOI_404; miss never raises severity; concordance separate counter), `test_orchestrator_scholar.py` (tiny cassette). With `SERPAPI_ENABLED=false` all pre-existing tests still pass unchanged.

---

## Prompt 4 — Author presence (positive-only)
**Read:** 02 §2.3–2.4; 00 §3 rule 6; 03 §4.
**Task:** Implement `google_scholar_author` support: `author_articles(author_id)` with a defensive adapter (V4), per-audit author cache, selection of the first author with an `author_id`, `lists_work()` (title similarity ≥ 0.90), and `author_presence ∈ {confirmed, unknown, not_checked}` — **no negative state exists in the type system**. Add limitation text to `limitations.py`. Extend scoring so `unknown` is excluded from failure counts. Add API fields for the UI.
**Acceptance:** tests prove that no code path maps author-unknown to a failure/risk change (include a property-style test over all enum combinations); author cache saves repeated calls (ledger shows 1 credit for 3 citations by the same author); parser tests on at least one **real recorded** response saved as fixture after the feasibility test (document in `docs/FEASIBILITY.md`).

---

## Prompt 5 — Transport layer, record/replay, lite mode
**Read:** 03 §2, §3.1 (transport rows), §6; 02 §7.
**Task:** Implement `services/transport.py` (`Transport` protocol, `LiveTransport`, `RecordTransport`, `ReplayTransport`, request fingerprint excluding secrets) and migrate all provider clients (CrossRef, Unpaywall, Semantic Scholar, OpenAlex, arXiv, Europe PMC, Exa, Firecrawl, Apify, DeepSeek, OpenRouter, embeddings, HF NLI) to use it mechanically. In replay: skip throttle waits and daily counters. Implement `services/replay/runner.py` (compressed-time event replay through the existing event bus; `event.replayed=true`), `scripts/freeze_fixtures.py` (sanitise: drop `api_key`, thumbnails, snippets > 300 chars; write manifest with `credits_spent`, library versions, **no dates**), and lite mode (`PAPYRUS_MODE=replay`, `PERSISTENCE_BACKEND=json`, `USE_CELERY_BACKGROUND=false`, no Redis; add in-memory event bus/cache fallback if needed — V17; guard `tiktoken` — V9). Add `POST /api/audits/replay/{set}` and `GET /api/config` (mode, serpapi enabled, no secrets).
**Acceptance:** `test_transport_replay.py` (unknown request → explicit error, never network), `test_replay_runner.py`, `test_lite_mode.py` (audit completes with no Redis/Postgres/Celery and no network — assert by monkeypatching sockets to fail). A tiny synthetic cassette set exists for tests; the real recorded demo set is produced later by the owner with their key.

---

## Prompt 6 — Evidence receipts API and bundle
**Read:** 03 §5.3; 02 §6; 01 F4, F7.
**Task:** Implement `api/evidence.py` (`GET /api/audits/{id}/serpapi`, `/bundle`), receipts attached to citations, bundle builder for `papyrus.evidence/1` including stdlib-only `verify.py` (recomputes hashes, re-applies the one-sided rules to raw inputs, compares verdict parity), archive-retention computation (31 days from `created_at`; no hard-coded dates).
**Acceptance:** `test_bundle.py`: build → `verify.py` PASS; tamper a byte → FAIL; bundle contains no `api_key`; receipts list matches ledger totals; archive link hidden when expired.

---

## Prompt 7 — Evaluation harness
**Read:** 03 §9; 01 §6; 02 §8.
**Task:** Implement `backend/eval/` (`labels.jsonl` schema + loader with validation, `run_eval.py`, `metrics.py` with Wilson intervals, arms A–D via `SERPAPI_SCOPE` and feature flags, per-stratum breakdown, report writer `eval/report.json` + `docs/EVAL.md` table generator). Provide a **synthetic mini label set** (≤ 12 rows, `synthetic: true`) so tests run; leave a documented procedure and a template file for the owner to add hand-verified real references (do not fabricate real references). Add `make eval`.
**Acceptance:** `python -m eval.run --set tests-mini --mode replay` produces a report offline; unit tests for metric functions (known small cases) and CI-interval correctness; the generator refuses to emit README numbers if the report is missing.

---

## Prompt 8 — UI refresh (evidence ledger)
**Read:** 04 (all); 03 §3.2; 01 §4.1 F4, F6, F9.
**Task:** Implement tokens (`theme.css`), self-hosted fonts via fontsource (remove Google Fonts requests), `WitnessMatrix`, `ReceiptCard`, `CreditsMeter`, `ReplayBanner`, `SampleChip`, drawer tabs (Verdict | Witnesses | Passage & claim | Receipts), heatmap witness ring, `CoverageBar` unknown segment, `/eval` and `/method` pages, `BundleButton`, `AccessCodeDialog`, landing refresh (hero preview labelled "Sample data"), keyboard navigation and reduced-motion handling. Keep the existing React 19/Vite/Tailwind 4/router/d3/motion stack and the existing polling + SSE behaviour; do not rewrite `App.tsx` wholesale — extract only what you need.
**Acceptance:** `npm run build` + `tsc --noEmit` pass; no external font/network requests in a replay run (check the Network tab); "Unknown" is never red/amber; every SerpApi dot shows `search_metadata.id` in its receipt; screenshots from replay mode saved to `docs/img/`.

---

## Prompt 9 — Railway deployment
**Read:** 03 §2, §11, §12; 00 V11, V12, V18.
**Task:** Add `Dockerfile.railway`, `railway.json`, `deploy/railway/README.md`, config changes (database URL normaliser, `SERVE_FRONTEND` static mount with SPA fallback, `FILE_STORAGE_BACKEND=postgres` + `PostgresFileStore` + `file_blobs`, lazy GCS import so `google-cloud-storage` is optional), public-demo guard (`PUBLIC_DEMO_MODE`, `LIVE_ACCESS_CODE`, per-IP rate limit, upload size/type checks), janitor script for retention, `docker-compose.yml` `lite` profile. Mark Cloud Run files as legacy in a header note (do not delete). Provide Lean and Full profile variable tables exactly as in 03 §12.3.
**Acceptance:** `docker build -f Dockerfile.railway .` succeeds; container starts with only `PORT` set in replay mode and `/api/health` returns 2xx; `test_config.py` covers `postgres://` normalisation and production validation; with `PUBLIC_DEMO_MODE=true` a live upload without the code returns 401/403 while replay works; secret scan clean.

---

## Prompt 10 — Docs, disclosure, final gate
**Read:** 05 (all); 01 §10–12.
**Task:** Write the README per 05 §1 using only real measured values from `eval/report.json`, ledger and fixtures (leave no `{{braces}}`), finalise `docs/PRE_EXISTING_WORK.md`, `AI_USE.md`, `NOTICE.md`, `docs/FEASIBILITY.md`, `docs/METHOD.md`, `docs/EVAL.md`, `.env.example`; add `docs/AI_LOG.md` (milestone → prompt → commit). Run the judge checklist (05 §6) and output a pass/fail table in `docs/FINAL_CHECK.md`.
**Acceptance:** `grep -R "{{" README.md docs/ AI_USE.md` returns nothing; every engine in the README table appears in code and tests; checklist items 1–15 are ticked or explicitly explained; `make secret-scan`, `pytest`, frontend build all green; no dates/timelines in repo docs authored by the agent.
