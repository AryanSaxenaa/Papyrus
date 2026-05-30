export type VersionEntry = {
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

export type AuditRun = {
  id: string;
  paper_title?: string | null;
  status: string;
  pipeline_version: string;
  coverage: {
    total: number;
    tier_1: number;
    tier_2: number;
    tier_3: number;
    tier_4: number;
    coverage_percent: number;
    coverage_confidence?: string;
  };
  risk_confidence?: string;
  failures: {
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
  risk_level: string;
  limitations?: {
    field_coverage_note?: string | null;
    misappropriation_not_detected?: string;
    nli_quantitative_caveat?: string;
    out_of_scope?: string[];
    unresolvable_count?: number;
  } | null;
  paper_text?: string | null;
  citations: CitationRecord[];
};

export type BulkDashboard = {
  job: {
    id: string;
    status: string;
    total: number;
    completed: number;
    failed: number;
    estimated_seconds_remaining?: number | null;
    avg_seconds_per_paper?: number | null;
  };
  note?: string;
  papers: Array<{
    audit_id: string;
    title?: string | null;
    status: string;
    coverage_percent: number;
    confirmed_failure_rate: number;
    risk_level: string;
  }>;
};

export type CitationRecord = {
  id: string;
  index: number;
  bibliography: {
    raw: string;
    title?: string | null;
    year?: number | null;
    doi?: string | null;
    authors: string[];
  };
  intent: string;
  evidence_tier: string;
  hallucination_type: string;
  verdict_color: string;
  status: string;
  inline_markers?: Array<{ marker: string; context_window: string }>;
  extracted_claim?: string | null;
  claim_user_corrected?: string | null;
  claim_pending_review?: boolean;
  evidence_passage?: string | null;
  quantitative_caveat?: string | null;
  claim_alignment_verdict?: string | null;
  title_edit_distance?: number | null;
  confidence?: string | null;
  version_mismatch?: VersionMismatchInfo | null;
  exa_signal?: string | null;
  source_verify_url?: string | null;
  oa_pdf_url?: string | null;
  resolution_attempts: Array<{
    source: string;
    query: string;
    success: boolean;
    summary: string;
  }>;
};

export type StreamEvent = {
  ts: string;
  type: string;
  message: string;
  citation_index?: number;
  [key: string]: unknown;
};

export type HeatmapFilter =
  | "all"
  | "supported"
  | "contradictions"
  | "cannot_assess"
  | "failures"
  | "unresolvable"
  | "retracted";
