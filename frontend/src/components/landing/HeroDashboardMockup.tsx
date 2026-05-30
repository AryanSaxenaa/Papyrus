import { useEffect, useRef, useState } from "react";
import { motion, useInView, useReducedMotion } from "motion/react";
import { PapyrusLogo } from "./LandingIcons";
import { useHeroTilt } from "./useHeroTilt";

const NAV_ITEMS = [
  { label: "Dashboard", active: true },
  { label: "Past audits", active: false },
  { label: "Live audit", active: false },
  { label: "Integrations", active: false },
  { label: "Settings", active: false },
];

const SEGMENTS = [
  { color: "#22c55e", pct: 39, label: "Supported", count: 64 },
  { color: "#ef4444", pct: 10, label: "Contradicted", count: 16 },
  { color: "#3b82f6", pct: 11, label: "Cannot assess", count: 18 },
  { color: "#f97316", pct: 10, label: "Unresolvable", count: 16 },
  { color: "#b91c1c", pct: 2, label: "Retracted", count: 4 },
  { color: "#d4d4d8", pct: 28, label: "Pending", count: 45 },
];

const STATUS_CARDS = [
  { label: "Supported", value: 64, icon: "check", color: "#166534", bg: "#ecfdf3" },
  { label: "Contradicted", value: 16, icon: "x", color: "#dc2626", bg: "#fef2f2" },
  { label: "Cannot assess", value: 18, icon: "question", color: "#2563eb", bg: "#eff6ff" },
  { label: "Confirmed failure", value: 16, icon: "alert", color: "#c2410c", bg: "#fff7ed" },
  { label: "Retracted", value: 4, icon: "ban", color: "#991b1b", bg: "#fef2f2" },
];

function SidebarIcon({ name }: { name: string }) {
  const s = "currentColor";
  if (name === "Dashboard") {
    return (
      <svg className="h-4 w-4 shrink-0" viewBox="0 0 16 16" fill="none" aria-hidden>
        <rect x="2" y="2" width="5" height="5" rx="1" stroke={s} strokeWidth="1.2" />
        <rect x="9" y="2" width="5" height="5" rx="1" stroke={s} strokeWidth="1.2" />
        <rect x="2" y="9" width="5" height="5" rx="1" stroke={s} strokeWidth="1.2" />
        <rect x="9" y="9" width="5" height="5" rx="1" stroke={s} strokeWidth="1.2" />
      </svg>
    );
  }
  if (name === "Past audits") {
    return (
      <svg className="h-4 w-4 shrink-0" viewBox="0 0 16 16" fill="none" aria-hidden>
        <path d="M3 4h10M3 8h10M3 12h6" stroke={s} strokeWidth="1.2" strokeLinecap="round" />
      </svg>
    );
  }
  if (name === "Live audit") {
    return (
      <svg className="h-4 w-4 shrink-0" viewBox="0 0 16 16" fill="none" aria-hidden>
        <circle cx="8" cy="8" r="5" stroke={s} strokeWidth="1.2" />
        <path d="M8 5v3l2 1" stroke={s} strokeWidth="1.2" strokeLinecap="round" />
      </svg>
    );
  }
  if (name === "Integrations") {
    return (
      <svg className="h-4 w-4 shrink-0" viewBox="0 0 16 16" fill="none" aria-hidden>
        <path
          d="M6 6a2 2 0 1 1 4 0M3 12a2 2 0 1 1 4 0M9 12a2 2 0 1 1 4 0"
          stroke={s}
          strokeWidth="1.2"
        />
      </svg>
    );
  }
  return (
    <svg className="h-4 w-4 shrink-0" viewBox="0 0 16 16" fill="none" aria-hidden>
      <circle cx="8" cy="8" r="2" stroke={s} strokeWidth="1.2" />
      <path d="M8 2v1M8 13v1M2 8h1M13 8h1" stroke={s} strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  );
}

function CardIcon({ type, color }: { type: string; color: string }) {
  const s = color;
  if (type === "check") {
    return (
      <svg className="h-3.5 w-3.5" viewBox="0 0 14 14" fill="none" aria-hidden>
        <path d="M3 7l3 3 5-6" stroke={s} strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }
  if (type === "x") {
    return (
      <svg className="h-3.5 w-3.5" viewBox="0 0 14 14" fill="none" aria-hidden>
        <path d="M4 4l6 6M10 4l-6 6" stroke={s} strokeWidth="1.4" strokeLinecap="round" />
      </svg>
    );
  }
  if (type === "question") {
    return (
      <svg className="h-3.5 w-3.5" viewBox="0 0 14 14" fill="none" aria-hidden>
        <path
          d="M5.5 5a2 2 0 1 1 3.2 1.6c-.8.6-1.2 1-1.2 1.9V9"
          stroke={s}
          strokeWidth="1.2"
          strokeLinecap="round"
        />
        <circle cx="7" cy="11" r="0.6" fill={s} />
      </svg>
    );
  }
  if (type === "alert") {
    return (
      <svg className="h-3.5 w-3.5" viewBox="0 0 14 14" fill="none" aria-hidden>
        <path d="M7 3v5M7 10.5v.5" stroke={s} strokeWidth="1.4" strokeLinecap="round" />
      </svg>
    );
  }
  return (
    <svg className="h-3.5 w-3.5" viewBox="0 0 14 14" fill="none" aria-hidden>
      <circle cx="7" cy="7" r="4.5" stroke={s} strokeWidth="1.2" />
      <path d="M4.5 4.5l5 5" stroke={s} strokeWidth="1.2" />
    </svg>
  );
}

export function HeroDashboardMockup() {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-5% 0px" });
  const reduce = useReducedMotion();
  const [score, setScore] = useState(reduce ? 87 : 0);
  const tilt = useHeroTilt();

  useEffect(() => {
    if (!inView || reduce) {
      if (reduce) setScore(87);
      return;
    }
    const duration = 1400;
    const start = performance.now();
    let frame = 0;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - (1 - t) ** 3;
      setScore(Math.round(87 * eased));
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [inView, reduce]);

  return (
    <div ref={ref} className="relative w-full">

      <motion.div
        ref={tilt.ref}
        onMouseMove={tilt.onMove}
        onMouseLeave={tilt.onLeave}
        style={tilt.style}
        className="hero-dashboard-mockup overflow-hidden rounded-2xl border border-zinc-200/80 bg-white shadow-[0_24px_80px_-20px_rgba(15,23,42,0.18)] will-change-transform"
        initial={{ opacity: 0, y: 32 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1], delay: 0.12 }}
      >
        <div className="flex min-h-[400px] lg:min-h-[440px]">
          <aside className="flex w-[168px] shrink-0 flex-col border-r border-zinc-100 bg-[#f7f7f7] px-3 py-5">
            <div className="mb-5 flex items-center gap-2 px-2">
              <PapyrusLogo className="h-[62px] w-[41px]" />
              <span className="text-sm font-bold text-zinc-900">Papyrus</span>
            </div>
            {NAV_ITEMS.map((item) => (
              <div
                key={item.label}
                className={`mb-1 flex items-center gap-2.5 rounded-lg px-2.5 py-2.5 text-[12px] font-medium ${
                  item.active ? "bg-[#e8f5e9] text-[#1b5e20]" : "text-zinc-500"
                }`}
              >
                <span className={item.active ? "text-[#2d6a4f]" : "text-zinc-400"}>
                  <SidebarIcon name={item.label} />
                </span>
                {item.label}
              </div>
            ))}
            <div className="flex-1" aria-hidden />
          </aside>

          <div className="flex min-w-0 flex-1 flex-col">
            <div className="flex items-center justify-end gap-2 border-b border-zinc-100 px-4 py-3.5">
              <button
                type="button"
                className="flex items-center gap-1 rounded-lg border border-zinc-200 bg-white px-2.5 py-1 text-[11px] font-medium text-zinc-600"
              >
                Export
                <svg className="h-3 w-3 opacity-50" viewBox="0 0 12 12" fill="none" aria-hidden>
                  <path d="M3 5l3 3 3-3" stroke="currentColor" strokeWidth="1.2" />
                </svg>
              </button>
              <div className="relative flex h-8 w-8 items-center justify-center rounded-lg border border-zinc-200 bg-white">
                <svg className="h-4 w-4 text-zinc-500" viewBox="0 0 16 16" fill="none" aria-hidden>
                  <path
                    d="M4 6a4 4 0 0 1 8 0v2l1 2H3l1-2V6z"
                    stroke="currentColor"
                    strokeWidth="1.2"
                  />
                </svg>
                <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-red-500" />
              </div>
              <div className="h-8 w-8 overflow-hidden rounded-full bg-gradient-to-br from-[#b7e4c7] to-[#40916c]" />
            </div>

            <div className="flex flex-1 flex-col p-5 pb-5">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <h3 className="text-[14px] font-semibold leading-snug text-zinc-900">
                    Quantum Coherence in Photosynthetic Complexes
                  </h3>
                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    <span className="inline-flex items-center gap-1 rounded-md bg-[#dcfce7] px-2 py-0.5 text-[10px] font-semibold text-[#15803d]">
                      <span className="h-1.5 w-1.5 rounded-full bg-[#22c55e]" />
                      Completed
                    </span>
                    <span className="text-[10px] text-zinc-400">
                      Pipeline v1.4.2 · 14 Apr 2024
                    </span>
                  </div>
                </div>
                <div className="shrink-0 text-right">
                  <div className="flex items-start justify-end gap-1">
                    <p className="text-[2rem] font-bold leading-none tracking-tight text-[#16a34a]">
                      {score}%
                    </p>
                    <svg
                      className="mt-1 h-3.5 w-3.5 text-zinc-300"
                      viewBox="0 0 14 14"
                      fill="none"
                      aria-hidden
                    >
                      <circle cx="7" cy="7" r="5.5" stroke="currentColor" strokeWidth="1" />
                      <path d="M7 6.2v3.5M7 4.5v.01" stroke="currentColor" strokeWidth="1.2" />
                    </svg>
                  </div>
                  <p className="mt-0.5 text-[10px] text-zinc-500">Overall score</p>
                </div>
              </div>

              <div className="mt-6 flex-1">
                <div className="flex items-baseline justify-between gap-2">
                  <p className="text-[12px] font-semibold text-zinc-800">Audit summary</p>
                  <p className="text-[10px] text-zinc-500">142 of 163 citations resolved</p>
                </div>
                <div className="mt-3 flex h-2.5 overflow-hidden rounded-full bg-zinc-100">
                  {SEGMENTS.map((seg, i) => (
                    <motion.div
                      key={seg.label}
                      className="h-full"
                      style={{ backgroundColor: seg.color }}
                      initial={{ width: 0 }}
                      animate={inView ? { width: `${seg.pct}%` } : { width: 0 }}
                      transition={{
                        duration: 0.75,
                        delay: 0.2 + i * 0.05,
                        ease: [0.22, 1, 0.36, 1],
                      }}
                    />
                  ))}
                </div>
                <div className="mt-3.5 grid grid-cols-2 gap-x-2 gap-y-1.5 sm:grid-cols-3">
                  {SEGMENTS.filter((s) => s.label !== "Pending").map((seg) => (
                    <span
                      key={seg.label}
                      className="flex items-center gap-1.5 text-[9px] text-zinc-500"
                    >
                      <span
                        className="h-1.5 w-1.5 shrink-0 rounded-full"
                        style={{ backgroundColor: seg.color }}
                      />
                      <span>
                        {seg.label}{" "}
                        <span className="font-semibold text-zinc-700">{seg.count}</span>
                        <span className="text-zinc-400"> ({seg.pct}%)</span>
                      </span>
                    </span>
                  ))}
                </div>
              </div>

              <div className="mt-5 grid grid-cols-3 gap-1.5 sm:grid-cols-5">
                {STATUS_CARDS.map((card, i) => (
                  <motion.div
                    key={card.label}
                    initial={{ opacity: 0, y: 6 }}
                    animate={inView ? { opacity: 1, y: 0 } : {}}
                    transition={{ delay: 0.5 + i * 0.04 }}
                    className="rounded-lg border border-zinc-100 bg-white px-1 py-3 text-center shadow-[0_1px_2px_rgba(0,0,0,0.04)]"
                  >
                    <span
                      className="mx-auto mb-1.5 flex h-6 w-6 items-center justify-center rounded-md"
                      style={{ backgroundColor: card.bg }}
                    >
                      <CardIcon type={card.icon} color={card.color} />
                    </span>
                    <p className="text-[7px] leading-tight text-zinc-500">{card.label}</p>
                    <p className="mt-0.5 text-[13px] font-bold text-zinc-900">{card.value}</p>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
