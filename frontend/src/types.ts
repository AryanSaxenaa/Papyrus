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
  };
  failures: {
    confirmed_failure_rate: number;
    type_1: number;
    type_2: number;
    type_6: number;
    type_7: number;
    retraction: number;
  };
  risk_level: string;
  citations: CitationRecord[];
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
  extracted_claim?: string | null;
  claim_user_corrected?: string | null;
  evidence_passage?: string | null;
  quantitative_caveat?: string | null;
  claim_alignment_verdict?: string | null;
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
  [key: string]: unknown;
};

export type HeatmapFilter = "all" | "failures" | "unresolvable" | "retracted";
