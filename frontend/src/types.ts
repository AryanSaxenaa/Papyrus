/** Mirrors backend `app.domain.models` / API JSON shapes (wire format). */

type VersionEntry = {
  label: string;
  date?: string | null;
  title?: string | null;
  abstract?: string | null;
  source?: string | null;
};

export type VersionMismatchInfo = {
  preprint?: VersionEntry | null;
  published?: VersionEntry | null;
  revisions: VersionEntry[];
  material_difference: boolean;
};

export type BibliographyEntry = {
  index?: number;
  raw: string;
  title?: string | null;
  year?: number | null;
  doi?: string | null;
  authors: string[];
  journal?: string | null;
  volume?: string | null;
  issue?: string | null;
  pages?: string | null;
  url?: string | null;
};

export type InlineCitation = {
  marker: string;
  bibliography_index?: number;
  context_window: string;
};

export type ResolutionAttempt = {
  source: string;
  query: string;
  success: boolean;
  summary: string;
  payload?: Record<string, object> | null;
};

export type CoverageSummary = {
  total: number;
  tier_1: number;
  tier_2: number;
  tier_3: number;
  tier_4: number;
  coverage_percent: number;
  coverage_confidence?: string;
};

export type FailureSummary = {
  confirmed_failure_rate: number;
  supported: number;
  not_supported: number;
  cannot_assess: number;
  type_1: number;
  type_2: number;
  type_5: number;
  type_6: number;
  type_7: number;
  retraction: number;
  version_mismatch: number;
};

export type AuditLimitations = {
  field_coverage_note?: string | null;
  misappropriation_not_detected?: string;
  nli_quantitative_caveat?: string;
  out_of_scope?: string[];
};

export type CitationRecord = {
  id: string;
  index: number;
  bibliography: BibliographyEntry;
  intent: string;
  intent_user_override?: boolean;
  evidence_tier: string;
  hallucination_type: string;
  verdict_color: string;
  status: string;
  inline_markers?: InlineCitation[];
  extracted_claim?: string | null;
  claim_user_corrected?: string | null;
  claim_pending_review?: boolean;
  evidence_passage?: string | null;
  evidence_provenance?: string | null;
  evidence_retrieved_at?: string | null;
  quantitative_caveat?: string | null;
  quantitative_claim?: boolean;
  claim_alignment_verdict?: string | null;
  nli_verdict?: string;
  title_edit_distance?: number | null;
  confidence?: string | null;
  version_mismatch?: VersionMismatchInfo | null;
  exa_signal?: string | null;
  source_verify_url?: string | null;
  oa_pdf_url?: string | null;
  resolved_title?: string | null;
  resolved_doi?: string | null;
  resolved_year?: number | null;
  resolved_authors?: string[];
  retracted?: boolean;
  resolution_attempts: ResolutionAttempt[];
};

export type AuditRun = {
  id: string;
  paper_title?: string | null;
  status: string;
  error?: string | null;
  pipeline_version: string;
  created_at?: string;
  completed_at?: string | null;
  coverage: CoverageSummary;
  risk_confidence?: string;
  failures: FailureSummary;
  risk_level: string;
  limitations?: AuditLimitations | null;
  paper_text?: string | null;
  citations: CitationRecord[];
};

/** `GET /api/audits/summaries` row shape. */
export type AuditSummary = {
  id: string;
  paper_title?: string | null;
  status: string;
  coverage_percent: number;
  failure_rate: number;
  risk_level: string;
  citation_count: number;
  created_at?: string | null;
};

export type BulkAuditJob = {
  id: string;
  status: string;
  total: number;
  completed: number;
  failed: number;
  estimated_seconds_remaining?: number | null;
  avg_seconds_per_paper?: number | null;
  created_at?: string;
  started_at?: string | null;
  completed_at?: string | null;
  audit_ids?: string[];
  error?: string | null;
};

/** One row from `GET /api/bulk/{id}/dashboard`. */
export type BulkDashboardPaper = {
  audit_id: string;
  title?: string | null;
  first_author?: string | null;
  status: string;
  coverage_percent: number;
  confirmed_failure_rate: number;
  risk_level: string;
  resolvable_citations?: number;
  type_1?: number;
  type_2?: number;
  type_5?: number;
  type_6?: number;
  type_7?: number;
  retraction?: number;
  version_mismatch?: number;
};

export type BulkDashboard = {
  job: BulkAuditJob;
  note?: string;
  pending_papers?: number;
  papers: BulkDashboardPaper[];
};

export type StreamEvent = {
  ts: string;
  type: string;
  message: string;
  citation_index?: number;
  path?: string;
  bibliography_count?: number;
  inline_count?: number;
  coverage?: number;
  risk?: string;
  doi?: string;
  counts?: Record<string, number>;
  hallucination?: string;
  tier?: string;
  color?: string;
  claim?: string;
  intent?: string;
  error?: string;
  job_id?: string;
  completed?: number;
  failed?: number;
};

/** UI-only filter; not an API field. */
export type HeatmapFilter =
  | "all"
  | "supported"
  | "contradictions"
  | "cannot_assess"
  | "failures"
  | "unresolvable"
  | "retracted";
