from __future__ import annotations

import re
import unicodedata

from app.domain.models import BibliographyEntry, ScholarCandidate
from app.text.similarity import compare_titles

MatchState = str  # match | near | miss | match_field_conflict


def normalize_title(title: str) -> str:
    text = unicodedata.normalize("NFKD", title).lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def match_scholar_candidates(
    entry: BibliographyEntry,
    candidates: list[ScholarCandidate],
) -> tuple[ScholarCandidate | None, MatchState]:
    if not candidates or not entry.title:
        return None, "miss"
    scored = sorted(candidates, key=lambda c: c.title_sim, reverse=True)
    best = scored[0]
    if best.title_sim >= 0.92:
        state: MatchState = "match"
    elif best.title_sim >= 0.78:
        state = "near"
    else:
        return None, "miss"
    if state == "match" and entry.year and best.year and entry.year != best.year:
        state = "match_field_conflict"
    if state in {"match", "match_field_conflict"} and entry.authors and best.authors:
        cited_surname = entry.authors[0].split()[-1].lower()
        scholar_names = " ".join(a.get("name", "") for a in best.authors if isinstance(a, dict)).lower()
        if cited_surname and cited_surname not in scholar_names:
            state = "match_field_conflict"
    return best, state
