from __future__ import annotations

import difflib

from app.domain.models import VersionEntry, VersionMismatchInfo
from app.pipeline.verdicts import compare_titles


def build_version_timeline(
    arxiv: dict | None,
    crossref: dict | None,
) -> VersionMismatchInfo | None:
    if not arxiv and not crossref:
        return None

    preprint = None
    if arxiv:
        preprint = VersionEntry(
            label="arXiv preprint",
            date=(arxiv.get("published") or "")[:10] or None,
            title=arxiv.get("title"),
            abstract=(arxiv.get("abstract") or "")[:1500] or None,
            source="arxiv",
        )

    published = None
    if crossref:
        published = VersionEntry(
            label="Published version",
            date=str(crossref.get("year")) if crossref.get("year") else None,
            title=crossref.get("title"),
            abstract=(crossref.get("abstract") or "")[:1500] or None,
            source="crossref",
        )

    material = False
    if preprint and published and preprint.title and published.title:
        ratio, _ = compare_titles(preprint.title, published.title)
        material = ratio < 0.75
        abs_a = preprint.abstract or ""
        abs_b = published.abstract or ""
        if abs_a and abs_b:
            abs_ratio = difflib.SequenceMatcher(None, abs_a[:500], abs_b[:500]).ratio()
            material = material or abs_ratio < 0.65

    return VersionMismatchInfo(
        preprint=preprint,
        published=published,
        revisions=[],
        material_difference=material,
    )
