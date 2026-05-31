from __future__ import annotations

from typing import Any

from app.text.similarity import coerce_author_list


def normalize_doi(doi: str) -> str:
    """Strip whitespace, URL prefixes, and trailing sentence punctuation from DOIs."""
    normalized = doi.strip()
    normalized = normalized.removeprefix("https://doi.org/")
    normalized = normalized.removeprefix("http://doi.org/")
    normalized = normalized.removeprefix("doi:")
    normalized = normalized.removeprefix("DOI:")
    return normalized.rstrip(".,;:)")


def author_title_query(title: str, authors: list[str] | Any | None) -> str:
    """First-author + title query used by retrieval fallbacks."""
    names = coerce_author_list(authors)
    if names:
        return f"{names[0]} {title}"
    return title
