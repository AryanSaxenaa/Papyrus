from __future__ import annotations

import difflib

import httpx

from app.domain.models import VersionEntry, VersionMismatchInfo
from app.text.similarity import compare_titles
from app.services.arxiv import arxiv_client


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

    material = _material_difference(preprint, published)

    return VersionMismatchInfo(
        preprint=preprint,
        published=published,
        revisions=[],
        material_difference=material,
    )


def merge_semantic_scholar_version(
    info: VersionMismatchInfo,
    scholar: dict | None,
    crossref: dict | None,
) -> VersionMismatchInfo:
    """Enrich timeline when S2 links a preprint to a distinct published DOI/title."""
    if not scholar or not info.preprint:
        return info
    scholar_doi = scholar.get("doi")
    published_doi = (crossref or {}).get("doi")
    if scholar_doi and published_doi and normalize_doi_safe(scholar_doi) != normalize_doi_safe(published_doi):
        info.material_difference = True
    scholar_title = scholar.get("title")
    if scholar_title and info.published and info.published.title:
        ratio, _ = compare_titles(scholar_title, info.published.title)
        if ratio < 0.75:
            info.material_difference = True
    if scholar.get("publication_date") and info.preprint and not info.preprint.date:
        info.preprint.date = str(scholar["publication_date"])[:10]
    return info


def normalize_doi_safe(doi: str) -> str:
    return doi.strip().lower().removeprefix("https://doi.org/")


async def enrich_version_timeline(
    info: VersionMismatchInfo,
    arxiv_id: str | None,
) -> VersionMismatchInfo:
    if not arxiv_id:
        return info

    revisions: list[VersionEntry] = []
    try:
        raw_revisions = await arxiv_client.fetch_revision_entries(arxiv_id)
    except (OSError, httpx.HTTPError):
        raw_revisions = []
    for row in raw_revisions:
        revisions.append(
            VersionEntry(
                label=row.get("label") or "Revision",
                date=row.get("date"),
                title=row.get("title"),
                abstract=row.get("abstract"),
                source="arxiv",
            )
        )

    if revisions:
        info.revisions = revisions
    return info


def _material_difference(preprint: VersionEntry | None, published: VersionEntry | None) -> bool:
    if not preprint or not published or not preprint.title or not published.title:
        return False
    ratio, _ = compare_titles(preprint.title, published.title)
    material = ratio < 0.75
    abs_a = preprint.abstract or ""
    abs_b = published.abstract or ""
    if abs_a and abs_b:
        abs_ratio = difflib.SequenceMatcher(None, abs_a[:500], abs_b[:500]).ratio()
        material = material or abs_ratio < 0.65
    return material

