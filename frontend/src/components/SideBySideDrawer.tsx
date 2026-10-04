import type { ReactNode } from "react";
import { ResolutionTrail } from "./ResolutionTrail";
import { VersionMismatchTimeline } from "./VersionMismatchTimeline";
import { highlightEvidencePassage } from "../lib/highlightEvidence";
import { ReceiptCard } from "./ReceiptCard";
import { WitnessMatrix } from "./WitnessMatrix";
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
  onRerunNli?: () => void;
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
  onRerunNli,
  onRerunCitation,
  onClose,
}: Props) {
  const context = citation.inline_markers?.[0]?.context_window ?? "No inline context captured.";
  const claim = citation.claim_user_corrected ?? citation.extracted_claim;
  const highlightClaim = claim && context.includes(claim);

  return (
    <div className="fixed inset-0 z-40 flex items-stretch justify-end bg-zinc-900/30 backdrop-blur-sm">
      <div className="flex h-full w-full max-w-6xl flex-col border-l border-zinc-200 bg-white shadow-2xl">
        <header className="flex items-center justify-between border-b border-zinc-200 px-5 py-4">
          <div>
            <p className="font-audit text-[10px] uppercase tracking-wide text-zinc-400">
              Citation #{citation.index}
            </p>
            <h3 className="mt-0.5 text-base font-semibold text-zinc-900">
              {citation.bibliography.title ?? "Untitled reference"}
            </h3>
          </div>
          <button
            type="button"
            onMouseDown={(event) => {
              event.preventDefault();
              onClose();
            }}
            className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-600 hover:bg-zinc-50 transition-colors"
          >
            Close
          </button>
        </header>

        <div className="grid min-h-0 flex-1 grid-cols-1 gap-0 lg:grid-cols-[1fr_0.9fr_1fr]">
          <Panel title="Manuscript context">
            <p className="text-sm leading-relaxed text-zinc-700">
              {highlightClaim ? (
                <>
                  {context.split(claim).map((part, index, parts) => (
                    <span key={index}>
                      {part}
                      {index < parts.length - 1 && (
                        <mark className="rounded bg-amber-100 px-0.5 text-amber-800">{claim}</mark>
                      )}
                    </span>
                  ))}
                </>
              ) : (
                context
              )}
            </p>
            <p className="mt-4 text-xs text-zinc-400">Bibliography entry</p>
            <p className="mt-1 font-audit text-xs text-zinc-500">{citation.bibliography.raw}</p>
          </Panel>

          <Panel title="Verdict & claim">
            <VerdictBadge citation={citation} />
            {citation.evidence_provenance && (
              <p className="mt-2 font-audit text-[10px] text-zinc-400">{citation.evidence_provenance}</p>
            )}
            <p className="mt-3 text-xs text-zinc-400">Hallucination type</p>
            <p className="font-audit text-sm text-zinc-800">{citation.hallucination_type}</p>
            {citation.title_edit_distance != null && (
              <p className="mt-1 text-xs text-zinc-500">
                Title edit distance: {citation.title_edit_distance}%
              </p>
            )}
            {citation.confidence && (
              <p className="mt-1 text-xs text-zinc-500">
                Confidence:{" "}
                <span className="font-audit uppercase font-medium">{citation.confidence}</span>
              </p>
            )}
            {citation.abstract_only_caveat && (
              <p className="mt-3 rounded-lg border border-sky-200 bg-sky-50 p-2 text-xs text-sky-900">
                {citation.abstract_only_caveat}
              </p>
            )}
            {citation.quantitative_caveat && (
              <p className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-2 text-xs text-amber-800">
                {citation.quantitative_caveat}
              </p>
            )}
            {citation.version_mismatch && (
              <VersionMismatchTimeline info={citation.version_mismatch} />
            )}
            <div className="mt-4">
              <p className="text-xs text-zinc-400">Witness matrix</p>
              <div className="mt-2">
                <WitnessMatrix citation={citation} />
              </div>
              {citation.scholar_limitation && (
                <p className="mt-2 rounded-lg border border-zinc-200 bg-zinc-50 p-2 text-xs text-zinc-600">
                  {citation.scholar_limitation}
                </p>
              )}
              {citation.author_presence_note && (
                <p className="mt-2 text-xs text-zinc-500">{citation.author_presence_note}</p>
              )}
            </div>
            <div className="mt-4">
              <p className="text-xs text-zinc-400">Resolution sources</p>
              <div className="mt-2 max-h-40 overflow-y-auto">
                <ResolutionTrail citation={citation} compact />
              </div>
            </div>
            {(citation.serpapi_receipts?.length || citation.scholar?.receipts?.length) ? (
              <div className="mt-4 space-y-2">
                <p className="text-xs text-zinc-400">SerpApi receipts</p>
                {(citation.serpapi_receipts ?? citation.scholar?.receipts ?? []).map((receipt) => (
                  <ReceiptCard key={receipt.call_id} receipt={receipt} />
                ))}
              </div>
            ) : null}
            <label className="mt-4 block text-xs text-zinc-500">
              Intent
              <select
                className="papyrus-input mt-1 w-full font-audit text-sm"
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
            <label className="mt-3 block text-xs text-zinc-500">
              Claim under test
              <textarea
                className="papyrus-input mt-1 w-full resize-none font-audit text-sm"
                rows={4}
                value={claimDraft}
                onChange={(e) => onClaimDraft(e.target.value)}
              />
            </label>
            <div className="mt-2 flex flex-wrap items-center gap-3">
              {citation.claim_pending_review && onApproveClaim ? (
                <>
                  <button
                    type="button"
                    onClick={onApproveClaim}
                    className="papyrus-btn papyrus-btn-accent px-3 py-1.5 text-xs"
                  >
                    Approve claim
                  </button>
                  <button
                    type="button"
                    onClick={onSaveClaim}
                    className="text-xs font-medium text-zinc-500 underline-offset-2 hover:text-zinc-800 hover:underline"
                  >
                    Save edits only
                  </button>
                </>
              ) : (
                <button
                  type="button"
                  onClick={onSaveClaim}
                  className="papyrus-btn papyrus-btn-accent px-3 py-1.5 text-xs"
                >
                  Save & re-check
                </button>
              )}
              {onRerunNli && citation.intent === "evidentiary" && (
                <button
                  type="button"
                  onClick={onRerunNli}
                  className="text-xs font-medium text-zinc-500 underline-offset-2 hover:text-zinc-800 hover:underline"
                >
                  Rerun NLI
                </button>
              )}
              {onRerunCitation && (
                <button
                  type="button"
                  onClick={onRerunCitation}
                  className="text-xs font-medium text-zinc-500 underline-offset-2 hover:text-zinc-800 hover:underline"
                >
                  Re-run resolution
                </button>
              )}
            </div>
            {citation.extracted_claim && citation.claim_user_corrected && (
              <p className="mt-3 text-xs text-zinc-400">
                Original extraction:{" "}
                <span className="text-zinc-600">{citation.extracted_claim}</span>
              </p>
            )}
            {claim && (
              <p className="mt-3 text-xs text-zinc-500">
                Alignment:{" "}
                <span className="text-zinc-700 font-medium">
                  {citation.claim_alignment_verdict ?? "-"}
                </span>
              </p>
            )}
          </Panel>

          <Panel title="Evidence drawer">
            {citation.evidence_tier === "tier_2" && (
              <p className="mb-3 rounded-lg border border-blue-200 bg-blue-50 p-2 text-xs text-blue-700">
                Analysis based on abstract only — full text unavailable. Specific numerical claims, methods details, and supplementary results cannot be verified from the abstract alone.
              </p>
            )}
            {citation.evidence_tier === "tier_3" && (
              <p className="mb-3 rounded-lg border border-sky-200 bg-sky-50 p-2 text-xs text-sky-700">
                Metadata-only resolution - existence may be confirmed but claim alignment is
                limited to title and abstract fields when present.
              </p>
            )}
            {citation.evidence_tier === "tier_4" || citation.verdict_color === "unresolvable" ? (
              <div className="mb-3 rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-xs text-zinc-600">
                <p className="font-semibold text-zinc-700">No document found in indexed sources.</p>
                <p className="mt-2 text-zinc-500">Sources queried with no match:</p>
                <ul className="mt-1 space-y-1 font-audit">
                  {citation.resolution_attempts.map((attempt, index) => (
                    <li key={`${attempt.source}-${index}`}>
                      {attempt.source}: {attempt.summary}
                    </li>
                  ))}
                </ul>
                {citation.exa_signal && (
                  <p className="mt-2 text-amber-700">{citation.exa_signal}</p>
                )}
              </div>
            ) : (
              <ul className="space-y-1 font-audit text-xs">
                {citation.resolution_attempts.map((attempt, index) => (
                  <li key={`${attempt.source}-${index}`} className="text-zinc-600">
                    <span className={attempt.success ? "text-emerald-600" : "text-zinc-400"}>
                      {attempt.success ? "+" : "-"}
                    </span>{" "}
                    {attempt.source}: {attempt.summary}
                  </li>
                ))}
              </ul>
            )}
            {citation.evidence_provenance && (
              <p className="mt-3 font-audit text-[10px] uppercase tracking-wide text-zinc-400">
                {citation.evidence_provenance}
                {citation.evidence_retrieved_at && (
                  <span className="ml-2 normal-case text-zinc-400">
                    · retrieved {new Date(citation.evidence_retrieved_at).toLocaleString()}
                  </span>
                )}
              </p>
            )}
            {citation.evidence_passage ? (
              <p className="mt-4 rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-xs leading-relaxed text-zinc-700">
                {highlightEvidencePassage(citation.evidence_passage.slice(0, 1200), claim)}
              </p>
            ) : (
              citation.evidence_tier !== "tier_4" &&
              citation.verdict_color !== "unresolvable" && (
                <p className="mt-4 text-xs text-zinc-400">No evidence passage retrieved yet.</p>
              )
            )}
            {citation.exa_signal &&
              citation.evidence_tier !== "tier_4" &&
              citation.verdict_color !== "unresolvable" && (
                <p className="mt-3 text-xs text-zinc-500">{citation.exa_signal}</p>
              )}
            {citation.source_verify_url && (
              <a
                href={citation.source_verify_url}
                target="_blank"
                rel="noreferrer"
                className="papyrus-link mt-3 inline-block text-sm"
              >
                Verify source
              </a>
            )}
            {citation.oa_pdf_url && (
              <a
                href={citation.oa_pdf_url}
                target="_blank"
                rel="noreferrer"
                className="papyrus-link mt-2 block text-sm"
              >
                Open access PDF
              </a>
            )}
          </Panel>
        </div>

        <footer className="border-t border-zinc-200 px-5 py-2.5 text-xs text-zinc-400">
          Audit {audit.id.slice(0, 8)} · Tier {citation.evidence_tier.replace("tier_", "")}
        </footer>
      </div>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="min-h-0 overflow-y-auto border-b border-zinc-100 p-5 lg:border-b-0 lg:border-r">
      <h4 className="font-audit text-[10px] uppercase tracking-wide text-zinc-400">{title}</h4>
      <div className="mt-3">{children}</div>
    </section>
  );
}

function VerdictBadge({ citation }: { citation: CitationRecord }) {
  const color =
    citation.verdict_color === "supported"
      ? "text-emerald-600"
      : citation.verdict_color === "failure"
        ? "text-red-600"
        : "text-zinc-700";
  const needsReview =
    citation.needs_human_review ||
    (citation.intent === "evidentiary" &&
      citation.confidence &&
      ["medium", "low"].includes(citation.confidence));
  return (
    <div>
      <p className={`font-audit text-2xl font-semibold uppercase ${color}`}>
        {citation.claim_alignment_verdict ?? citation.verdict_color}
      </p>
      {needsReview && (
        <p className="mt-2 rounded-lg border border-amber-200 bg-amber-50 px-2 py-1.5 text-xs text-amber-700">
          Medium/low confidence - human review recommended
        </p>
      )}
    </div>
  );
}
