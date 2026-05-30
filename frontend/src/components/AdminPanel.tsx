import { useEffect, useState } from "react";

type RateLimitRow = {
  used_today: number;
  daily_budget: number;
  remaining: number;
  utilization_percent?: number;
};

type ConfigPayload = {
  pipeline_version: string;
  persistence_backend: string;
  grobid_enabled: boolean;
  integrations: Record<string, boolean | string>;
};

type CorrectionRow = {
  audit_id: string;
  citation_index: number;
  field: string;
  original_value?: string | null;
  corrected_value: string;
  created_at?: string | null;
};

export function AdminPanel() {
  const [open, setOpen] = useState(false);
  const [limits, setLimits] = useState<Record<string, RateLimitRow> | null>(null);
  const [config, setConfig] = useState<ConfigPayload | null>(null);
  const [corrections, setCorrections] = useState<CorrectionRow[]>([]);

  useEffect(() => {
    if (!open) return;
    void Promise.all([
      fetch("/api/admin/rate-limits").then((r) => (r.ok ? r.json() : null)),
      fetch("/api/admin/config").then((r) => (r.ok ? r.json() : null)),
      fetch("/api/admin/corrections?limit=15").then((r) => (r.ok ? r.json() : null)),
    ]).then(([limitsData, configData, correctionsData]) => {
      setLimits(limitsData?.sources ?? null);
      setConfig(configData);
      setCorrections(correctionsData?.corrections ?? []);
    });
  }, [open]);

  return (
    <div className="rounded-xl border border-white/10 bg-[var(--papyrus-panel)] p-4">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="font-audit text-sm uppercase tracking-wide text-[var(--papyrus-muted)]"
      >
        Admin & integrations {open ? "▾" : "▸"}
      </button>
      {open && (
        <div className="mt-3 space-y-4 text-xs">
          {config && (
            <div>
              <p className="font-audit uppercase text-[var(--papyrus-muted)]">Pipeline</p>
              <p className="mt-1 text-stone-300">
                v{config.pipeline_version} · persistence {config.persistence_backend} · GROBID{" "}
                {config.grobid_enabled ? "on" : "off"}
              </p>
              <ul className="mt-2 grid gap-1 sm:grid-cols-2">
                {Object.entries(config.integrations).map(([key, enabled]) => (
                  <li key={key} className="flex justify-between gap-2 rounded bg-black/20 px-2 py-1">
                    <span className="text-stone-400">{key}</span>
                    <span className={enabled ? "text-emerald-300" : "text-stone-500"}>
                      {String(enabled)}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {limits && (
            <div>
              <p className="font-audit uppercase text-[var(--papyrus-muted)]">API budgets (today)</p>
              <ul className="mt-2 space-y-1 font-audit">
                {Object.entries(limits).map(([source, row]) => {
                  const utilization =
                    row.utilization_percent ??
                    (row.daily_budget ? (row.used_today / row.daily_budget) * 100 : 0);
                  const warn = utilization >= 80;
                  const critical = utilization >= 95;
                  return (
                    <li
                      key={source}
                      className={`flex justify-between gap-2 ${
                        critical ? "text-amber-300" : warn ? "text-amber-200/90" : "text-stone-300"
                      }`}
                    >
                      <span>
                        {source}
                        {warn && (
                          <span className="ml-1 text-[10px] uppercase tracking-wide opacity-80">
                            {critical ? "critical" : "high"}
                          </span>
                        )}
                      </span>
                      <span>
                        {row.used_today}/{row.daily_budget}
                        {warn && ` (${utilization.toFixed(0)}%)`}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
          {corrections.length > 0 && (
            <div>
              <p className="font-audit uppercase text-[var(--papyrus-muted)]">Recent corrections (ground truth)</p>
              <ul className="mt-2 max-h-36 space-y-2 overflow-y-auto">
                {corrections.map((row) => (
                  <li key={`${row.audit_id}-${row.citation_index}-${row.field}`} className="rounded bg-black/20 p-2">
                    <p className="text-stone-400">
                      Audit {row.audit_id.slice(0, 8)} · #{row.citation_index} · {row.field}
                    </p>
                    <p className="mt-1 text-stone-500 line-through">{row.original_value?.slice(0, 80) ?? "—"}</p>
                    <p className="text-stone-200">{row.corrected_value.slice(0, 120)}</p>
                  </li>
                ))}
              </ul>
            </div>
          )}
          <a
            href="/api/admin/corrections/export.csv"
            className="inline-block rounded border border-stone-600 px-3 py-1 text-stone-200 hover:bg-white/5"
          >
            Export corrections CSV
          </a>
        </div>
      )}
    </div>
  );
}
