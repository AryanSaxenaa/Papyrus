import type { AuditRun, CitationRecord } from "../types";

const PAPER_TITLE =
  "Long-lived quantum coherence in photosynthetic complexes at physiological temperature";

export const DEMO_PAPER_TEXT = `Recent experiments suggest that electronic coherence can persist in photosynthetic antenna complexes long enough to influence excitation energy transfer [1]. Earlier models treated transport as purely incoherent hopping [2], but two-dimensional spectroscopy has challenged that picture [3].

We build on prior measurements of reaction-center kinetics [4] and extend the analysis to cryogenic controls [5]. A retracted reanalysis of the same dataset was excluded from our comparison [6]. One cited preprint could not be matched to a DOI in CrossRef [7].

Methods follow standard open-access reporting guidelines [8]. Statistical power for the secondary endpoint was under-reported in the source we cite for effect sizes [9].`;

function cite(
  index: number,
  overrides: Partial<CitationRecord> & Pick<CitationRecord, "verdict_color" | "evidence_tier">,
): CitationRecord {
  const title = overrides.bibliography?.title ?? `Reference ${index}`;
  const { bibliography: bibOverrides, ...rest } = overrides;
  return {
    intent: rest.intent ?? "evidentiary",
    hallucination_type: rest.hallucination_type ?? "none",
    status: "complete",
    inline_markers: [
      {
        marker: `[${index}]`,
        bibliography_index: index,
        context_window: `Context for citation [${index}] in the demo manuscript.`,
      },
    ],
    resolution_attempts: [
      {
        source: "crossref",
        query: `DOI:10.1000/demo.${index}`,
        success: overrides.evidence_tier !== "tier_4",
        summary: overrides.evidence_tier === "tier_4" ? "not_found" : "resolved",
      },
    ],
    ...rest,
    index,
    id: `demo-citation-${index}`,
    bibliography: {
      index,
      raw: bibOverrides?.raw ?? `${title} (${2018 + (index % 6)}).`,
      title: bibOverrides?.title ?? title,
      year: bibOverrides?.year ?? 2018 + (index % 6),
      doi: bibOverrides?.doi ?? (index === 7 ? null : `10.1000/demo.${index}`),
      authors: bibOverrides?.authors ?? ["A. Researcher", "B. Collaborator"],
      journal: bibOverrides?.journal ?? "Journal of Demo Biophysics",
      ...bibOverrides,
    },
  };
}

/** Completed audit snapshot — same JSON shape as `GET /api/audits/{id}`. */
export const DEMO_AUDIT: AuditRun = {
  id: "00000000-0000-4000-8000-000000000001",
  paper_title: PAPER_TITLE,
  status: "complete",
  pipeline_version: "2.0",
  created_at: "2025-11-14T09:12:00Z",
  completed_at: "2025-11-14T09:28:00Z",
  paper_text: DEMO_PAPER_TEXT,
  risk_level: "elevated",
  risk_confidence: "high",
  coverage: {
    total: 20,
    tier_1: 4,
    tier_2: 9,
    tier_3: 3,
    tier_4: 2,
    coverage_percent: 65,
    coverage_confidence: "high",
  },
  failures: {
    confirmed_failure_rate: 15,
    supported: 10,
    not_supported: 1,
    cannot_assess: 3,
    type_1: 1,
    type_2: 0,
    type_5: 1,
    type_6: 0,
    type_7: 1,
    retraction: 1,
    version_mismatch: 0,
  },
  limitations: {
    field_coverage_note: "Demo audit for marketing preview.",
    misappropriation_not_detected:
      "Author-disambiguation and ghost-author checks are out of scope for this preview.",
    nli_quantitative_caveat: "NLI on quantitative claims requires full-text evidence tiers 1–2.",
    out_of_scope: ["AI authorship detection"],
  },
  citations: [
    cite(1, { evidence_tier: "tier_2", verdict_color: "supported", bibliography: { index: 1, raw: "", title: "Coherent dynamics in FMO complexes", year: 2021, doi: "10.1000/demo.1", authors: ["Engel et al."] } }),
    cite(2, { evidence_tier: "tier_2", verdict_color: "supported", bibliography: { index: 2, raw: "", title: "Hopping transport in photosynthesis", year: 2019, doi: "10.1000/demo.2", authors: ["May et al."] } }),
    cite(3, { evidence_tier: "tier_1", verdict_color: "supported", claim_alignment_verdict: "claim_supported", bibliography: { index: 3, raw: "", title: "2D spectroscopy of light harvesting", year: 2020, doi: "10.1000/demo.3", authors: ["Panitchayangkoon et al."] } }),
    cite(4, { evidence_tier: "tier_2", verdict_color: "supported", intent: "methodological" }),
    cite(5, { evidence_tier: "tier_1", verdict_color: "supported" }),
    cite(6, {
      evidence_tier: "tier_2",
      verdict_color: "retraction",
      hallucination_type: "retraction",
      retracted: true,
      bibliography: { index: 6, raw: "", title: "Retracted coherence analysis", year: 2017, doi: "10.1000/demo.6", authors: ["Lee et al."] },
    }),
    cite(7, { evidence_tier: "tier_4", verdict_color: "unresolvable", hallucination_type: "none" }),
    cite(8, { evidence_tier: "tier_2", verdict_color: "neutral", intent: "background" }),
    cite(9, {
      evidence_tier: "tier_2",
      verdict_color: "failure",
      hallucination_type: "type_5",
      claim_alignment_verdict: "not_addressed",
    }),
    cite(10, { evidence_tier: "tier_3", verdict_color: "cannot_assess" }),
    cite(11, { evidence_tier: "tier_2", verdict_color: "supported" }),
    cite(12, { evidence_tier: "tier_2", verdict_color: "supported" }),
    cite(13, { evidence_tier: "tier_1", verdict_color: "supported" }),
    cite(14, { evidence_tier: "tier_3", verdict_color: "cannot_assess" }),
    cite(15, {
      evidence_tier: "tier_2",
      verdict_color: "failure",
      hallucination_type: "type_1",
      bibliography: { index: 15, raw: "", title: "Non-existent DOI record", year: 2022, doi: "10.1000/missing", authors: [] },
    }),
    cite(16, { evidence_tier: "tier_2", verdict_color: "supported" }),
    cite(17, { evidence_tier: "tier_3", verdict_color: "cannot_assess" }),
    cite(18, {
      evidence_tier: "tier_2",
      verdict_color: "failure",
      hallucination_type: "type_7",
      claim_alignment_verdict: "claim_contradiction",
    }),
    cite(19, { evidence_tier: "tier_4", verdict_color: "unresolvable" }),
    cite(20, { evidence_tier: "tier_2", verdict_color: "supported" }),
  ],
};
