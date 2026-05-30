import type { CitationRecord } from "../types";
import { citationFill, isRetraction } from "../lib/verdictColors";

type Props = {
  text: string;
  citations: CitationRecord[];
  onSelectCitation: (citation: CitationRecord) => void;
};

export function PaperAnatomy({ text, citations, onSelectCitation }: Props) {
  const byIndex = new Map(citations.map((c) => [c.index, c]));
  const parts = text.split(/(\[\d+\])/g);

  return (
    <div className="text-sm leading-relaxed text-stone-200">
      {parts.map((part, index) => {
        const match = part.match(/^\[(\d+)\]$/);
        if (!match) {
          return <span key={`${index}-text`}>{part}</span>;
        }
        const citation = byIndex.get(Number(match[1]));
        if (!citation) {
          return <span key={`${index}-raw`}>{part}</span>;
        }
        const color = citationFill(citation);
        const ring = isRetraction(citation) ? "ring-1 ring-amber-400" : "";
        return (
          <button
            key={`${index}-cite`}
            type="button"
            onClick={() => onSelectCitation(citation)}
            className={`mx-0.5 inline rounded px-1 font-audit text-xs font-semibold text-white transition hover:opacity-90 ${ring}`}
            style={{ background: color }}
            title={`Citation #${citation.index}: ${citation.bibliography.title ?? "Reference"}`}
          >
            {part}
          </button>
        );
      })}
    </div>
  );
}
