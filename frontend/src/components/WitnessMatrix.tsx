import type { CitationRecord, ScholarEvidence } from "../types";

type WitnessKey = "crossref" | "openalex" | "semantic_scholar" | "scholar" | "author";

const WITNESSES: Array<{ key: WitnessKey; label: string; source: string }> = [
  { key: "crossref", label: "CrossRef", source: "crossref" },
  { key: "semantic_scholar", label: "Semantic Scholar", source: "semantic_scholar" },
  { key: "openalex", label: "OpenAlex", source: "openalex" },
  { key: "scholar", label: "Scholar", source: "serpapi_scholar" },
  { key: "author", label: "Author profile", source: "serpapi_scholar_author" },
];

function sourceMatches(attemptSource: string, expected: string): boolean {
  const norm = attemptSource.toLowerCase().replace(/-/g, "_");
  return norm === expected || norm.endsWith(expected);
}

function scholarState(evidence: ScholarEvidence | null | undefined): string {
  if (!evidence) return "skipped";
  if (evidence.state === "match" || evidence.state === "near" || evidence.state === "match_field_conflict") {
    return "hit";
  }
  if (evidence.state === "miss" || evidence.state === "fetch_error") return "unknown";
  return "skipped";
}

function dotClass(state: string): string {
  switch (state) {
    case "hit":
      return "bg-emerald-500 ring-emerald-200";
    case "miss":
      return "bg-zinc-300 ring-zinc-200";
    case "unknown":
      return "bg-zinc-200 ring-zinc-100 border border-dashed border-zinc-400";
    default:
      return "bg-transparent ring-zinc-200 border border-dashed border-zinc-300";
  }
}

function resolveState(citation: CitationRecord, key: WitnessKey): string {
  if (key === "scholar") return scholarState(citation.scholar);
  if (key === "author") {
    const presence = citation.scholar?.author_presence;
    if (presence === "confirmed") return "hit";
    if (presence === "unknown") return "unknown";
    return "skipped";
  }
  const witness = WITNESSES.find((w) => w.key === key);
  if (!witness) return "skipped";
  const attempt = citation.resolution_attempts.find((a) => sourceMatches(a.source, witness.source));
  if (!attempt) return "skipped";
  return attempt.success ? "hit" : "miss";
}

type Props = {
  citation: CitationRecord;
  compact?: boolean;
};

export function WitnessMatrix({ citation, compact }: Props) {
  return (
    <ul className={`flex ${compact ? "gap-1.5" : "flex-wrap gap-3"}`} role="list">
      {WITNESSES.map((witness) => {
        const state = resolveState(citation, witness.key);
        const aria =
          state === "hit"
            ? `${witness.label}: corroborated`
            : state === "unknown"
              ? `${witness.label}: unknown (not a failure)`
              : state === "miss"
                ? `${witness.label}: no match in this index`
                : `${witness.label}: not checked`;
        return (
          <li key={witness.key} role="listitem" className="flex items-center gap-1.5">
            <span
              className={`inline-block h-2.5 w-2.5 shrink-0 rounded-full ring-2 ${dotClass(state)}`}
              aria-label={aria}
              title={aria}
            />
            {!compact && <span className="text-xs text-zinc-600">{witness.label}</span>}
          </li>
        );
      })}
    </ul>
  );
}
