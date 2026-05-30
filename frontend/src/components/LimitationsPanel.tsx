import type { AuditRun } from "../types";

type Props = {
  audit: AuditRun;
};

export function LimitationsPanel({ audit }: Props) {
  const limitations = audit.limitations;
  if (!limitations) return null;

  return (
    <div className="mt-4 rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-xs text-zinc-600">
      <p className="font-audit text-[10px] uppercase tracking-wide text-zinc-400">
        What this audit does not cover
      </p>
      {limitations.field_coverage_note && (
        <p className="mt-2 leading-relaxed">{limitations.field_coverage_note}</p>
      )}
      {limitations.misappropriation_not_detected && (
        <p className="mt-2 leading-relaxed">{limitations.misappropriation_not_detected}</p>
      )}
      {limitations.nli_quantitative_caveat && (
        <p className="mt-2 leading-relaxed text-amber-700">{limitations.nli_quantitative_caveat}</p>
      )}
      {limitations.out_of_scope && (
        <ul className="mt-2 list-inside list-disc space-y-1 text-zinc-500">
          {limitations.out_of_scope.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
