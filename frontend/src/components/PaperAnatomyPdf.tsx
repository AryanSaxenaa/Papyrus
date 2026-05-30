import { useEffect, useMemo, useRef, useState } from "react";
import * as pdfjsLib from "pdfjs-dist";
import type { CitationRecord } from "../types";
import { collectAnatomyMarkers, findMarkerInString } from "../lib/anatomyMarkers";
import { citationFill, isRetraction } from "../lib/verdictColors";

pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

type Props = {
  auditId: string;
  citations: CitationRecord[];
  onSelectCitation: (citation: CitationRecord) => void;
  onUnavailable?: () => void;
};

function applyCitationStyles(button: HTMLButtonElement, citation: CitationRecord) {
  button.style.backgroundColor = citationFill(citation);
  if (isRetraction(citation)) {
    button.classList.add("ring-1", "ring-amber-400");
  } else {
    button.classList.remove("ring-1", "ring-amber-400");
  }
}

export function PaperAnatomyPdf({ auditId, citations, onSelectCitation, onUnavailable }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const overlayButtonsRef = useRef<HTMLButtonElement[]>([]);
  const onSelectRef = useRef(onSelectCitation);
  const onUnavailableRef = useRef(onUnavailable);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const markerKey = useMemo(
    () =>
      citations
        .map((c) => `${c.index}:${(c.inline_markers ?? []).map((m) => m.marker).join("|")}`)
        .join(";"),
    [citations],
  );

  onSelectRef.current = onSelectCitation;
  onUnavailableRef.current = onUnavailable;

  useEffect(() => {
    let cancelled = false;
    const markers = collectAnatomyMarkers(citations);

    async function renderPdf() {
      const container = containerRef.current;
      if (!container) return;

      setLoading(true);
      setError(null);
      container.innerHTML = "";
      overlayButtonsRef.current = [];

      try {
        const pdf = await pdfjsLib.getDocument(`/api/audits/${auditId}/paper.pdf`).promise;
        const scale = 1.15;

        for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
          if (cancelled) return;
          const page = await pdf.getPage(pageNumber);
          const viewport = page.getViewport({ scale });
          const pageWrap = document.createElement("div");
          pageWrap.className = "relative mb-4";
          pageWrap.style.width = `${viewport.width}px`;
          pageWrap.style.height = `${viewport.height}px`;

          const canvas = document.createElement("canvas");
          canvas.width = viewport.width;
          canvas.height = viewport.height;
          const context = canvas.getContext("2d");
          if (!context) continue;
          await page.render({ canvasContext: context, viewport }).promise;
          pageWrap.appendChild(canvas);

          const textContent = await page.getTextContent();
          for (const item of textContent.items) {
            if (!("str" in item) || typeof item.str !== "string") continue;
            const hit = findMarkerInString(item.str, markers);
            if (!hit) continue;

            const citation = hit.marker.citation;
            const label = item.str.slice(hit.start, hit.end);
            const tx = pdfjsLib.Util.transform(viewport.transform, item.transform);
            const x = tx[4];
            const y = viewport.height - tx[5] - 12;

            const button = document.createElement("button");
            button.type = "button";
            button.textContent = label;
            button.dataset.citationIndex = String(citation.index);
            button.title = `Citation #${citation.index}`;
            button.className = "absolute z-10 rounded px-1 font-audit text-[10px] font-bold text-white";
            button.style.left = `${x}px`;
            button.style.top = `${y}px`;
            applyCitationStyles(button, citation);
            button.onclick = () => onSelectRef.current(citation);
            pageWrap.appendChild(button);
            overlayButtonsRef.current.push(button);
          }

          if (!cancelled) container.appendChild(pageWrap);
        }

        if (!cancelled) setLoading(false);
      } catch {
        if (!cancelled) {
          setError("Source PDF unavailable.");
          setLoading(false);
          onUnavailableRef.current?.();
        }
      }
    }

    void renderPdf();
    return () => {
      cancelled = true;
      overlayButtonsRef.current = [];
    };
  }, [auditId, markerKey]);

  useEffect(() => {
    const byIndex = new Map(citations.map((c) => [c.index, c]));
    for (const button of overlayButtonsRef.current) {
      const index = Number(button.dataset.citationIndex);
      const citation = byIndex.get(index);
      if (citation) applyCitationStyles(button, citation);
    }
  }, [citations]);

  return (
    <div className="max-h-[28rem] overflow-auto rounded border border-white/10 bg-stone-950/40 p-2">
      {loading && (
        <p className="mb-2 text-sm text-[var(--papyrus-muted)]">Loading PDF with citation overlays…</p>
      )}
      {error && <p className="mb-2 text-sm text-amber-200">{error}</p>}
      <div
        ref={containerRef}
        className={`mx-auto w-fit ${loading && !error ? "opacity-0" : ""}`}
        aria-hidden={loading && !error}
      />
    </div>
  );
}
