import { useCallback, useEffect, useMemo, useState } from "react";
import type { AuditRun, CitationRecord, StreamEvent } from "./types";

const verdictClass: Record<string, string> = {
  supported: "bg-[var(--papyrus-green)]",
  failure: "bg-[var(--papyrus-crimson)]",
  retraction: "bg-[var(--papyrus-crimson)] ring-2 ring-amber-400",
  cannot_assess: "bg-[var(--papyrus-steel)]",
  neutral: "bg-[var(--papyrus-grey)]",
  unresolvable: "bg-[#4a524e]",
  resolving: "bg-[var(--papyrus-amber)] animate-pulse",
  pending: "bg-[#2a312e]",
  amber: "bg-[var(--papyrus-amber)]",
};

export default function App() {
  const [audit, setAudit] = useState<AuditRun | null>(null);
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [selected, setSelected] = useState<CitationRecord | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshAudit = useCallback(async (id: string) => {
    const response = await fetch(`/api/audits/${id}`);
    if (!response.ok) return;
    setAudit(await response.json());
  }, []);

  useEffect(() => {
    if (!audit?.id || audit.status === "complete" || audit.status === "failed") return;
    const timer = window.setInterval(() => refreshAudit(audit.id), 2500);
    return () => window.clearInterval(timer);
  }, [audit?.id, audit?.status, refreshAudit]);

  useEffect(() => {
    if (!audit?.id) return;
    const source = new EventSource(`/api/audits/${audit.id}/events`);
    source.onmessage = (message) => {
      try {
        const payload = JSON.parse(message.data) as StreamEvent;
        setEvents((prev) => [...prev, payload]);
      } catch {
        // ignore malformed chunks
      }
    };
    source.onerror = () => source.close();
    return () => source.close();
  }, [audit?.id]);

  const onUpload = async (file: File) => {
    setUploading(true);
    setError(null);
    setEvents([]);
    setSelected(null);
    try {
      const body = new FormData();
      body.append("file", file);
      const response = await fetch("/api/audits", { method: "POST", body });
      if (!response.ok) throw new Error(await response.text());
      const created = (await response.json()) as AuditRun;
      setAudit(created);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const coverageBar = useMemo(() => {
    if (!audit) return null;
    const { coverage } = audit;
    const total = coverage.total || 1;
    const segments = [
      { label: "Tier 1", value: coverage.tier_1, color: "bg-emerald-700" },
      { label: "Tier 2", value: coverage.tier_2, color: "bg-emerald-900" },
      { label: "Tier 3", value: coverage.tier_3, color: "bg-slate-600" },
      { label: "Unresolvable", value: coverage.tier_4, color: "bg-stone-600" },
    ];
    return (
      <div className="flex h-3 overflow-hidden rounded-full border border-white/10">
        {segments.map((segment) => (
          <div
            key={segment.label}
            className={segment.color}
            style={{ width: `${(segment.value / total) * 100}%` }}
            title={`${segment.label}: ${segment.value}`}
          />
        ))}
      </div>
    );
  }, [audit]);

  return (
    <div className="min-h-screen">
      <header className="border-b border-white/10 bg-[var(--papyrus-panel)] px-6 py-5">
        <div className="mx-auto flex max-w-7xl flex-wrap items-end justify-between gap-4">
          <div>
            <p className="font-audit text-xs uppercase tracking-[0.2em] text-[var(--papyrus-muted)]">
              Citation integrity audit
            </p>
            <h1 className="text-3xl font-semibold tracking-tight">Papyrus</h1>
            <p className="mt-1 max-w-2xl text-sm text-[var(--papyrus-muted)]">
              Verifies whether references exist and whether evidentiary citations are supported.
              Does not detect AI authorship.
            </p>
          </div>
          <label className="cursor-pointer rounded-md border border-emerald-700/60 bg-emerald-950/40 px-4 py-2 text-sm font-semibold hover:bg-emerald-900/50">
            {uploading ? "Uploading…" : "Upload PDF"}
            <input
              type="file"
              accept="application/pdf"
              className="hidden"
              disabled={uploading}
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) void onUpload(file);
              }}
            />
          </label>
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl gap-6 px-6 py-6 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="space-y-4">
          {error && (
            <p className="rounded-md border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-200">
              {error}
            </p>
          )}

          {audit && (
            <div className="rounded-xl border border-white/10 bg-[var(--papyrus-panel)] p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold">{audit.paper_title ?? "Analyzing document…"}</h2>
                  <p className="font-audit text-xs text-[var(--papyrus-muted)]">
                    Status: {audit.status} · Pipeline {audit.pipeline_version}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-audit text-3xl font-semibold text-emerald-300">
                    {audit.coverage.coverage_percent}%
                  </p>
                  <p className="text-xs text-[var(--papyrus-muted)]">Coverage</p>
                  <p className="mt-2 font-audit text-sm uppercase text-amber-300">{audit.risk_level} risk</p>
                </div>
              </div>
              <div className="mt-4">{coverageBar}</div>
              <p className="mt-2 text-xs text-[var(--papyrus-muted)]">
                Risk is derived from confirmed failures among resolvable citations only.
              </p>
            </div>
          )}

          <div className="rounded-xl border border-white/10 bg-[var(--papyrus-panel)] p-4">
            <h3 className="font-audit text-sm uppercase tracking-wide text-[var(--papyrus-muted)]">
              Citation heatmap
            </h3>
            <div className="mt-3 grid grid-cols-[repeat(auto-fill,minmax(88px,1fr))] gap-2">
              {(audit?.citations ?? []).map((citation) => (
                <button
                  key={citation.id}
                  type="button"
                  onClick={() => setSelected(citation)}
                  className={`rounded-md border border-white/10 p-2 text-left transition hover:scale-[1.02] ${
                    verdictClass[citation.verdict_color] ?? verdictClass.pending
                  }`}
                >
                  <p className="font-audit text-xs opacity-80">#{citation.index}</p>
                  <p className="truncate text-sm font-semibold">
                    {citation.bibliography.authors[0] ?? "Unknown"}
                  </p>
                  <p className="text-xs opacity-80">{citation.bibliography.year ?? "—"}</p>
                </button>
              ))}
              {!audit?.citations?.length && (
                <p className="col-span-full text-sm text-[var(--papyrus-muted)]">
                  Upload a PDF to extract and verify citations.
                </p>
              )}
            </div>
          </div>

          {selected && (
            <div className="rounded-xl border border-white/10 bg-[var(--papyrus-panel)] p-4">
              <h3 className="font-audit text-sm uppercase tracking-wide text-[var(--papyrus-muted)]">
                Citation #{selected.index}
              </h3>
              <p className="mt-2 text-sm">{selected.bibliography.title ?? selected.bibliography.raw.slice(0, 240)}</p>
              <dl className="mt-3 grid grid-cols-2 gap-2 text-xs">
                <div>
                  <dt className="text-[var(--papyrus-muted)]">Intent</dt>
                  <dd className="font-audit">{selected.intent}</dd>
                </div>
                <div>
                  <dt className="text-[var(--papyrus-muted)]">Tier</dt>
                  <dd className="font-audit">{selected.evidence_tier}</dd>
                </div>
                <div>
                  <dt className="text-[var(--papyrus-muted)]">Hallucination</dt>
                  <dd className="font-audit">{selected.hallucination_type}</dd>
                </div>
                <div>
                  <dt className="text-[var(--papyrus-muted)]">Claim verdict</dt>
                  <dd className="font-audit">{selected.claim_alignment_verdict ?? "—"}</dd>
                </div>
              </dl>
              {selected.quantitative_caveat && (
                <p className="mt-3 rounded border border-amber-700/40 bg-amber-950/30 p-2 text-xs text-amber-100">
                  {selected.quantitative_caveat}
                </p>
              )}
            </div>
          )}
        </section>

        <section className="rounded-xl border border-white/10 bg-[#0c100e] p-4">
          <h3 className="font-audit text-sm uppercase tracking-wide text-[var(--papyrus-muted)]">
            Live resolution panel
          </h3>
          <div className="mt-3 max-h-[70vh] space-y-2 overflow-y-auto font-audit text-xs leading-relaxed">
            {events.map((event, index) => (
              <div key={`${event.ts}-${index}`} className="border-b border-white/5 pb-2">
                <span className="text-[var(--papyrus-muted)]">{event.ts.slice(11, 19)}</span>{" "}
                <span className="text-emerald-300">{event.type}</span> {event.message}
              </div>
            ))}
            {!events.length && (
              <p className="text-[var(--papyrus-muted)]">Resolution events will stream here during analysis.</p>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
