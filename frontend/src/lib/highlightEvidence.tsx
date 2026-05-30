import type { ReactNode } from "react";

export function highlightEvidencePassage(passage: string, claim: string | null | undefined): ReactNode {
  if (!claim?.trim()) return passage;
  const sentences = passage.match(/[^.!?]+[.!?]?/g) ?? [passage];
  const claimLower = claim.toLowerCase();
  let best = passage;
  let bestScore = -1;
  for (const sentence of sentences) {
    const words = new Set(claimLower.split(/\s+/).filter((w) => w.length > 3));
    const sentLower = sentence.toLowerCase();
    let score = 0;
    for (const word of words) {
      if (sentLower.includes(word)) score += 1;
    }
    if (score > bestScore) {
      bestScore = score;
      best = sentence.trim();
    }
  }
  if (!passage.includes(best) || bestScore <= 0) {
    return passage;
  }
  const parts = passage.split(best);
  return (
    <>
      {parts[0]}
      <mark className="rounded bg-[#ecfdf3] px-0.5 text-[#1b4332] ring-1 ring-[#bbf7d0]">{best}</mark>
      {parts.slice(1).join(best)}
    </>
  );
}
