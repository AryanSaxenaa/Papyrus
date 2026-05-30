import type { CitationRecord } from "../types";

const verdictColors: Record<string, string> = {
  supported: "#1f6b4a",
  failure: "#8b1e2f",
  retraction: "#8b1e2f",
  cannot_assess: "#3d5a73",
  neutral: "#5c6460",
  unresolvable: "#4a524e",
  resolving: "#b8860b",
  pending: "#2a312e",
  amber: "#b8860b",
};

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
        const color = verdictColors[citation.verdict_color] ?? verdictColors.pending;
        return (
          <button
            key={`${index}-cite`}
            type="button"
            onClick={() => onSelectCitation(citation)}
            className="mx-0.5 inline rounded px-1 font-audit text-xs font-semibold text-white transition hover:opacity-90"
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
