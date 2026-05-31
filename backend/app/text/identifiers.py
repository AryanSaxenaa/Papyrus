from __future__ import annotations

from typing import Any

from app.text.similarity import coerce_author_list


def normalize_doi(doi: str) -> str:
    """Strip whitespace and common DOI URL prefixes for API lookups."""
    normalized = doi.strip()
    normalized = normalized.removeprefix("https://doi.org/")
    normalized = normalized.removeprefix("http://doi.org/")
    return normalized


def author_title_query(title: str, authors: list[str] | Any | None) -> str:
    """First-author + title query used by retrieval fallbacks."""
    names = coerce_author_list(authors)
    if names:
        return f"{names[0]} {title}"
    return title
