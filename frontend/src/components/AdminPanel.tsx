import { useEffect, useState } from "react";

type RateLimitRow = {
  used_today: number;
  daily_budget: number;
  remaining: number;
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
  const [reindexStatus, setReindexStatus] = useState<string | null>(null);
  const [schemaStats, setSchemaStats] = useState<Record<string, number | boolean> | null>(null);

  useEffect(() => {
    if (!open) return;
    void Promise.all([
      fetch("/api/admin/rate-limits").then((r) => (r.ok ? r.json() : null)),
      fetch("/api/admin/config").then((r) => (r.ok ? r.json() : null)),
      fetch("/api/admin/corrections?limit=15").then((r) => (r.ok ? r.json() : null)),
      fetch("/api/admin/schema/stats").then((r) => (r.ok ? r.json() : null)),
    ]).then(([limitsData, configData, correctionsData, schemaData]) => {
      setLimits(limitsData?.sources ?? null);
      setConfig(configData);
      setCorrections(correctionsData?.corrections ?? []);
      setSchemaStats(schemaData);
    });
  }, [open]);

  const onReindex = async () => {
    setReindexStatus("Reindexing…");
    const response = await fetch("/api/admin/citations/reindex", { method: "POST" });
    if (!response.ok) {
      setReindexStatus("Reindex failed (Postgres required).");
      return;
    }
    const data = (await response.json()) as { audits_indexed: number };
    setReindexStatus(`Indexed ${data.audits_indexed} completed audit(s).`);
  };

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
          {schemaStats?.postgres && (
            <div>
              <p className="font-audit uppercase text-[var(--papyrus-muted)]">Relational schema (v2)</p>
              <p className="mt-1 text-stone-400">
                {String(schemaStats.citations ?? 0)} citations · {String(schemaStats.resolution_attempts ?? 0)}{" "}
                attempts · {String(schemaStats.audit_events ?? 0)} events
              </p>
            </div>
          )}
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
                {Object.entries(limits).map(([source, row]) => (
                  <li key={source} className="flex justify-between gap-2 text-stone-300">
                    <span>{source}</span>
                    <span>
                      {row.used_today}/{row.daily_budget}
                    </span>
                  </li>
                ))}
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
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => void onReindex()}
              className="rounded border border-stone-600 px-3 py-1 text-stone-200 hover:bg-white/5"
            >
              Reindex citation analytics
            </button>
            {reindexStatus && <span className="text-stone-400">{reindexStatus}</span>}
            <a
              href="/api/admin/corrections/export.csv"
              className="rounded border border-stone-600 px-3 py-1 text-stone-200 hover:bg-white/5"
            >
              Export corrections CSV
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
