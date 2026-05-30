import type { ReactNode } from "react";
import { ResolutionTrail } from "./ResolutionTrail";
import { VersionMismatchTimeline } from "./VersionMismatchTimeline";
import { highlightEvidencePassage } from "../lib/highlightEvidence";
import type { AuditRun, CitationRecord } from "../types";

const INTENT_OPTIONS = ["evidentiary", "methodological", "contrastive", "background"];

type Props = {
  audit: AuditRun;
  citation: CitationRecord;
  claimDraft: string;
  onClaimDraft: (value: string) => void;
  onSaveIntent: (intent: string) => void;
  onSaveClaim: () => void;
  onApproveClaim?: () => void;
  onRerunCitation?: () => void;
  onClose: () => void;
};

export function SideBySideDrawer({
  audit,
  citation,
  claimDraft,
  onClaimDraft,
  onSaveIntent,
  onSaveClaim,
  onApproveClaim,
  onRerunCitation,
  onClose,
}: Props) {
  const context = citation.inline_markers?.[0]?.context_window ?? "No inline context captured.";
  const claim = citation.claim_user_corrected ?? citation.extracted_claim;
  const highlightClaim = claim && context.includes(claim);

  return (
    <div className="fixed inset-0 z-40 flex items-stretch justify-end bg-black/60 backdrop-blur-sm">
      <div className="flex h-full w-full max-w-6xl flex-col border-l border-white/10 bg-[var(--papyrus-panel)] shadow-2xl">
        <header className="flex items-center justify-between border-b border-white/10 px-4 py-3">
          <div>
            <p className="font-audit text-xs uppercase tracking-wide text-[var(--papyrus-muted)]">
              Citation #{citation.index}
            </p>
            <h3 className="text-lg font-semibold">{citation.bibliography.title ?? "Untitled reference"}</h3>
          </div>
          <button type="button" onClick={onClose} className="rounded border border-white/15 px-3 py-1 text-sm">
            Close
          </button>
        </header>

        <div className="grid min-h-0 flex-1 grid-cols-1 gap-0 lg:grid-cols-[1fr_0.9fr_1fr]">
          <Panel title="Manuscript context">
            <p className="text-sm leading-relaxed text-stone-200">
              {highlightClaim ? (
                <>
                  {context.split(claim).map((part, index, parts) => (
                    <span key={index}>
                      {part}
                      {index < parts.length - 1 && (
                        <mark className="rounded bg-amber-900/60 px-1 text-amber-50">{claim}</mark>
                      )}
                    </span>
                  ))}
                </>
              ) : (
                context
              )}
            </p>
            <p className="mt-4 text-xs text-[var(--papyrus-muted)]">Bibliography entry</p>
            <p className="mt-1 font-audit text-xs text-stone-400">{citation.bibliography.raw}</p>
          </Panel>

          <Panel title="Verdict & claim">
            <VerdictBadge citation={citation} />
            {citation.evidence_provenance && (
              <p className="mt-2 font-audit text-[10px] text-stone-500">{citation.evidence_provenance}</p>
            )}
            <p className="mt-3 text-xs text-[var(--papyrus-muted)]">Hallucination type</p>
            <p className="font-audit text-sm">{citation.hallucination_type}</p>
            {citation.title_edit_distance != null && (
              <p className="mt-1 text-xs text-stone-400">
                Title edit distance: {citation.title_edit_distance}%
              </p>
            )}
            {citation.confidence && (
              <p className="mt-1 text-xs text-stone-400">
                Confidence: <span className="font-audit uppercase">{citation.confidence}</span>
              </p>
            )}
            {citation.quantitative_caveat && (
              <p className="mt-3 rounded border border-amber-700/40 bg-amber-950/30 p-2 text-xs text-amber-100">
                {citation.quantitative_caveat}
              </p>
            )}
            {citation.version_mismatch && (
              <VersionMismatchTimeline info={citation.version_mismatch} />
            )}
            <div className="mt-4">
              <p className="text-xs text-[var(--papyrus-muted)]">Resolution sources</p>
              <div className="mt-2 max-h-40 overflow-y-auto">
                <ResolutionTrail citation={citation} compact />
              </div>
            </div>
            <label className="mt-4 block text-xs text-[var(--papyrus-muted)]">
              Intent
              <select
                className="mt-1 w-full rounded border border-white/15 bg-black/30 px-2 py-1 font-audit text-sm"
                value={citation.intent}
                onChange={(e) => onSaveIntent(e.target.value)}
              >
                {INTENT_OPTIONS.map((intent) => (
                  <option key={intent} value={intent}>
                    {intent}
                  </option>
                ))}
              </select>
            </label>
            <label className="mt-3 block text-xs text-[var(--papyrus-muted)]">
              Claim under test
              <textarea
                className="mt-1 w-full rounded border border-white/15 bg-black/30 px-2 py-1 font-audit text-sm"
                rows={4}
                value={claimDraft}
                onChange={(e) => onClaimDraft(e.target.value)}
              />
            </label>
            <div className="mt-2 flex flex-wrap gap-2">
              {citation.claim_pending_review && onApproveClaim && (
                <button
                  type="button"
                  onClick={onApproveClaim}
                  className="rounded border border-amber-600/60 bg-amber-950/50 px-3 py-1 text-xs font-semibold text-amber-100"
                >
                  Approve claim & run NLI
                </button>
              )}
              <button
                type="button"
                onClick={onSaveClaim}
                className="rounded border border-emerald-700/50 px-3 py-1 text-xs font-semibold text-emerald-200"
              >
                Rerun NLI
              </button>
              {onRerunCitation && (
                <button
                  type="button"
                  onClick={onRerunCitation}
                  className="rounded border border-stone-600 px-3 py-1 text-xs text-stone-300"
                >
                  Rerun resolution
                </button>
              )}
            </div>
            {citation.extracted_claim && citation.claim_user_corrected && (
              <p className="mt-3 text-xs text-stone-500">
                Original extraction:{" "}
                <span className="text-stone-300">{citation.extracted_claim}</span>
              </p>
            )}
            {claim && (
              <p className="mt-3 text-xs text-stone-400">
                Alignment: <span className="text-stone-200">{citation.claim_alignment_verdict ?? "—"}</span>
              </p>
            )}
          </Panel>

          <Panel title="Evidence drawer">
            {citation.evidence_tier === "tier_2" && (
              <p className="mb-3 rounded border border-slate-600/50 bg-slate-900/40 p-2 text-xs text-slate-200">
                Analysis based on abstract only — full text unavailable. Numerical claims in the body
                cannot be verified from the abstract alone.
              </p>
            )}
            {citation.evidence_tier === "tier_3" && (
              <p className="mb-3 rounded border border-sky-800/40 bg-sky-950/30 p-2 text-xs text-sky-100">
                Metadata-only resolution — existence may be confirmed but claim alignment is limited to
                title and abstract fields when present.
              </p>
            )}
            {citation.evidence_tier === "tier_4" || citation.verdict_color === "unresolvable" ? (
              <div className="mb-3 rounded border border-stone-600/50 bg-stone-900/40 p-2 text-xs text-stone-300">
                <p className="font-semibold text-stone-200">No document found in indexed sources.</p>
                <p className="mt-2 text-[var(--papyrus-muted)]">Sources queried with no match:</p>
                <ul className="mt-1 space-y-1 font-audit">
                  {citation.resolution_attempts.map((attempt, index) => (
                    <li key={`${attempt.source}-${index}`}>
                      {attempt.source}: {attempt.summary}
                    </li>
                  ))}
                </ul>
                {citation.exa_signal && <p className="mt-2 text-amber-100/90">{citation.exa_signal}</p>}
              </div>
            ) : (
              <ul className="space-y-1 font-audit text-xs">
                {citation.resolution_attempts.map((attempt, index) => (
                  <li key={`${attempt.source}-${index}`} className="text-stone-300">
                    <span className={attempt.success ? "text-emerald-400" : "text-stone-500"}>
                      {attempt.success ? "✓" : "✗"}
                    </span>{" "}
                    {attempt.source}: {attempt.summary}
                  </li>
                ))}
              </ul>
            )}
            {citation.evidence_provenance && (
              <p className="mt-3 font-audit text-[10px] uppercase tracking-wide text-stone-500">
                {citation.evidence_provenance}
                {citation.evidence_retrieved_at && (
                  <span className="ml-2 normal-case text-stone-600">
                    · retrieved {new Date(citation.evidence_retrieved_at).toLocaleString()}
                  </span>
                )}
              </p>
            )}
            {citation.evidence_passage ? (
              <p className="mt-4 rounded border border-white/10 bg-black/20 p-2 text-xs leading-relaxed text-stone-200">
                {highlightEvidencePassage(citation.evidence_passage.slice(0, 1200), claim)}
              </p>
            ) : (
              citation.evidence_tier !== "tier_4" &&
              citation.verdict_color !== "unresolvable" && (
                <p className="mt-4 text-xs text-[var(--papyrus-muted)]">No evidence passage retrieved yet.</p>
              )
            )}
            {citation.exa_signal &&
              citation.evidence_tier !== "tier_4" &&
              citation.verdict_color !== "unresolvable" && (
                <p className="mt-3 text-xs text-stone-400">{citation.exa_signal}</p>
              )}
            {citation.source_verify_url && (
              <a
                href={citation.source_verify_url}
                target="_blank"
                rel="noreferrer"
                className="mt-3 inline-block text-sm text-emerald-300 underline"
              >
                Verify source
              </a>
            )}
            {citation.oa_pdf_url && (
              <a
                href={citation.oa_pdf_url}
                target="_blank"
                rel="noreferrer"
                className="mt-2 block text-sm text-emerald-300 underline"
              >
                Open access PDF
              </a>
            )}
          </Panel>
        </div>

        <footer className="border-t border-white/10 px-4 py-2 text-xs text-[var(--papyrus-muted)]">
          Audit {audit.id.slice(0, 8)} · Tier {citation.evidence_tier.replace("tier_", "")}
        </footer>
      </div>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="min-h-0 overflow-y-auto border-b border-white/5 p-4 lg:border-b-0 lg:border-r">
      <h4 className="font-audit text-xs uppercase tracking-wide text-[var(--papyrus-muted)]">{title}</h4>
      <div className="mt-3">{children}</div>
    </section>
  );
}

function VerdictBadge({ citation }: { citation: CitationRecord }) {
  const color =
    citation.verdict_color === "supported"
      ? "text-emerald-300"
      : citation.verdict_color === "failure"
        ? "text-red-300"
        : "text-stone-300";
  const needsReview =
    citation.intent === "evidentiary" &&
    citation.confidence &&
    ["medium", "low"].includes(citation.confidence);
  return (
    <div>
      <p className={`font-audit text-2xl font-semibold uppercase ${color}`}>
        {citation.claim_alignment_verdict ?? citation.verdict_color}
      </p>
      {needsReview && (
        <p className="mt-2 rounded border border-amber-700/50 bg-amber-950/40 px-2 py-1 text-xs text-amber-100">
          Medium/low confidence — human review recommended
        </p>
      )}
    </div>
  );
}
