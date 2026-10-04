type Props = {
  open: boolean;
  loading: boolean;
  onAccept: () => void;
  onDecline: () => void;
};

export function ShepherdModePrompt({ open, loading, onAccept, onDecline }: Props) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-900/40 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="shepherd-mode-title"
      data-testid="shepherd-mode-prompt"
    >
      <div className="w-full max-w-md rounded-xl border border-zinc-200 bg-white p-6 shadow-xl">
        <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[#40916c]">
          Optional
        </p>
        <h2 id="shepherd-mode-title" className="mt-1 font-serif-display text-xl font-bold text-zinc-900">
          Shepherd mode
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-zinc-600">
          We&apos;ll preload a <strong className="font-semibold text-zinc-800">real recorded audit</strong>{" "}
          (replay API), then walk you through <strong className="font-semibold text-zinc-800">upload</strong>,{" "}
          <strong className="font-semibold text-zinc-800">SerpApi credits</strong>, the heatmap, and the{" "}
          <strong className="font-semibold text-zinc-800">Scholar witness matrix</strong> — not just the side
          drawer. When you exit, the same audit stays loaded for live PDF/DOI/URL uploads.
        </p>
        <p className="mt-2 text-xs text-zinc-500">
          Nothing starts until you accept. Decline to use the app without the tour.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <button
            type="button"
            disabled={loading}
            onClick={onAccept}
            className="rounded-lg bg-[#1a3d32] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#153028] disabled:opacity-60"
          >
            {loading ? "Loading audit…" : "Start guided tour"}
          </button>
          <button
            type="button"
            disabled={loading}
            onClick={onDecline}
            className="rounded-lg border border-zinc-200 px-4 py-2.5 text-sm font-medium text-zinc-700 hover:bg-zinc-50"
          >
            No thanks
          </button>
        </div>
      </div>
    </div>
  );
}

export function ShepherdTourBanner() {
  return (
    <div
      data-testid="shepherd-tour-banner"
      className="rounded-lg border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-950"
      role="status"
    >
      <p className="font-medium">Shepherd mode — guided tour</p>
      <p className="mt-1 text-xs text-sky-900/90">
        Preloaded audit uses real API replay data. Exit the tour anytime; results stay loaded.
      </p>
    </div>
  );
}
