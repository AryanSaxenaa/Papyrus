import { useEffect, useState } from "react";
import { ChevronDown } from "./landing/LandingIcons";
import { SettingsIcon } from "./app/AppIcons";

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
  use_celery_bulk?: boolean;
  bulk_queue_mode?: string;
  celery_worker_available?: boolean;
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

type Props = {
  variant?: "default" | "app";
};

export function AdminPanel({ variant = "default" }: Props) {
  const [open, setOpen] = useState(false);
  const isApp = variant === "app";
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
    <div
      className={
        isApp
          ? "rounded-xl border border-zinc-100 bg-white"
          : "papyrus-card !p-4"
      }
    >
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className={`flex w-full items-center justify-between gap-3 text-left transition-colors ${
          isApp ? "px-4 py-3 hover:bg-zinc-50/80" : ""
        }`}
      >
        <span className="flex items-center gap-3 text-sm font-semibold text-zinc-800">
          {isApp && <SettingsIcon className="text-zinc-500" />}
          Admin & integrations
        </span>
        {isApp ? (
          <ChevronDown
            className={`h-4 w-4 text-zinc-400 transition-transform ${open ? "rotate-180" : ""}`}
          />
        ) : (
          <span className="font-audit text-xs text-zinc-500">{open ? "▾" : "▸"}</span>
        )}
      </button>
      {open && (
        <div className={`space-y-4 text-xs ${isApp ? "border-t border-zinc-100 px-5 pb-5 pt-4" : "mt-3"}`}>
          {config && (
            <div>
              <p className="font-audit text-[10px] uppercase tracking-wide text-zinc-400">Pipeline</p>
              <p className="mt-1 text-zinc-700">
                v{config.pipeline_version} · persistence {config.persistence_backend} · GROBID{" "}
                {config.grobid_enabled ? "on" : "off"}
              </p>
              <p className="mt-1 text-zinc-600">
                Bulk queue: {config.bulk_queue_mode ?? "unknown"}
                {config.use_celery_bulk !== undefined && (
                  <span className="text-zinc-400">
                    {" "}
                    (Celery {config.celery_worker_available ? "worker live" : "fallback to in-process"})
                  </span>
                )}
              </p>
              <ul className="mt-2 grid gap-1 sm:grid-cols-2">
                {Object.entries(config.integrations).map(([key, enabled]) => (
                  <li
                    key={key}
                    className="flex justify-between gap-2 rounded-lg bg-zinc-50 border border-zinc-100 px-2 py-1.5"
                  >
                    <span className="text-zinc-500">{key}</span>
                    <span className={enabled ? "text-emerald-600 font-medium" : "text-zinc-400"}>
                      {String(enabled)}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {limits && (
            <div>
              <p className="font-audit text-[10px] uppercase tracking-wide text-zinc-400">
                API budgets (today)
              </p>
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
                        critical
                          ? "text-red-600"
                          : warn
                            ? "text-amber-600"
                            : "text-zinc-700"
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
              <p className="font-audit text-[10px] uppercase tracking-wide text-zinc-400">
                Recent corrections (ground truth)
              </p>
              <ul className="mt-2 max-h-36 space-y-2 overflow-y-auto">
                {corrections.map((row) => (
                  <li
                    key={`${row.audit_id}-${row.citation_index}-${row.field}`}
                    className="rounded-lg border border-zinc-100 bg-zinc-50 p-2"
                  >
                    <p className="text-zinc-500">
                      Audit {row.audit_id.slice(0, 8)} · #{row.citation_index} · {row.field}
                    </p>
                    <p className="mt-1 text-zinc-400 line-through">
                      {row.original_value?.slice(0, 80) ?? "-"}
                    </p>
                    <p className="text-zinc-700">{row.corrected_value.slice(0, 120)}</p>
                  </li>
                ))}
              </ul>
            </div>
          )}
          <a
            href="/api/admin/corrections/export.csv"
            className="inline-block rounded-lg border border-zinc-300 px-3 py-1.5 text-zinc-600 hover:bg-zinc-50 transition-colors"
          >
            Export corrections CSV
          </a>
        </div>
      )}
    </div>
  );
}
