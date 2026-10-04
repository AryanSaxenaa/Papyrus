import { Fragment, useCallback, useEffect, useMemo, useState } from "react";
import { CoverageBar } from "./components/CoverageBar";
import { CoverageSummary } from "./components/CoverageSummary";
import { HeatmapLegend } from "./components/HeatmapLegend";
import { LivePanel } from "./components/LivePanel";
import { LimitationsPanel } from "./components/LimitationsPanel";
import { CitationHeatmap } from "./components/CitationHeatmap";
import { PaperAnatomyView } from "./components/PaperAnatomyView";
import { canShowPaperAnatomy } from "./lib/anatomyMarkers";
import { SiteFooter } from "./components/SiteFooter";
import { LandingNav } from "./components/landing/LandingNav";
import { AppFeaturesCard } from "./components/app/AppFeaturesCard";
import { AppHeroIllustration } from "./components/app/AppHeroIllustration";
import { AppUploadCard } from "./components/app/AppUploadCard";
import { AdminPanel } from "./components/AdminPanel";
import { PastAudits } from "./components/PastAudits";
import { SideBySideDrawer } from "./components/SideBySideDrawer";
import { CreditsMeter } from "./components/CreditsMeter";
import { ReplayBanner } from "./components/ReplayBanner";
import { ShepherdModePrompt, ShepherdTourBanner } from "./components/ShepherdModePrompt";
import { MathGridBg } from "./components/app/MathGridBg";
import { useShepherdTour } from "./hooks/useShepherdTour";
import { apiUrl } from "./lib/api";
import {
  markShepherdDeclined,
  shouldOfferShepherdMode,
} from "./lib/shepherdStorage";
import { connectAuditEventSource } from "./lib/sse";
import type {
  AppPublicConfig,
  AuditRun,
  BulkDashboard,
  CitationRecord,
  HeatmapFilter,
  StreamEvent,
} from "./types";

export default function App() {
  const [audit, setAudit] = useState<AuditRun | null>(null);
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [selected, setSelected] = useState<CitationRecord | null>(null);
  const [uploading, setUploading] = useState(false);
  const [activityOpen, setActivityOpen] = useState(false);
  const [bulkStatus, setBulkStatus] = useState<string | null>(null);
  const [bulkJobId, setBulkJobId] = useState<string | null>(null);
  const [bulkEvents, setBulkEvents] = useState<StreamEvent[]>([]);
  const [bulkDashboard, setBulkDashboard] = useState<BulkDashboard | null>(null);
  const [showAnatomy, setShowAnatomy] = useState(false);
  const [filter, setFilter] = useState<HeatmapFilter>("all");
  const [claimDraft, setClaimDraft] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [expandedBulkId, setExpandedBulkId] = useState<string | null>(null);
  const [bulkAuditCache, setBulkAuditCache] = useState<Record<string, AuditRun>>({});
  const [auditsListKey, setAuditsListKey] = useState(0);
  const [appConfig, setAppConfig] = useState<AppPublicConfig | null>(null);
  const [serpapiBudget, setSerpapiBudget] = useState<{
    monthly_spent: number;
    monthly_cap: number;
    per_audit_cap: number;
    enabled: boolean;
  } | null>(null);
  const [shepherdPromptOpen, setShepherdPromptOpen] = useState(false);
  const [shepherdLoading, setShepherdLoading] = useState(false);
  const [shepherdTouring, setShepherdTouring] = useState(false);

  const { startTour, cancelTour } = useShepherdTour({
    onFinish: () => setShepherdTouring(false),
  });

  useEffect(() => {
    void (async () => {
      try {
        const res = await fetch(apiUrl("/api/config"));
        if (res.ok) setAppConfig((await res.json()) as AppPublicConfig);
        const budgetRes = await fetch(apiUrl("/api/serpapi/budget"));
        if (budgetRes.ok) {
          const body = (await budgetRes.json()) as {
            monthly_spent: number;
            monthly_cap: number;
            per_audit_cap: number;
            enabled: boolean;
          };
          setSerpapiBudget(body);
        }
      } catch {
        /* offline dev */
      }
    })();
  }, []);

  useEffect(() => {
    if (appConfig && !audit && shouldOfferShepherdMode()) {
      setShepherdPromptOpen(true);
    }
  }, [appConfig, audit]);

  const refreshAudit = useCallback(async (id: string) => {
    const response = await fetch(apiUrl(`/api/audits/${id}`));
    if (!response.ok) return;
    const next = (await response.json()) as AuditRun;
    setAudit(next);
    setSelected((current) => {
      if (!current) return null;
      return next.citations.find((c) => c.id === current.id) ?? current;
    });
  }, []);

  useEffect(() => {
    if (!audit?.id) return;
    if (audit.status === "complete" || audit.status === "failed") {
      void refreshAudit(audit.id);
      return;
    }
    const timer = window.setInterval(() => refreshAudit(audit.id), 2500);
    return () => window.clearInterval(timer);
  }, [audit?.id, audit?.status, refreshAudit]);

  useEffect(() => {
    if (!audit?.id) return;
    const pollEvents = async () => {
      try {
        const res = await fetch(apiUrl(`/api/audits/${audit.id}/events/history`));
        if (res.ok) {
          setEvents((await res.json()) as StreamEvent[]);
        }
      } catch {
        /* ignore */
      }
    };
    void pollEvents();
    if (audit.status === "complete" || audit.status === "failed") {
      return;
    }
    const timer = window.setInterval(pollEvents, 2000);
    return () => window.clearInterval(timer);
  }, [audit?.id, audit?.status]);

  useEffect(() => {
    if (audit && audit.status !== "complete" && audit.status !== "failed") {
      setActivityOpen(true);
    }
  }, [audit?.id, audit?.status]);

  useEffect(() => {
    if (!bulkJobId) return;
    const source = connectAuditEventSource(apiUrl(`/api/bulk/${bulkJobId}/events`), (payload) => {
      setBulkEvents((prev) => [...prev.slice(-80), payload]);
    });
    source.onerror = () => source.close();
    return () => source.close();
  }, [bulkJobId]);

  useEffect(() => {
    if (!audit?.id) return;
    const source = connectAuditEventSource(apiUrl(`/api/audits/${audit.id}/events`), (payload) => {
      setEvents((prev) => [...prev, payload]);
    });
    source.onerror = () => source.close();
    return () => source.close();
  }, [audit?.id]);

  useEffect(() => {
    if (!selected) return;
    setClaimDraft(selected.claim_user_corrected ?? selected.extracted_claim ?? "");
  }, [selected]);

  useEffect(() => {
    if (!selected?.id) return;
    document.getElementById(`heatmap-citation-${selected.id}`)?.scrollIntoView({
      behavior: "smooth",
      block: "nearest",
    });
  }, [selected?.id]);

  const startAudit = async (response: Response) => {
    if (!response.ok) throw new Error(await response.text());
    const created = (await response.json()) as AuditRun;
    setAudit(created);
    setAuditsListKey((key) => key + 1);
  };

  const onUpload = async (file: File) => {
    setUploading(true);
    setError(null);
    setEvents([]);
    setSelected(null);
    try {
      const body = new FormData();
      body.append("file", file);
      await startAudit(await fetch(apiUrl("/api/audits"), { method: "POST", body }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const waitForAuditTerminal = async (id: string, maxMs = 90_000): Promise<AuditRun | null> => {
    const deadline = Date.now() + maxMs;
    while (Date.now() < deadline) {
      const response = await fetch(apiUrl(`/api/audits/${id}`));
      if (response.ok) {
        const body = (await response.json()) as AuditRun;
        setAudit(body);
        if (body.status === "complete" || body.status === "failed") {
          return body;
        }
      }
      await new Promise((resolve) => window.setTimeout(resolve, 600));
    }
    return null;
  };

  const onReplayRecorded = async () => {
    const replaySet = appConfig?.replay_set ?? "demo-a";
    setUploading(true);
    setError(null);
    setEvents([]);
    setSelected(null);
    try {
      await startAudit(
        await fetch(apiUrl(`/api/audits/replay/${replaySet}`), { method: "POST" }),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Replay failed");
    } finally {
      setUploading(false);
    }
  };

  const loadReplayAudit = async (): Promise<AuditRun | null> => {
    const replaySet = appConfig?.replay_set ?? "demo-a";
    setError(null);
    setEvents([]);
    setSelected(null);
    const response = await fetch(apiUrl(`/api/audits/replay/${replaySet}`), { method: "POST" });
    if (!response.ok) throw new Error(await response.text());
    const created = (await response.json()) as AuditRun;
    setAudit(created);
    setAuditsListKey((key) => key + 1);
    return waitForAuditTerminal(created.id);
  };

  const onAcceptShepherdMode = async () => {
    setShepherdLoading(true);
    setError(null);
    try {
      const finished = await loadReplayAudit();
      if (!finished || finished.status !== "complete" || finished.citations.length === 0) {
        throw new Error("Could not load the guided tour audit.");
      }
      const first = finished.citations[0];
      setSelected(first);
      setShepherdPromptOpen(false);
      setShepherdTouring(true);
      window.requestAnimationFrame(() => {
        startTour(() => setSelected(first));
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Shepherd mode failed");
      setShepherdPromptOpen(false);
      setShepherdTouring(false);
    } finally {
      setShepherdLoading(false);
    }
  };

  const onDeclineShepherdMode = () => {
    markShepherdDeclined();
    setShepherdPromptOpen(false);
    cancelTour();
    setShepherdTouring(false);
  };

  const openShepherdPrompt = () => {
    if (!uploading && !shepherdLoading) {
      setShepherdPromptOpen(true);
    }
  };

  const onStartReference = async (kind: "doi" | "url", value: string) => {
    setUploading(true);
    setError(null);
    setEvents([]);
    setSelected(null);
    try {
      const endpoint = kind === "url" ? apiUrl("/api/audits/url") : apiUrl("/api/audits/doi");
      const body = kind === "url" ? { url: value } : { doi: value };
      await startAudit(
        await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start audit");
    } finally {
      setUploading(false);
    }
  };

  const onBulkUpload = async (file: File) => {
    setUploading(true);
    setError(null);
    setBulkStatus(null);
    try {
      const body = new FormData();
      body.append("file", file);
      const response = await fetch(apiUrl("/api/audits/bulk"), { method: "POST", body });
      if (!response.ok) throw new Error(await response.text());
      const job = (await response.json()) as { id: string; total: number };
      setBulkJobId(job.id);
      setBulkEvents([]);
      setBulkDashboard(null);
      setBulkStatus(`Bulk job ${job.id} queued (${job.total} papers)`);
      const poll = window.setInterval(async () => {
        const statusRes = await fetch(apiUrl(`/api/bulk/${job.id}`));
        if (!statusRes.ok) return;
        const status = (await statusRes.json()) as {
          status: string;
          completed: number;
          failed: number;
          total: number;
          estimated_seconds_remaining?: number | null;
        };
        const eta =
          status.estimated_seconds_remaining != null
            ? ` · ~${Math.ceil(status.estimated_seconds_remaining / 60)} min left`
            : "";
        setBulkStatus(
          `Bulk: ${status.completed}/${status.total} complete, ${status.failed} failed (${status.status})${eta}`,
        );
        if (status.status === "complete" || status.status === "failed") {
          window.clearInterval(poll);
          setUploading(false);
          await hydrateBulkEvents(job.id);
          const dashRes = await fetch(apiUrl(`/api/bulk/${job.id}/dashboard`));
          if (dashRes.ok) setBulkDashboard((await dashRes.json()) as BulkDashboard);
        }
      }, 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bulk upload failed");
      setUploading(false);
    }
  };

  const saveIntent = async (intent: string) => {
    if (!audit || !selected) return;
    const response = await fetch(apiUrl(`/api/audits/${audit.id}/citations/${selected.id}/intent`), {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ intent }),
    });
    if (response.ok) await refreshAudit(audit.id);
  };

  const saveClaim = async () => {
    if (!audit || !selected || !claimDraft.trim()) return;
    const response = await fetch(apiUrl(`/api/audits/${audit.id}/citations/${selected.id}/claim`), {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ claim: claimDraft.trim() }),
    });
    if (response.ok) await refreshAudit(audit.id);
  };

  const approveClaim = async () => {
    if (!audit || !selected) return;
    const response = await fetch(
      apiUrl(`/api/audits/${audit.id}/citations/${selected.id}/approve-claim`),
      { method: "POST" },
    );
    if (response.ok) await refreshAudit(audit.id);
  };

  const rerunNli = async () => {
    if (!audit || !selected) return;
    const response = await fetch(
      apiUrl(`/api/audits/${audit.id}/citations/${selected.id}/rerun-nli`),
      { method: "POST" },
    );
    if (response.ok) await refreshAudit(audit.id);
  };

  const rerunCitation = async () => {
    if (!audit || !selected) return;
    const response = await fetch(apiUrl(`/api/audits/${audit.id}/citations/${selected.id}/rerun`), {
      method: "POST",
    });
    if (response.ok) await refreshAudit(audit.id);
  };

  const filteredCitations = useMemo(() => {
    const citations = audit?.citations ?? [];
    if (filter === "all") return citations;
    if (filter === "supported") {
      return citations.filter(
        (c) => c.claim_alignment_verdict === "supported" || c.verdict_color === "supported",
      );
    }
    if (filter === "contradictions") {
      return citations.filter(
        (c) =>
          c.hallucination_type === "type_7_claim_contradiction" ||
          c.claim_alignment_verdict === "claim_contradiction",
      );
    }
    if (filter === "cannot_assess") {
      return citations.filter(
        (c) => c.claim_alignment_verdict === "cannot_determine" || c.verdict_color === "cannot_assess",
      );
    }
    if (filter === "failures") {
      return citations.filter((c) => {
        if (c.verdict_color === "unresolvable" || c.evidence_tier === "tier_4") {
          return false;
        }
        return (
          c.verdict_color === "failure" ||
          (c.hallucination_type.startsWith("type_") && c.hallucination_type !== "retraction") ||
          c.claim_alignment_verdict === "claim_contradiction" ||
          c.claim_alignment_verdict === "not_addressed"
        );
      });
    }
    if (filter === "unresolvable") return citations.filter((c) => c.verdict_color === "unresolvable");
    return citations.filter(
      (c) => c.hallucination_type === "retraction" || c.verdict_color === "retraction",
    );
  }, [audit?.citations, filter]);

  const loadAuditById = async (auditId: string) => {
    const response = await fetch(apiUrl(`/api/audits/${auditId}`));
    if (!response.ok) return;
    setAudit((await response.json()) as AuditRun);
    setSelected(null);
    setAuditsListKey((key) => key + 1);
    try {
      const historyRes = await fetch(apiUrl(`/api/audits/${auditId}/events/history`));
      if (historyRes.ok) {
        setEvents((await historyRes.json()) as StreamEvent[]);
      } else {
        setEvents([]);
      }
    } catch {
      setEvents([]);
    }
  };

  const onAuditDeleted = (auditId: string) => {
    if (audit?.id === auditId) {
      setAudit(null);
      setEvents([]);
      setSelected(null);
    }
    setBulkAuditCache((prev) => {
      if (!(auditId in prev)) return prev;
      const next = { ...prev };
      delete next[auditId];
      return next;
    });
    setAuditsListKey((key) => key + 1);
  };

  const hydrateBulkEvents = async (jobId: string) => {
    try {
      const res = await fetch(apiUrl(`/api/bulk/${jobId}/events/history`));
      if (res.ok) {
        setBulkEvents((await res.json()) as StreamEvent[]);
      }
    } catch {
      /* ignore */
    }
  };

  const openBulkPaper = async (auditId: string) => {
    if (bulkJobId) {
      void hydrateBulkEvents(bulkJobId);
    }
    if (bulkAuditCache[auditId]) {
      setAudit(bulkAuditCache[auditId]);
      setExpandedBulkId(auditId);
      try {
        const historyRes = await fetch(apiUrl(`/api/audits/${auditId}/events/history`));
        if (historyRes.ok) {
          setEvents((await historyRes.json()) as StreamEvent[]);
        }
      } catch {
        setEvents([]);
      }
      return;
    }
    const response = await fetch(apiUrl(`/api/audits/${auditId}`));
    if (!response.ok) return;
    const data = (await response.json()) as AuditRun;
    setBulkAuditCache((prev) => ({ ...prev, [auditId]: data }));
    setAudit(data);
    setExpandedBulkId(auditId);
    setShowAnatomy(true);
    try {
      const historyRes = await fetch(apiUrl(`/api/audits/${auditId}/events/history`));
      if (historyRes.ok) {
        setEvents((await historyRes.json()) as StreamEvent[]);
      }
    } catch {
      setEvents([]);
    }
  };

  return (
    <div className="landing-page papyrus-app min-h-screen overflow-x-hidden bg-[#fafafa]">
      <MathGridBg />
      <div className="relative z-[1]">
      <LandingNav />

      <div className="mx-auto max-w-[1120px] px-5 lg:px-8">
        <section id="audit-start" className="scroll-mt-[var(--lp-nav-h)] pb-6 lg:pb-8">
          <div className="grid lg:grid-cols-2 lg:gap-10 mb-0">
            <div className="min-w-0 mt-[70px]">
              <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#40916c]">
                Citation integrity
              </p>
              <h1 className="font-serif-display mt-2 max-w-md text-[clamp(1.75rem,3.8vw,2.35rem)] font-bold leading-[1.14] tracking-[-0.02em] text-zinc-900">
                Audit <em className="italic text-[#1b4332]">every</em> citation.
                <br />
                Trust <em className="italic text-[#1b4332]">every</em> claim.
              </h1>
              <p className="mt-3 max-w-md text-[14px] leading-relaxed text-zinc-500">
                Run a full integrity pass on your manuscript—resolution trails, heatmaps, and
                exportable reports in one place.
              </p>
            </div>
            <AppHeroIllustration />
          </div>

          <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-2 lg:gap-8">
            <AppUploadCard
              uploading={uploading}
              onUploadPdf={(file) => void onUpload(file)}
              onStartReference={(kind, value) => void onStartReference(kind, value)}
              onBulkZip={(file) => void onBulkUpload(file)}
              onStartShepherd={openShepherdPrompt}
              onReplayRecorded={() => void onReplayRecorded()}
              moreOptions={
                <PastAudits
                  embedded
                  refreshKey={auditsListKey}
                  activeAuditId={audit?.id ?? null}
                  onSelect={(id) => void loadAuditById(id)}
                  onDeleted={onAuditDeleted}
                />
              }
            />
            <AppFeaturesCard />
          </div>
        </section>

        <ShepherdModePrompt
          open={shepherdPromptOpen}
          loading={shepherdLoading}
          onAccept={() => void onAcceptShepherdMode()}
          onDecline={onDeclineShepherdMode}
        />

        <main className="space-y-6 pb-8">
          {shepherdTouring && <ShepherdTourBanner />}
          {appConfig?.mode === "replay" && (
            <ReplayBanner replaySet={appConfig.replay_set} />
          )}
          {serpapiBudget && (
            <CreditsMeter
              mode={appConfig?.mode ?? "live"}
              enabled={serpapiBudget.enabled}
              monthlySpent={serpapiBudget.monthly_spent}
              monthlyCap={serpapiBudget.monthly_cap}
              perAuditCap={serpapiBudget.per_audit_cap}
            />
          )}

          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {bulkStatus && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
              <p className="font-medium">{bulkStatus}</p>
              {bulkEvents.length > 0 && (
                <ul className="mt-2 max-h-24 overflow-y-auto papyrus-scroll-hidden font-audit text-[10px] leading-relaxed text-amber-700/80">
                  {bulkEvents.slice(-12).map((event, index) => (
                    <li key={`${event.ts}-${index}`}>
                      {event.ts.slice(11, 19)} {event.type}: {event.message}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {bulkDashboard && (
            <div className="papyrus-card">
              <h3 className="font-semibold text-zinc-900">Bulk analysis dashboard</h3>
              <p className="mt-1 text-xs text-zinc-500">{bulkDashboard.note}</p>
              <div className="mt-2 flex flex-wrap gap-3 text-xs">
                <a
                  className="papyrus-link"
                  href={apiUrl(`/api/bulk/${bulkDashboard.job.id}/dashboard.json`)}
                >
                  Export dashboard JSON
                </a>
                <a
                  className="papyrus-link"
                  href={apiUrl(`/api/bulk/${bulkDashboard.job.id}/events/log.txt`)}
                >
                  Bulk event log
                </a>
              </div>
              {(bulkDashboard.pending_papers ?? 0) > 0 && (
                <p className="mt-2 font-audit text-xs text-amber-700">
                  {bulkDashboard.pending_papers} paper(s) still resolving...
                  {bulkDashboard.job.estimated_seconds_remaining != null && (
                    <span className="text-zinc-500">
                      {" "}
                      · ~{Math.ceil(bulkDashboard.job.estimated_seconds_remaining / 60)} min remaining
                    </span>
                  )}
                </p>
              )}
              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-zinc-200 text-xs font-medium text-zinc-500">
                      <th className="pb-2 pr-3">Paper</th>
                      <th className="pb-2 pr-3">First author</th>
                      <th className="pb-2 pr-3">Coverage</th>
                      <th className="pb-2 pr-3">Failure rate</th>
                      <th className="pb-2 pr-3">T1 / T7 / Ret</th>
                      <th className="pb-2">Risk</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bulkDashboard.papers.map((paper) => {
                      const cached = bulkAuditCache[paper.audit_id];
                      const isExpanded = expandedBulkId === paper.audit_id;
                      return (
                        <Fragment key={paper.audit_id}>
                          <tr
                            className="cursor-pointer border-t border-zinc-100 hover:bg-zinc-50 transition-colors"
                            onClick={() => void openBulkPaper(paper.audit_id)}
                          >
                            <td className="py-2.5 pr-3 text-zinc-800">
                              {paper.title ?? paper.audit_id.slice(0, 8)}
                              {isExpanded && (
                                <span className="ml-2 font-audit text-[10px] text-[#2d6a4f]">
                                  expanded
                                </span>
                              )}
                            </td>
                            <td className="py-2.5 pr-3 text-zinc-500">
                              {paper.first_author ?? "-"}
                            </td>
                            <td className="py-2.5 pr-3 font-audit text-zinc-800">
                              {paper.coverage_percent}%
                            </td>
                            <td className="py-2.5 pr-3 font-audit text-zinc-800">
                              {paper.confirmed_failure_rate}%
                            </td>
                            <td className="py-2.5 pr-3 font-audit text-xs text-zinc-500">
                              {paper.type_1 ?? 0} / {paper.type_7 ?? 0} / {paper.retraction ?? 0}
                            </td>
                            <td className="py-2.5 font-audit text-xs font-semibold uppercase text-zinc-700">
                              {paper.risk_level}
                            </td>
                          </tr>
                          {isExpanded && cached && (
                            <tr
                              key={`${paper.audit_id}-heat`}
                              className="border-t border-zinc-100 bg-zinc-50"
                            >
                              <td colSpan={6} className="space-y-4 py-3">
                                <CitationHeatmap
                                  citations={cached.citations}
                                  selectedId={selected?.id}
                                  onSelect={(citation) => {
                                    setSelected(citation);
                                  }}
                                />
                                <div className="rounded-lg border border-zinc-200 bg-white p-3">
                                  <p className="mb-2 text-xs font-semibold text-zinc-600">
                                    Resolution log
                                  </p>
                                  <LivePanel
                                    events={events}
                                    audit={cached}
                                    auditId={cached.id}
                                    citations={cached.citations}
                                    onSelect={setSelected}
                                  />
                                </div>
                              </td>
                            </tr>
                          )}
                        </Fragment>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              {bulkDashboard && bulkJobId && (
                <div className="mt-4 rounded-lg border border-zinc-200 bg-white p-3">
                  <p className="mb-2 text-xs font-semibold text-zinc-600">Bulk resolution log</p>
                  <LivePanel events={bulkEvents} audit={null} auditId={undefined} />
                </div>
              )}
            </div>
          )}

          {audit && (
            <div className="papyrus-card" data-testid="current-audit-card">
              <p className="papyrus-eyebrow">Current audit</p>
              <div className="mt-2 flex flex-wrap items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <h2 className="font-serif-display text-xl font-bold leading-snug text-[#0a3d2e] sm:text-2xl">
                    {audit.paper_title ?? "Analyzing document..."}
                  </h2>
                  <p className="mt-1 font-audit text-xs text-zinc-400">
                    Status: {audit.status} · Pipeline {audit.pipeline_version}
                  </p>
                  <p className="mt-2 text-xs leading-relaxed text-zinc-500">
                    Citation integrity audit only — Papyrus does not detect AI authorship or
                    writing style.
                  </p>
                  {audit.status === "failed" && audit.error && (
                    <p className="mt-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
                      {audit.error}
                    </p>
                  )}
                </div>
                <div className="shrink-0 text-right">
                  <p className="font-audit text-3xl font-semibold text-[#0a3d2e]">
                    {audit.coverage.coverage_percent}%
                  </p>
                  <p className="text-xs text-zinc-500">
                    Coverage ({audit.coverage.tier_1 + audit.coverage.tier_2} of{" "}
                    {audit.coverage.total} at Tier 2+)
                  </p>
                  <p className="mt-1.5 font-audit text-sm font-semibold uppercase text-amber-700">
                    {audit.risk_level} risk
                    {audit.risk_confidence && (
                      <span className="ml-1 text-xs font-normal text-zinc-500">
                        ({audit.risk_confidence} confidence)
                      </span>
                    )}
                  </p>
                </div>
              </div>
              <div className="mt-4">
                <CoverageBar audit={audit} />
              </div>
              <CoverageSummary audit={audit} filter={filter} onFilter={setFilter} />
              <LimitationsPanel audit={audit} />
              <div className="mt-6 border-t border-zinc-100 pt-5" data-testid="citation-heatmap-section">
                <p className="papyrus-section-title">Citation heatmap</p>
                <div className="mt-2">
                  <HeatmapLegend />
                </div>
                <div className="mt-3">
                  {filteredCitations.length > 0 ? (
                    <CitationHeatmap
                      citations={filteredCitations}
                      selectedId={selected?.id}
                      onSelect={setSelected}
                    />
                  ) : (
                    <p className="text-sm text-zinc-500">No citations match this filter.</p>
                  )}
                </div>
              </div>
              {canShowPaperAnatomy(audit.status) && (
                <div className="mt-4 border-t border-zinc-100 pt-4">
                  <button
                    type="button"
                    className="flex items-center gap-1.5 text-sm font-semibold text-zinc-700 hover:text-[#2d6a4f] transition-colors"
                    onClick={() => setShowAnatomy((value) => !value)}
                  >
                    <span className="font-audit text-xs">{showAnatomy ? "▾" : "▸"}</span>
                    Paper anatomy
                  </button>
                  {showAnatomy && (
                    <div className="mt-3">
                      <PaperAnatomyView
                        auditId={audit.id}
                        text={audit.paper_text ?? ""}
                        citations={audit.citations}
                        onSelectCitation={setSelected}
                      />
                    </div>
                  )}
                </div>
              )}
              {audit.status === "complete" && (
                <details className="mt-4 border-t border-zinc-100 pt-4 text-sm">
                  <summary className="cursor-pointer font-medium text-zinc-700 hover:text-[#2d6a4f]">
                    Export reports
                  </summary>
                  <div className="mt-2 flex flex-wrap gap-3">
                    <a className="papyrus-link" href={apiUrl(`/api/audits/${audit.id}/report.pdf`)}>
                      PDF
                    </a>
                    <a className="papyrus-link" href={apiUrl(`/api/audits/${audit.id}/report.txt`)}>
                      Text
                    </a>
                    <a className="papyrus-link" href={apiUrl(`/api/audits/${audit.id}/report.json`)}>
                      JSON
                    </a>
                    <a className="papyrus-link" href={apiUrl(`/api/audits/${audit.id}/events/log.txt`)}>
                      Event log
                    </a>
                  </div>
                </details>
              )}
            </div>
          )}

          {audit && (
            <div className="papyrus-card !p-4">
              <button
                type="button"
                className="flex w-full items-center justify-between gap-2 text-sm font-semibold text-zinc-700 hover:text-zinc-900 transition-colors"
                onClick={() => setActivityOpen((open) => !open)}
              >
                <span>Activity log</span>
                <span className="font-audit text-xs text-zinc-400">
                  {activityOpen ? "▾" : "▸"} · {events.length} events
                </span>
              </button>
              {activityOpen && (
                <div className="mt-3">
                  <LivePanel
                    events={events}
                    audit={audit}
                    auditId={audit.id}
                    citations={audit.citations}
                    onSelect={setSelected}
                  />
                </div>
              )}
            </div>
          )}

          {selected && audit && (
            <SideBySideDrawer
              audit={audit}
              citation={selected}
              claimDraft={claimDraft}
              onClaimDraft={setClaimDraft}
              onSaveIntent={(intent) => void saveIntent(intent)}
              onSaveClaim={() => void saveClaim()}
              onApproveClaim={() => void approveClaim()}
              onRerunNli={() => void rerunNli()}
              onRerunCitation={() => void rerunCitation()}
              onClose={() => setSelected(null)}
            />
          )}
        </main>

        <div className="mt-8">
          <AdminPanel variant="app" />
        </div>
      </div>

      <div className="mt-12">
        <SiteFooter />
      </div>
      </div>
    </div>
  );
}
