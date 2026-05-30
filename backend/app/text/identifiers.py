from __future__ import annotations


def normalize_doi(doi: str) -> str:
    """Strip whitespace and common DOI URL prefixes for API lookups."""
    normalized = doi.strip()
    normalized = normalized.removeprefix("https://doi.org/")
    normalized = normalized.removeprefix("http://doi.org/")
    return normalized


def author_title_query(title: str, authors: list[str] | None) -> str:
    """First-author + title query used by retrieval fallbacks."""
    if authors and authors[0]:
        return f"{authors[0]} {title}"
    return title
