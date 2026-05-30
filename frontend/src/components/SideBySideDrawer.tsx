import type { ReactNode } from "react";
import type { AuditRun, CitationRecord, VersionMismatchInfo } from "../types";

const INTENT_OPTIONS = ["evidentiary", "methodological", "contrastive", "background"];

type Props = {
  audit: AuditRun;
  citation: CitationRecord;
  claimDraft: string;
  onClaimDraft: (value: string) => void;
  onSaveIntent: (intent: string) => void;
  onSaveClaim: () => void;
  onClose: () => void;
};

export function SideBySideDrawer({
  audit,
  citation,
  claimDraft,
  onClaimDraft,
  onSaveIntent,
  onSaveClaim,
  onClose,
}: Props) {
  const context = citation.inline_markers?.[0]?.context_window ?? "No inline context captured.";
  const claim = citation.claim_user_corrected ?? citation.extracted_claim;

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
            <p className="text-sm leading-relaxed text-stone-200">{context}</p>
            <p className="mt-4 text-xs text-[var(--papyrus-muted)]">Bibliography entry</p>
            <p className="mt-1 font-audit text-xs text-stone-400">{citation.bibliography.raw}</p>
          </Panel>

          <Panel title="Verdict & claim">
            <VerdictBadge citation={citation} />
            <p className="mt-3 text-xs text-[var(--papyrus-muted)]">Hallucination type</p>
            <p className="font-audit text-sm">{citation.hallucination_type}</p>
            {citation.quantitative_caveat && (
              <p className="mt-3 rounded border border-amber-700/40 bg-amber-950/30 p-2 text-xs text-amber-100">
                {citation.quantitative_caveat}
              </p>
            )}
            {citation.version_mismatch && (
              <VersionTimeline info={citation.version_mismatch} />
            )}
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
            <button
              type="button"
              onClick={onSaveClaim}
              className="mt-2 rounded border border-emerald-700/50 px-3 py-1 text-xs font-semibold text-emerald-200"
            >
              Rerun alignment
            </button>
            {claim && (
              <p className="mt-3 text-xs text-stone-400">
                Alignment: <span className="text-stone-200">{citation.claim_alignment_verdict ?? "—"}</span>
              </p>
            )}
          </Panel>

          <Panel title="Evidence drawer">
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
            {citation.evidence_passage ? (
              <p className="mt-4 rounded border border-white/10 bg-black/20 p-2 text-xs leading-relaxed text-stone-200">
                {citation.evidence_passage.slice(0, 1200)}
              </p>
            ) : (
              <p className="mt-4 text-xs text-[var(--papyrus-muted)]">No evidence passage retrieved yet.</p>
            )}
            {citation.exa_signal && <p className="mt-3 text-xs text-stone-400">{citation.exa_signal}</p>}
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
  return (
    <p className={`font-audit text-2xl font-semibold uppercase ${color}`}>
      {citation.claim_alignment_verdict ?? citation.verdict_color}
    </p>
  );
}

function VersionTimeline({ info }: { info: VersionMismatchInfo }) {
  const entries = [info.preprint, ...info.revisions, info.published].filter(Boolean);
  return (
    <div className="mt-4 space-y-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-amber-200">Version timeline</p>
      {info.material_difference && (
        <p className="text-xs text-amber-100">Material difference detected between preprint and published versions.</p>
      )}
      {entries.map((entry) => (
        <div key={entry!.label} className="border-l-2 border-amber-700/60 pl-3">
          <p className="font-audit text-xs text-amber-300">{entry!.label}</p>
          {entry!.date && <p className="text-[10px] text-stone-500">{entry!.date}</p>}
          {entry!.title && <p className="mt-1 text-xs font-semibold">{entry!.title}</p>}
          {entry!.abstract && (
            <p className="mt-1 text-[11px] leading-relaxed text-stone-400">{entry!.abstract.slice(0, 280)}…</p>
          )}
        </div>
      ))}
    </div>
  );
}
