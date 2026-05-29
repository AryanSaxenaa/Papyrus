# Papyrus

## Citation Integrity Audit System — Build Specification

---

## Project Statement

Academic citation hallucination is the most dangerous form of AI-generated slop because it
actively corrupts the knowledge graph that science depends on. A blog post that says nothing
is wasteful. A paper that cites 23 sources that don't exist — and gets cited by three other
papers — corrupts the scientific record permanently and propagates silently through the
literature.

Existing tools check for plagiarism: text overlap, paraphrasing, copied passages. Nobody
systematically verifies whether the references themselves are real, and whether they actually
say what the citing paper claims they say.

Papyrus fills that gap. It is a citation integrity audit pipeline that verifies the existence
of every cited source through multi-database cross-referencing, classifies the specific failure
mode when a citation breaks, and checks whether evidentiary citations are supported by the
sources they point to — using Natural Language Inference on bounded, explicit inputs.

**What Papyrus is:** A verifiable audit pipeline with receipts.

**What Papyrus is not:** An AI writing detector. Papyrus does not attempt to determine whether
a paper was written by an AI. Citation fabrication predates language models. A human can write
a paper with fake references. An AI can write a perfectly cited one. Papyrus audits the
reference layer, not the author.

This distinction is not a caveat. It is the entire thesis. It is stated clearly in the product,
in the interface, and in every communication about the tool.

---

## The Hallucination Taxonomy

Every flagged citation is classified into a specific failure type. Classification is a factual
finding with a defined detection method and a documented evidence source. Users can
independently verify every verdict with a browser.

### Type 1 — DOI 404

The digital object identifier does not resolve to any document. CrossRef returns no record.
Semantic Scholar finds nothing by title or author match. OpenAlex returns nothing. Exa finds
nothing semantically similar on the open web.

Detection method: multi-source API lookup, all returning null.
Confidence: High.
This is the cleanest signal in the taxonomy. It is a binary fact.

### Type 2 — DOI Redirect

The DOI resolves, but the metadata returned describes a completely different paper. The title,
authors, or journal in the bibliography entry do not match what the identifier actually points
to.

Detection method: CrossRef metadata diffing against the cited entry using fuzzy string
comparison on title and exact match on author list.
Confidence: High.
Classic LLM confabulation — the model generates a real-looking DOI that belongs to a
different real paper.

### Type 5 — Date Impossible

The paper is cited as published in year X, but the journal volume for that year did not exist.
The journal may have launched in 2021 and the citation claims 2018. Or the volume number does
not correspond to the year cited.

Detection method: CrossRef journal volume/issue metadata cross-referenced against the cited
year and volume number. Supplemented by the parseforge/crossref-journals-scraper Apify actor
for journals with incomplete API metadata.
Confidence: High.

### Type 6 — Title Drift

The paper exists and resolves correctly, but the title in the bibliography is a plausible
variation of the actual title rather than the exact title. The model remembered the topic and
generated a title that sounds right but isn't.

Detection method: Fuzzy title matching (Levenshtein distance and token overlap) against
CrossRef and Semantic Scholar results. Two-gate flagging: (1) substantial edit distance
threshold, AND (2) semantic mismatch between the cited title embedding and the resolved title
embedding. Both gates must trigger. Minor preposition changes that fall below the semantic
mismatch threshold are not flagged. Edit distance is displayed on every Type 6 verdict.
Confidence: Medium-High.

### Type 7 — Claim Contradiction

The cited paper exists, is real, and the citation resolves correctly. But the source either
directly contradicts what is claimed, or the topic of the source does not address the claim at
all.

Detection method: NLI entailment model on the extracted claim versus retrieved evidence
passage. Output: Entails / Contradicts / Neutral.

NLI known limitations (displayed to users):
NLI is reliable for detecting clear logical contradiction and topic mismatch. It is less
reliable on:

- Quantitative discrepancies ("42% reduction" vs "31% reduction" — NLI may return Entails)
- Statistical hedging ("significant effect" vs "trend not reaching significance")
- Causation vs correlation ("X causes Y" vs "X is associated with Y")

For any verdict on a claim containing specific numbers, percentages, p-values, or causal
language, the interface displays: "Quantitative claim — NLI may not detect numerical
discrepancies. Manual verification recommended." This caveat is non-optional and appears
regardless of confidence level.

Confidence: High for clear contradiction with Tier 1 evidence. Medium for abstract-only.
Always labeled with evidence tier and quantitative caveat where applicable.

### Retraction Flag

The cited paper is real and resolves correctly, but it has been retracted. A retracted citation
is arguably worse than a missing one — the work was relied upon after it was discredited.

Detection method: CrossRef retraction flag checked on every resolved DOI.
Confidence: High.
Elevated severity display — visually distinct from standard hallucination flags.

### Version Mismatch

The paper is cited using a preprint DOI (typically arXiv), but the published version has
materially different conclusions, authorship, or title.

Detection method: arXiv API submission history + Semantic Scholar version linking. Comparison
of preprint metadata versus published record metadata. The datapilot/arxiv-research-paper-scraper
Apify actor provides structured version data when direct API calls return incomplete history.
Confidence: Medium.

### Cannot Determine

The source exists behind a paywall and no abstract or metadata is available beyond the
identifier. Existence may be confirmed but claim alignment cannot be assessed.

This is not a failure category. It is an honest verdict. The system does not score what it
cannot see. The interface displays this explicitly and separately from all hallucination
verdicts. It does not contribute to the risk assessment.

---

## Categories Excluded and Why

**Author Ghost** (excluded): Checking whether an author has previously published in a specific
journal generates false positives on legitimate first publications, interdisciplinary work,
and invited contributions. Semantic Scholar's author disambiguation fails on common non-Western
names and early-career researchers. This heuristic produces noise, not signal.

**Journal Phantom via DOAJ** (excluded): DOAJ is an open-access index, not a universal
journal registry. It would flag thousands of legitimate subscription journals as suspicious.
Replaced with CrossRef ISSN verification and OpenAlex journal catalog lookup.

**Circular Citation** (excluded from v1): A citation loop where paper A cites paper B which
cites paper A for the same claim is a real methodological problem, but not hallucination. It
requires two-level-deep resolution — up to 2,500 API calls for a 50-citation paper — and
produces ambiguous verdicts. Documented as a v2 feature.

---

## System Architecture

### Layer 1 — Ingestion

**PDF Upload**
User uploads a PDF via drag-and-drop. The system accepts standard academic PDFs, preprints,
theses, and grant documents.

Primary parser: GROBID (self-hosted Docker container, 2-4GB RAM allocation). GROBID is a
purpose-built academic PDF parser with F1 scores of 0.87-0.90 on reference extraction
benchmarks. It extracts every bibliography entry as structured JSON, maps every inline citation
marker to its corresponding bibliography entry, and captures the surrounding sentence context
for each inline citation — the "claim context window" used in Layer 5.

Fallback parser: PyMuPDF for raw text extraction, followed by a structured DeepSeek API call
for citation parsing into JSON. This fallback handles non-standard layouts — theses, conference
proceedings, preprints with unusual formatting — that GROBID handles poorly. The system
automatically routes to the fallback when GROBID returns malformed or sparse output, assessed
by checking the ratio of extracted fields to bibliography entries.

**Direct URL Input**
Accepts arXiv URLs, SSRN links, PubMed URLs, and direct DOI URLs. Firecrawl fetches and
parses the landing page to locate the PDF. GROBID handles extraction from there.

**Direct DOI Input**
Single DOI for targeted verification of one cited source.

**Bulk Upload**
ZIP archive of multiple PDFs. Jobs enter an async queue (Redis + Celery). Results are returned
per-paper as they complete, with a live progress tracker showing which papers have finished and
their preliminary coverage scores. This is the primary workflow for journal editors and grant
review panels.

**Apify Integration for Paper Retrieval**
When cited papers need metadata or full text retrieved and standard API calls fail or hit rate
limits, the following Apify actors serve as structured retrieval tools:

- datapilot/arxiv-research-paper-scraper: Retrieves arXiv paper metadata — titles, abstracts,
authors with affiliations, DOI, categories, submission dates, and PDF links in structured
JSON. Primary use: preprint version tracking and Version Mismatch detection.
- openclawmara/arxiv-paper-scraper: Secondary arXiv retrieval for cross-validation,
particularly for citation metadata fields the primary actor does not surface.
- shahidirfan/openalex-scraper and parseforge/openalex-scraper: Bulk OpenAlex retrieval when
the direct REST API hits rate limits. Returns scholarly metadata including institutional
affiliations, concept tags, open access status, and ISSN data for journal verification.
- parseforge/crossref-journals-scraper: Journal-level metadata for Type 5 (Date Impossible)
verification — journal names, identifiers, publication dates, volume history, and status flags.
- ryanclinton/europe-pmc-search and parseforge/europepmc-scraper: Biomedical and life sciences
full text. Europe PMC aggregates PubMed, PubMed Central, bioRxiv, and medRxiv. Used for
Tier 1 evidence retrieval in biomedical citation alignment.
- nexgendata/academic-research-mcp-server: MCP-based cross-database research server for paper
search and citation lookup across arXiv, PubMed, and Google Scholar. Used as a structured
search layer when direct DOI resolution fails and semantic search is needed. MCP-native
invocation means calls appear in the live resolution panel as named tool calls with parameters.

All Apify actor outputs are cached at the DOI level with a 30-day TTL in Redis. The same paper
queried by multiple users triggers one actor run.

**Caching Architecture**
Every DOI resolution result, every abstract retrieval, and every actor output is cached in
Redis with structured keys: doi:{hash}, abstract:{hash}, actor:{actor_id}:{input_hash}.
Caching is architecture, not optimization. Without it, the resolution pipeline becomes
rate-limited at any realistic scale. Rate limit budgets for each API are tracked and exposed
in the admin dashboard.

---

### Layer 2 — Citation Extraction and Structural Mapping

After ingestion, Papyrus builds a complete internal citation map before any external resolution
begins.

For every bibliography entry: raw string, extracted authors (parsed into structured name
fields), title, year, journal, volume, issue, pages, DOI, URL, and any other identifiers
present.

For every inline citation marker: which bibliography entry it points to, and the surrounding
three sentences — the claim context window used in Layer 5.

**Citation Intent Classification**
Applied at this stage, before resolution. Not every citation makes a factual claim. Running
claim alignment on every citation generates noise and false positives. Intent classification
gates which citations receive full alignment scoring.

Classification uses DeepSeek v4 Pro with a bounded structured extraction prompt: given this
citation context sentence, classify the intent as one of four categories and output JSON.

Intent categories:

- Evidentiary: The citation supports a specific factual claim. "Smith et al. found that X
increases Y by 40%." Proceeds to full claim alignment.
- Methodological: The citation is a technique or tool reference. "We used the approach
described in Smith et al." Existence-verified, not claim-scored.
- Contrastive: The citation establishes contrast. "Unlike Smith et al., we find..." Low
semantic similarity between the claim context and the source is expected and correct.
Scoring as unsupported would be a systematic false positive.
- Background: General field-framing with low claim specificity. "This field has grown
substantially (Smith et al., Jones et al.)." Existence-verified, not claim-scored.

The intent classification for every citation is displayed in the interface and editable by the
user. If the system misclassifies a contrastive citation as evidentiary, the user corrects it
and the citation is removed from claim scoring.

---

### Layer 3 — Multi-Source Resolution Pipeline

The resolution layer runs every citation through a cascading sequence of verification sources.
Every source queried and every result returned — including failures — is logged to the audit
trail. The full sequence is the evidence base for every verdict.

Citations are resolved in parallel threads. Results are aggregated before verdicts are assigned.

**CrossRef** (Primary DOI Resolution)
The authoritative registry for DOI-identified content. Called first for any citation containing
a DOI. Returns: title, authors, year, journal, volume, issue, abstract where available,
retraction flag, and license information.

DOI content negotiation is used before any crawling — hitting the DOI URL with
Accept: application/json headers returns structured metadata directly for most major publishers.

**Semantic Scholar** (Secondary)
Called when CrossRef returns no result, or as a cross-check on CrossRef metadata. Title and
author search returns the publication record when it exists. Also provides the paper's
embedding (used in Layer 4 for evidence retrieval) and the author's publication history as a
soft context signal. Author disambiguation has documented failures on common non-Western names
— any author-graph output is labeled as a soft signal, never a hard verdict.

**OpenAlex** (Tertiary)
The most comprehensive open bibliographic database, with 250M+ scholarly records. Catches
papers that CrossRef and Semantic Scholar both miss — older content, regional journals,
humanities papers, conference proceedings, and papers with inconsistent DOI assignment. Also
used for ISSN-based journal existence verification.

**Unpaywall** (Open Access Full Text)
For every resolved DOI, Unpaywall is queried for open-access full-text availability. When full
text exists, it is retrieved and stored for Layer 4 evidence retrieval.

**PMC / Europe PMC** (Biomedical Full Text)
For biomedical and life sciences papers. PMC and Europe PMC have extensive open full-text
coverage in this domain. Retrieved via the parseforge/europepmc-scraper and
ryanclinton/europe-pmc-search Apify actors when direct API calls hit rate limits.

**arXiv API** (Preprint Version Tracking)
For any citation using an arXiv identifier, the API is queried for the submission history.
Combined with Semantic Scholar's version linking, this detects cases where a preprint was cited
but the published version has materially different conclusions.

**Exa AI** (Last Resort — Semantic Web Search)
When all structured databases return nothing, Exa performs a semantic web search using the
paper title and abstract fragment.

Critical constraint, architecturally enforced: Exa returning no results does not mean the paper
does not exist. Exa absence is a low-confidence signal only. The UI always displays: "Not found
in any indexed source — signal only, not a verdict. Human review required." Exa absence cannot
be the sole basis for any hallucination verdict.

**Firecrawl** (Targeted Landing Page Crawling)
Called only when a DOI resolves to a JavaScript-rendered publisher landing page that returns no
structured metadata via content negotiation and no abstract via CrossRef. Called only after all
other retrieval sources are exhausted. Rate-limited aggressively. Results cached at the DOI level.

**Resolution Tiers**


| Tier   | Condition                      | Claim Alignment Available        |
| ------ | ------------------------------ | -------------------------------- |
| Tier 1 | Verified + full text retrieved | Yes — high confidence ceiling    |
| Tier 2 | Verified + abstract only       | Yes — medium confidence, labeled |
| Tier 3 | Verified + no text available   | No — existence confirmed only    |
| Tier 4 | All sources return nothing     | No — unresolvable signal         |


---

### Layer 4 — Evidence Retrieval for Claim Alignment

Evidence retrieval runs before claim alignment begins. The tier reached determines the
confidence ceiling on any claim verdict. This ceiling cannot be overridden.

**Tier 1 — Full Text Available**
Source: Unpaywall, PMC, Europe PMC, arXiv open-access PDF. The full text is chunked into
overlapping windows of approximately 512 tokens. The extracted claim is embedded. The most
semantically relevant chunk is retrieved via cosine similarity ranking. This chunk — not the
abstract — is the evidence input to the NLI model.

**Tier 2 — Abstract Only**
When full text is unavailable. The abstract is retrieved from CrossRef, Semantic Scholar, or
OpenAlex. Claim alignment proceeds but every verdict carries a mandatory label: "Analysis based
on abstract only — full text unavailable. Specific numerical claims, methods details, and
supplementary results cannot be verified from the abstract alone."

Tier 2 Neutral verdicts are always flagged for human review rather than presented as
unsupported findings — the most common cause is that the claim refers to something in the body
of the paper that does not appear in the abstract.

**Tier 3 — Metadata Only**
Title, authors, and year confirmed but no text is available. Existence is verified. Claim
alignment verdict is Cannot Determine. Displayed without negative connotation.

**Tier 4 — Unresolvable**
No resolution source returns any data. The composite signal is based on citation specificity:
a citation with a DOI that resolves to nothing is a stronger signal than a citation without a
DOI that cannot be found. The full list of queries and negative results is shown in the audit
trail. This contributes to the Coverage metric but not to the Risk assessment directly.

---

### Layer 5 — Claim Alignment Reasoning

This layer runs only on citations classified as Evidentiary in Layer 2. The intent
classification gate is the single most important quality decision in the pipeline.

**Step 1 — Claim Extraction**
DeepSeek v4 Pro is called with a structured extraction prompt: given the inline citation context
window, extract the specific factual claim being attributed to the cited source and output it
as a single clean sentence.

The extracted claim is shown to the user before NLI runs, with an Edit button. The user can
inspect it, correct it if wrong, and resubmit. This human-in-the-loop gate catches fragile
extractions from multi-claim sentences ("Prior work demonstrated A, B, and C (Smith et al.,
2022)") and builds a ground-truth dataset of corrected claim extractions for future calibration.

The original context window, the extracted claim, the user's correction if any, and a
confidence flag are all stored in the per-citation record.

**Step 2 — Evidence Retrieval**
If Tier 1 evidence is available, the extracted claim is embedded and the most relevant passage
from the chunked full text is retrieved via cosine similarity ranking. If only Tier 2 is
available, the abstract is used directly. If neither is available, the verdict is Cannot
Determine.

Embeddings model: OpenAI text-embedding-3-small (default) or Snowflake Arctic Embed. Used for
retrieval only — the cosine similarity score is an internal ranking mechanism, not a verdict,
and is not displayed to users.

**Step 3 — NLI Entailment**
The extracted claim and the retrieved evidence passage are passed to a Natural Language
Inference model. Output: Entails / Contradicts / Neutral.

The verdict is accompanied by the exact evidence passage that was used so the user can verify
it independently.

**Step 3a — Quantitative Claim Detection (mandatory caveat gate)**
Before the NLI verdict is finalized, the extracted claim is checked for quantitative language:
specific numbers, percentages, p-values, confidence intervals, effect sizes, and causal
language. If any are present, the following caveat is appended and cannot be suppressed:

"Quantitative claim detected. NLI reasoning is reliable for logical contradiction and topic
mismatch but may not detect numerical discrepancies or differences between causal and
correlational language. Manual verification of the specific figures is recommended."

**Step 4 — Negation and Hedging Detection**
A secondary check scans the claim context window for contrastive and negation language:
"contrary to," "we challenge," "unlike," "in contrast to," "we dispute," "inconsistent with."
Citations flagged by this check are reclassified as Contrastive and removed from claim scoring,
overriding the Layer 2 classification if needed.

**Step 5 — Confidence Assignment**


| NLI Output  | Evidence Tier          | Final Confidence                   |
| ----------- | ---------------------- | ---------------------------------- |
| Entails     | Tier 1 (full text)     | High — Supported                   |
| Entails     | Tier 2 (abstract only) | Medium — Supported (abstract only) |
| Contradicts | Tier 1                 | High — Claim Contradiction         |
| Contradicts | Tier 2                 | Medium — Possible Contradiction    |
| Neutral     | Tier 1                 | Medium — Not Addressed             |
| Neutral     | Tier 2                 | Low — Cannot Determine             |


Any verdict at Medium confidence or below is automatically flagged for human review.

---

### Layer 6 — Scoring and Output

**Citation Verification Coverage (Primary Metric)**

The primary output metric is Coverage, not Risk. Coverage answers: what fraction of this
paper's citations could we actually verify?

```
Citation Verification Coverage: 55%
(26 of 47 citations received at least Tier 2 resolution)
```

A paper with 90% coverage and a high risk score is alarming. A paper with 30% coverage and a
high risk score may simply be a humanities paper with old sources — the distinction is critical.

**Risk Assessment (Derived from Confirmed Failures Only)**

Risk is derived only from citations that were resolvable and failed — not from unresolvable
ones. Unresolvable citations are reported separately with an explicit note about field coverage
limitations.

Risk levels: Low / Elevated / High / Critical

- Critical: confirmed failures exceed 20% of total citations
- High: 10–20%
- Elevated: 5–10%
- Low: under 5%

Unresolvable citations are labeled: "These citations could not be verified by any indexed
source. This may reflect database coverage limitations rather than citation failure,
particularly for older sources, books, and non-English publications."

**Paper-Level Audit Summary**

```
═══════════════════════════════════════════════════════════════
 PAPYRUS — CITATION INTEGRITY AUDIT
 Paper: [Title truncated to 80 chars]
 Analyzed: [ISO timestamp]  |  Pipeline version: 2.0
═══════════════════════════════════════════════════════════════

 CITATION VERIFICATION COVERAGE
 ────────────────────────────────────────────────────────────
 Total citations extracted:                              47
 Resolved (Tier 1 — full text):                         11   (23%)
 Resolved (Tier 2 — abstract only):                     15   (32%)
 Resolved (Tier 3 — metadata only):                      4   ( 8%)
 Unresolvable (outside indexed sources):                17   (37%)
 ────────────────────────────────────────────────────────────
 Coverage score:                                        55%
 Coverage confidence:                      MEDIUM
 Note: 17 citations outside indexed sources.
       Field-specific coverage limitations may apply.

 CONFIRMED CITATION FAILURES (resolvable citations only)
 ────────────────────────────────────────────────────────────
 Verified + claim supported:                            12   (40% of resolved)
 Verified + claim not supported:                         4   (13% of resolved)
 Verified + cannot assess claim [paywalled]:             4   (13% of resolved)
 Type 1 — DOI 404:                                       3   (10% of resolved)
 Type 2 — DOI Redirect:                                  2   ( 7% of resolved)
 Type 5 — Date Impossible:                               1   ( 3% of resolved)
 Type 6 — Title Drift:                                   1   ( 3% of resolved)
 Retraction Flag:                                        0
 Version Mismatch:                                       2   ( 7% of resolved)
 ────────────────────────────────────────────────────────────
 Confirmed failure rate (of resolved citations):        37%
 RISK ASSESSMENT:                                     HIGH
 Risk confidence:                                   MEDIUM
 Basis: Coverage at 55%. Risk derived from
        confirmed failures only.

 ────────────────────────────────────────────────────────────
 This is a citation integrity audit.
 Papyrus does not determine authorship or AI involvement.
═══════════════════════════════════════════════════════════════
```

**Per-Citation Verdict Record**
Every citation produces a structured record: original bibliography entry, intent classification,
resolution tier reached, all resolution sources queried with their responses, hallucination type
if applicable, claim alignment verdict if evidentiary, the extracted claim as submitted to NLI
(and any user correction), the evidence passage used, the confidence level, quantitative claim
flag, retraction status, and a direct URL to the source for independent verification.

**Exportable Audit Report**
PDF export of the full audit: summary card, per-citation verdicts with evidence, resolution
log, and a section explicitly documenting what the tool did not check and why. JSON export for
downstream integration.

---

## Visual Interface

### Design Philosophy

The interface is built around one principle: the evidence should do the persuading. Papyrus
does not assert. It shows. Coverage shows reliability. The live panel shows work. The
side-by-side viewer shows receipts.

No element of the interface makes a claim the underlying data does not support. Confidence
levels are visually distinct from high-certainty verdicts. Cannot Determine is displayed
neutrally. Unresolvable is shown separately from confirmed failures. The retraction flag is the
most visually severe verdict in the system.

### Visual Design Language

Semantic color system:

- Deep forest green — Verified and claim supported (high confidence)
- Amber — Exists, claim uncertain or abstract-only analysis
- Crimson — Confirmed failure: hallucinated, contradicted, impossible date
- Gold border on crimson — Retraction flag (elevated severity)
- Steel blue — Verified, cannot assess claim (paywalled / Tier 3)
- Warm grey — Methodological or background citation (intentionally not claim-scored)
- Dark ash grey — Unresolvable (separate from failure colors, visually neutral)

Unresolvable citations use a deliberately neutral color distinct from confirmed failure crimson.
The color system enforces the Coverage vs Risk distinction at a glance.

Typography: A monospaced or slab-serif display font for verdict counts, confidence levels, and
audit data paired with a refined humanist sans-serif for body text and labels. Not Inter. Not
system fonts. The typography should feel like a scientific instrument readout.

Motion: Staggered card reveals as analysis completes. Citation cards transition from pending
grey through resolving amber to their final verdict color. No animation runs without a real
system event behind it.

### The Live Resolution Panel

A real-time event stream via SSE (Server-Sent Events) shows every tool call and resolution
step as it happens. This is a live feed of actual API calls returning actual results.

The panel is split into two columns: the event log on the left (timestamped tool calls with
parameters and outcomes), and a live citation card stack on the right (cards transitioning to
their verdict colors as they resolve).

Example live stream:

```
10:42:31  GROBID  PDF parse complete
          -> 47 citations extracted · 89 inline markers mapped
          -> Intent classification: 31 Evidentiary · 9 Methodological · 7 Background

10:42:32  CrossRef  DOI 10.1038/s41586-021-03819-2
          -> Resolved — Nature 2021, Vol 595, pp. 41-45
          -> Retraction flag: None
          -> Unpaywall: Full text available [PDF link stored]
          -> Resolution tier: Tier 1

10:42:33  Claim extraction  Citation #3 (Evidentiary)
          -> DeepSeek extraction: "reduces cognitive load by 34% in working memory tasks"
          -> [Quantitative claim detected — NLI caveat will apply]
          -> Awaiting user review before NLI...

10:42:41  NLI alignment  Citation #3
          -> Claim (user-confirmed): "reduces cognitive load by 34% in working memory tasks"
          -> Evidence: Section 3.2, full text (Tier 1)
          -> NLI verdict: ENTAILS
          -> Quantitative caveat: appended
          -> Verdict: SUPPORTED (High confidence) — verify figures manually

10:42:43  CrossRef  DOI 10.xxxx/neurosci.2023.8841
          -> 404 — No record found
          -> Semantic Scholar: No title match
          -> OpenAlex: No match
          -> arXiv: Not found
          -> Exa: Cannot locate
          -> Verdict: Type 1 — DOI 404 [Added to confirmed failures]

10:42:45  CrossRef  DOI 10.1001/jama.2021.6224
          -> Resolved — title mismatch detected
          -> Cited as:    "Long-term outcomes in post-COVID neurological syndromes"
          -> Resolved to: "Association of SARS-CoV-2 Infection With Physical..."
          -> Levenshtein distance: 61 tokens | Semantic mismatch: confirmed
          -> Both gates triggered
          -> Verdict: Type 6 — Title Drift (Medium-High confidence)

10:42:47  CrossRef  Retraction check  Citation #12
          -> RETRACTED — notice issued 2023-09-14
          -> Verdict: Retraction Flag — elevated severity [Gold border]

10:42:49  nexgendata/academic-research-mcp-server
          -> Tool: search_papers
          -> Query: "Hoffman et al 2022 scaling laws emergent behavior"
          -> Found via Google Scholar index — Semantic Scholar confirmed
          -> Resolution tier: Tier 2 (abstract available)
```

Every line is a real event. The log is scrollable, searchable by citation number or verdict
type, and downloadable as plain text.

### Citation Integrity Heatmap

The bibliography rendered as a grid of citation cards. Color-coded by verdict as analysis
completes. Cards begin grey (pending), shift to pulsing amber (resolving), then settle to their
final verdict color.

Cards display: citation number, first author name, year, verdict badge. Click any card to open
the Side-by-Side Viewer.

Heatmap filter controls: show all / confirmed failures only / unresolvable only / claim
contradictions only / retracted only. The confirmed-failures-only view is the most important
for editors assessing risk.

A visual legend below the heatmap explicitly separates the unresolvable color from the
confirmed failure colors.

### Paper Anatomy View

The full paper text rendered in a reading pane. Every inline citation marker displayed as a
color-coded badge, updating live as the corresponding citation resolves.

Click any inline citation marker to jump directly to its card in the heatmap and open the
Side-by-Side Viewer.

Dense clusters of failure-colored badges in the introduction and related work sections are a
consistent pattern in AI-generated papers — the model needed to appear well-read but had no
real sources to cite.

### Side-by-Side Claim Viewer

Click any citation card. A full-width drawer expands.

Left panel: the full paragraph from the citing paper surrounding the inline citation marker,
with the claim sentence highlighted. Intent classification shown with an Edit button to
reclassify.

Centre column: verdict badge, confidence level, evidence tier, hallucination type, retraction
status, quantitative claim flag, and a complete list of every resolution source queried with
its outcome. Evidence provenance displayed as a chain: which API provided the text, what type
of access, and when it was retrieved.

Right panel: the evidence used. If Tier 1: the retrieved passage from the full text, most
relevant sentence highlighted. If Tier 2: the abstract, most relevant sentence highlighted.
If unresolvable: "No document found. The following sources were queried and returned no result:"
followed by each API call and its response.

Extracted Claim display: the claim sentence that was submitted to NLI, shown in an editable
field. If the user submitted a correction, both the original extraction and the corrected
version are shown. A "Rerun NLI" button reruns claim alignment on the corrected claim.

### Version Mismatch Timeline

For Version Mismatch verdicts: arXiv preprint submission date, revision dates with change
notes, published version date and journal of record. Both the preprint abstract and the
published abstract are shown side by side where they differ materially.

### Coverage and Risk Summary Panel

Displayed at the top of every analysis result. Shows Coverage percentage prominently, then the
Risk assessment below it, with the explicit note that Risk is derived only from confirmed
failures. A visual bar divides the citation count into: Tier 1 / Tier 2 / Tier 3 /
Unresolvable / Confirmed Failure.

Below the summary, five clickable verdict-type counts filter the heatmap:
Supported · Contradicted · Cannot Assess · Confirmed Failure · Retracted

### Bulk Analysis Dashboard

When multiple papers are submitted, a ranked list sorted by confirmed failure rate among
resolvable citations (not by unresolvable count). Each row: paper title, first author, coverage
percentage, confirmed failure rate, risk level, and verdict-type counts.

Click any paper to expand its full heatmap and resolution log.

Progress tracking per paper with estimated completion based on citation count.

---

## Technology Stack

### Document Processing

- GROBID — self-hosted Docker, primary academic PDF parser (F1 ~0.87-0.90)
- PyMuPDF — fallback raw text extraction for non-standard PDF layouts
- Firecrawl — targeted JavaScript-rendered landing pages only, after all other retrieval
methods exhausted

### Bibliographic Resolution APIs

- CrossRef — primary DOI resolution, retraction flags, content negotiation for abstracts
- Semantic Scholar — title/author search, paper embeddings, version linking
- OpenAlex — broadest bibliographic coverage, ISSN journal verification (250M+ records)
- Unpaywall — open access full text retrieval
- PMC / Europe PMC — biomedical full text (direct API + Apify actors)
- arXiv API — preprint submission history and version tracking
- Exa AI — last-resort semantic web search, architecturally constrained to signal-only

### Apify Actors (Structured Retrieval Layer)

- datapilot/arxiv-research-paper-scraper — arXiv structured metadata and version data
- openclawmara/arxiv-paper-scraper — secondary arXiv cross-validation
- shahidirfan/openalex-scraper + parseforge/openalex-scraper — bulk OpenAlex retrieval
- parseforge/crossref-journals-scraper — journal-level metadata for Type 5 verification
- ryanclinton/europe-pmc-search + parseforge/europepmc-scraper — biomedical full text
- nexgendata/academic-research-mcp-server — MCP cross-database paper search

### AI and Reasoning Models

- DeepSeek v4 Pro — structured extraction: citation intent classification, claim sentence
extraction. Not used for detection verdicts. Input and output are bounded and explicit.
- NLI model — entailment classification (Entails / Contradicts / Neutral). Purpose-built
for this task. Applied only to evidentiary citations with Tier 1 or Tier 2 evidence.
- Embeddings model — OpenAI text-embedding-3-small (default) or Snowflake Arctic Embed.
Used for evidence passage retrieval only. Not used for verdicts.

### Infrastructure

- Redis — DOI-level result caching (30-day TTL), job queue, rate limit budgets
- Celery / RQ — async job queue for bulk paper analysis
- SSE (Server-Sent Events) — real-time event streaming to the live resolution panel
- PostgreSQL — persistent storage for completed analyses, audit logs, user corrections
(ground-truth dataset), exported reports
- Docker Compose — local orchestration of GROBID + application services

### Frontend

- React — main application shell
- Tailwind CSS — utility styling
- SSE consumer — live resolution panel event rendering
- PDF renderer — paper anatomy view with inline citation badge overlays
- D3 — heatmap grid, coverage bar visualization, version mismatch timeline
- Custom font pairing — slab-serif or monospaced display font for audit data; humanist
sans-serif for body text

---

## Data Handling and Honest Constraints

**Paywalled sources**
Paywalled citations receive a Cannot Determine verdict on claim alignment. The audit summary
shows how many citations fell into this category. Papyrus does not attempt to circumvent
access controls.

**Field coverage bias**
The pipeline performs best on STEM papers with high DOI coverage and open access availability.
Humanities, social sciences, and non-English papers have lower bibliographic indexing density
and will produce more unresolvable verdicts even when citations are entirely real. The interface
notes this on every analysis and it is reflected in the Coverage metric, shown separately from
the Risk assessment precisely to prevent misinterpretation.

**Exa absence is not evidence of hallucination**
This constraint is enforced architecturally. Exa can only move a citation from unresolvable to
"weak signal found." Exa absence cannot trigger a confirmed failure verdict.

**NLI limitations on quantitative claims**
Every verdict on a claim containing numbers, percentages, statistical terms, or causal language
carries the mandatory quantitative caveat. This cannot be suppressed.

**What Papyrus does not catch**
Misappropriated citations: a real paper cited out of context to support a claim its authors
never made. The citation resolves correctly, the claim alignment may return Entails because the
topics overlap, but the intellectual connection is fabricated. This is documented in the
interface as a known limitation.

Self-citation manipulation, quality of the underlying research, and author misconduct beyond
fabricated references are outside scope. The "What this audit does not cover" section appears
in every exported report.

---

## Positioning

**Against existing tools**
iThenticate and Turnitin check text overlap. Papyrus checks whether the reference layer is
real and whether cited sources support the claims made. These are different problems. Papyrus
is the missing layer in the existing integrity workflow, not a competitor to plagiarism
detection.

**Immediate applications**

- Journal editors: bulk submission screening ranked by confirmed failure rate
- Preprint servers: submission quality gate on bibliography integrity
- University integrity offices: citation audit layer complementing plagiarism detection
- Grant review panels: bibliography integrity scoring for applications
- Individual researchers: self-audit before submission

**Acquisition path**
Natural integration with Elsevier, Springer, Wiley, CrossRef itself, Clarivate (Web of
Science), and academic integrity platforms. The JSON export is designed for downstream API
consumption. The ground-truth correction dataset built from user edits has standalone value.

---

## The Honest Summary

The citation existence pipeline — Types 1, 2, 5, 6, and Retraction — is high precision and
produces independently verifiable verdicts. A DOI that does not exist is a fact, not a
probability.

The claim alignment pipeline — Type 7 — is genuine and architecturally sound (embeddings for
retrieval, NLI for verdict, intent gate before both) but carries documented confidence ceilings
that the interface never obscures. Quantitative claims carry an additional mandatory caveat.
User-editable claim extraction makes the most fragile pipeline step auditable.

The Coverage metric separates what the system could verify from what it couldn't, preventing
the category error of treating unresolvable citations as confirmed failures.

The things Papyrus doesn't catch are documented. The things it gets wrong at medium confidence
are labeled. The quantitative limits of NLI are disclosed on every relevant verdict. The
evidence behind every verdict is shown. The system asks to be checked.

That is the architecture. That is also the argument.