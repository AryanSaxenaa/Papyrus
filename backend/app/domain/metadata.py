from __future__ import annotations

from typing import TypedDict


class ResolvedMetadata(TypedDict, total=False):
    """Normalized bibliographic metadata from resolution providers."""

    title: str | None
    abstract: str | None
    authors: list[str]
    year: int | None
    doi: str | None
    open_access_pdf: str | None
    oa_url: str | None
    source: str
    via: str
