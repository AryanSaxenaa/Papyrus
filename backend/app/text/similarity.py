from __future__ import annotations

import difflib
import math
import re


def normalize_author_set(authors: list[str]) -> set[str]:
    result: set[str] = set()
    for author in authors:
        collapsed = re.sub(r"[^a-z0-9]", "", author.lower())
        if collapsed:
            result.add(collapsed)
    return result


def author_sets_equal(cited: list[str], resolved: list[str]) -> bool | None:
    """Return True/False when both sides have authors; None if comparison is not possible."""
    cited_set = normalize_author_set(cited)
    resolved_set = normalize_author_set(resolved)
    if not cited_set or not resolved_set:
        return None
    return cited_set == resolved_set


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return -1.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    norm_left = math.sqrt(sum(a * a for a in left))
    norm_right = math.sqrt(sum(b * b for b in right))
    if norm_left == 0.0 or norm_right == 0.0:
        return -1.0
    return dot / (norm_left * norm_right)


def compare_titles(cited: str | None, resolved: str | None) -> tuple[float, float]:
    if not cited or not resolved:
        return 0.0, 0.0
    cited_tokens = " ".join(sorted(cited.lower().split()))
    resolved_tokens = " ".join(sorted(resolved.lower().split()))
    ratio = difflib.SequenceMatcher(None, cited_tokens, resolved_tokens).ratio()
    partial = difflib.SequenceMatcher(None, cited.lower(), resolved.lower()).ratio()
    return ratio, partial
