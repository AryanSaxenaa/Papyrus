from __future__ import annotations

import difflib

from app.domain.models import VersionEntry, VersionMismatchInfo
from app.pipeline.verdicts import compare_titles
from app.services.apify_client import ApifyClient
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


async def enrich_version_timeline(
    info: VersionMismatchInfo,
    arxiv_id: str | None,
) -> VersionMismatchInfo:
    if not arxiv_id:
        return info

    revisions: list[VersionEntry] = []
    raw_revisions = await arxiv_client.fetch_revision_entries(arxiv_id)
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

    if not revisions:
        apify_row = await ApifyClient().resolve_arxiv(arxiv_id)
        if apify_row:
            revisions = _revisions_from_apify(apify_row)

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


def _revisions_from_apify(row: dict) -> list[VersionEntry]:
    revisions: list[VersionEntry] = []
    raw_versions = row.get("versions") or row.get("versionHistory") or row.get("revisions") or []
    if isinstance(raw_versions, list):
        for item in raw_versions:
            if not isinstance(item, dict):
                continue
            revisions.append(
                VersionEntry(
                    label=item.get("version") or item.get("label") or "Revision",
                    date=_coerce_date(item),
                    title=item.get("title"),
                    abstract=(item.get("abstract") or item.get("summary") or "")[:1500] or None,
                    source="apify",
                )
            )
    return revisions


def _coerce_date(item: dict) -> str | None:
    for key in ("date", "submittedDate", "published", "updated"):
        value = item.get(key)
        if value:
            return str(value)[:10]
    return None
