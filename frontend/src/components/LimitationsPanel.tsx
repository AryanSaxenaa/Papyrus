import type { AuditRun } from "../types";

type Props = {
  audit: AuditRun;
};

export function LimitationsPanel({ audit }: Props) {
  const limitations = audit.limitations;
  if (!limitations) return null;

  return (
    <div className="mt-4 rounded-md border border-white/10 bg-black/20 p-3 text-xs text-stone-300">
      <p className="font-audit text-[10px] uppercase tracking-wide text-[var(--papyrus-muted)]">
        What this audit does not cover
      </p>
      {limitations.field_coverage_note && (
        <p className="mt-2 leading-relaxed">{limitations.field_coverage_note}</p>
      )}
      {limitations.misappropriation_not_detected && (
        <p className="mt-2 leading-relaxed">{limitations.misappropriation_not_detected}</p>
      )}
      {limitations.nli_quantitative_caveat && (
        <p className="mt-2 leading-relaxed text-amber-100/90">{limitations.nli_quantitative_caveat}</p>
      )}
      {limitations.out_of_scope && (
        <ul className="mt-2 list-inside list-disc space-y-1 text-stone-400">
          {limitations.out_of_scope.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
