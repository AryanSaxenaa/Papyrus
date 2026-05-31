from __future__ import annotations

import difflib
import math
import re
from typing import Any


def coerce_author_name(author: Any) -> str | None:
    """Normalize author entries from strings or API shapes (e.g. OpenAlex dicts)."""
    if author is None:
        return None
    if isinstance(author, str):
        text = author.strip()
        return text or None
    if isinstance(author, dict):
        for key in ("display_name", "name", "literal", "author", "authorName"):
            if key not in author:
                continue
            nested = author[key]
            if isinstance(nested, dict):
                return coerce_author_name(nested)
            if isinstance(nested, str):
                text = nested.strip()
                return text or None
        return None
    text = str(author).strip()
    return text or None


def coerce_author_list(authors: Any) -> list[str]:
    if not authors:
        return []
    if isinstance(authors, str):
        name = coerce_author_name(authors)
        return [name] if name else []
    if not isinstance(authors, list):
        name = coerce_author_name(authors)
        return [name] if name else []
    result: list[str] = []
    for item in authors:
        if isinstance(item, list):
            result.extend(coerce_author_list(item))
            continue
        name = coerce_author_name(item)
        if name:
            result.append(name)
    return result


def normalize_author_set(authors: list[str] | Any) -> set[str]:
    result: set[str] = set()
    for author in coerce_author_list(authors):
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
