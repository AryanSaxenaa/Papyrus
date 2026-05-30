import { useState } from "react";
import { AnimatePresence, motion } from "motion/react";

type Props = {
  activeStep: number;
};

const CITATION_MARKS = [
  { label: "[12]", color: "bg-red-100 text-red-700", line: 2 },
  { label: "[7]", color: "bg-blue-100 text-blue-700", line: 4 },
  { label: "[11]", color: "bg-orange-100 text-orange-700", line: 5 },
  { label: "[14]", color: "bg-emerald-100 text-emerald-700", line: 7 },
  { label: "[3]", color: "bg-zinc-200 text-zinc-600", line: 9 },
];

const STEP_PANELS = [
  {
    status: "Extracting",
    statusCls: "bg-zinc-600 text-white",
    confidence: 18,
    showDetails: false,
    body: "Scanning bibliography and inline citation markers across your manuscript.",
    visibleMarks: 2,
    highlightLine: -1,
  },
  {
    status: "Verifying",
    statusCls: "bg-blue-600 text-white",
    confidence: 45,
    showDetails: true,
    body: null,
    visibleMarks: 3,
    highlightLine: 2,
  },
  {
    status: "Supported",
    statusCls: "bg-emerald-600 text-white",
    confidence: 72,
    showDetails: true,
    body: null,
    visibleMarks: 4,
    highlightLine: 2,
  },
  {
    status: "Contradicted",
    statusCls: "bg-red-50 text-red-600 ring-1 ring-red-200",
    confidence: 88,
    showDetails: true,
    body: null,
    visibleMarks: 5,
    highlightLine: 2,
  },
  {
    status: "87% coverage",
    statusCls: "bg-[#0a3d2e] text-white",
    confidence: 87,
    showDetails: false,
    body: "export",
    visibleMarks: 5,
    highlightLine: -1,
  },
];

export function PaperAnatomyMockup({ activeStep }: Props) {
  const [view, setView] = useState<"text" | "pdf">("text");
  const step = Math.min(Math.max(activeStep, 0), STEP_PANELS.length - 1);
  const panel = STEP_PANELS[step] ?? STEP_PANELS[0];
  const marks = CITATION_MARKS.slice(0, panel.visibleMarks);

  return (
    <div className="overflow-hidden rounded-2xl border border-zinc-200/90 bg-white shadow-[0_20px_50px_-16px_rgba(15,23,42,0.12)]">
      <div className="flex items-center justify-between gap-4 border-b border-zinc-100 px-5 py-4">
        <p className="text-sm font-semibold text-zinc-900">Paper anatomy</p>
        <div
          className="flex rounded-lg bg-zinc-100 p-1"
          role="tablist"
          aria-label="Document view"
        >
          <button
            type="button"
            role="tab"
            aria-selected={view === "text"}
            onClick={() => setView("text")}
            className={`rounded-md px-3 py-1 text-xs font-semibold transition-colors ${
              view === "text"
                ? "bg-[#ecfdf3] text-[#1b4332] shadow-sm"
                : "text-zinc-500 hover:text-zinc-700"
            }`}
          >
            Text view
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={view === "pdf"}
            onClick={() => setView("pdf")}
            className={`rounded-md px-3 py-1 text-xs font-semibold transition-colors ${
              view === "pdf"
                ? "bg-[#ecfdf3] text-[#1b4332] shadow-sm"
                : "text-zinc-500 hover:text-zinc-700"
            }`}
          >
            PDF view
          </button>
        </div>
      </div>

      <div className="grid lg:grid-cols-[1.15fr_0.85fr]">
        <div className="relative min-h-[200px] border-b border-zinc-100 p-5 lg:min-h-[220px] lg:border-b-0 lg:border-r">
          <div className="space-y-2.5">
            {Array.from({ length: 10 }).map((_, i) => (
              <div
                key={i}
                className={`relative h-2 rounded-full bg-zinc-100 transition-colors duration-300 ${
                  i === panel.highlightLine
                    ? "bg-emerald-100/80 ring-1 ring-emerald-200/60"
                    : ""
                }`}
                style={{ width: `${68 + ((i * 17) % 28)}%` }}
              />
            ))}
          </div>
          <AnimatePresence mode="popLayout">
            {marks.map((mark) => (
              <motion.span
                key={mark.label}
                layout
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className={`absolute rounded px-1 py-0.5 text-[9px] font-bold ${mark.color}`}
                style={{
                  top: `${12 + mark.line * 9}%`,
                  left: `${20 + (mark.line % 3) * 22}%`,
                }}
              >
                {mark.label}
              </motion.span>
            ))}
          </AnimatePresence>
        </div>

        <div className="min-h-[200px] bg-[#fafafa] p-5 lg:min-h-[220px]">
          <AnimatePresence mode="wait">
            <motion.div
              key={step}
              initial={{ opacity: 0, x: 12 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.3 }}
            >
              {panel.body === "export" ? (
                <div>
                  <p className="text-xs font-semibold text-zinc-900">Audit report ready</p>
                  <p className="mt-1 text-sm text-zinc-500">
                    Coverage, risk level, and per-citation detail in one shareable export.
                  </p>
                  <div className="mt-4 space-y-2">
                    {["TXT", "JSON", "PDF"].map((fmt) => (
                      <div
                        key={fmt}
                        className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-xs font-medium text-zinc-700"
                      >
                        Export {fmt}
                      </div>
                    ))}
                  </div>
                </div>
              ) : !panel.showDetails ? (
                <div>
                  <p className="text-xs font-semibold text-zinc-900">#12 Lee, M. (2012)</p>
                  <p className="mt-0.5 font-mono text-[10px] text-zinc-400">
                    DOI: 10.1126/science.1227604
                  </p>
                  <span
                    className={`mt-3 inline-block rounded-md px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide ${panel.statusCls}`}
                  >
                    {panel.status}
                  </span>
                  <p className="mt-4 text-sm leading-relaxed text-zinc-500">{panel.body}</p>
                </div>
              ) : (
                <>
                  <p className="text-xs font-semibold text-zinc-900">#12 Lee, M. (2012)</p>
                  <p className="mt-0.5 font-mono text-[10px] text-zinc-400">
                    DOI: 10.1126/science.1227604
                  </p>
                  <span
                    className={`mt-3 inline-block rounded-md px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide ${panel.statusCls}`}
                  >
                    {panel.status}
                  </span>

                  <div
                    className="mt-4 flex gap-4 border-b border-zinc-200"
                    role="tablist"
                    aria-label="Citation panel"
                  >
                    <button
                      type="button"
                      role="tab"
                      aria-selected
                      className="border-b-2 border-[#2d6a4f] pb-2 text-xs font-semibold text-[#1b4332]"
                    >
                      Details
                    </button>
                    <button
                      type="button"
                      role="tab"
                      aria-selected={false}
                      className="pb-2 text-xs font-medium text-zinc-400"
                      disabled
                    >
                      Evidence
                    </button>
                  </div>

                  <dl className="mt-4 space-y-2.5 text-xs">
                    {[
                      ["Journal", "Science"],
                      ["Published", "2012"],
                      ["DOI Status", "Active"],
                      ["Match", "Exact"],
                      ["Confidence", "High"],
                    ].map(([term, value]) => (
                      <div key={term} className="flex justify-between gap-4">
                        <dt className="text-zinc-400">{term}</dt>
                        <dd className="font-medium text-zinc-800">
                          {term === "DOI Status" ? (
                            <span className="rounded-md bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700 ring-1 ring-emerald-200">
                              {value}
                            </span>
                          ) : (
                            value
                          )}
                        </dd>
                      </div>
                    ))}
                  </dl>

                  <p className="mt-3 text-[10px] text-zinc-500">Confidence</p>
                  <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-zinc-200">
                    <motion.div
                      className="h-full rounded-full bg-[#2d6a4f]"
                      initial={{ width: 0 }}
                      animate={{ width: `${panel.confidence}%` }}
                      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
                    />
                  </div>

                  {step === 3 && (
                    <button
                      type="button"
                      disabled
                      className="mt-5 w-full cursor-default rounded-lg border border-zinc-300 bg-white px-4 py-2.5 text-xs font-semibold text-zinc-800 opacity-90"
                    >
                      View full details →
                    </button>
                  )}
                </>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
