from __future__ import annotations

import re
from typing import Any

from app.domain.models import BibliographyEntry, ConcordanceReport, ScholarCandidate
from app.services.serpapi.client import SerpApiClient
from app.text.similarity import compare_titles


def build_scholar_query(entry: BibliographyEntry, *, tier2: bool = False) -> str:
    title = (entry.title or entry.raw or "").strip()
    if tier2 and entry.authors:
        surname = entry.authors[0].split()[-1]
        return f'{title} author:"{surname}"'
    return title


def parse_scholar_candidates(body: dict[str, Any]) -> list[ScholarCandidate]:
    results: list[ScholarCandidate] = []
    for item in body.get("organic_results") or []:
        title = item.get("title") or ""
        pub = item.get("publication_info") or {}
        authors_raw = pub.get("authors") or []
        authors: list[dict[str, Any]] = []
        for author in authors_raw:
            if isinstance(author, dict):
                authors.append({"name": author.get("name"), "author_id": author.get("author_id")})
            elif isinstance(author, str):
                authors.append({"name": author.replace("…", "").strip(), "author_id": None})
        inline = item.get("inline_links") or {}
        cited_by = inline.get("cited_by") or {}
        versions = inline.get("versions") or {}
        year = _extract_year(pub.get("summary") or "")
        results.append(
            ScholarCandidate(
                result_id=str(item.get("result_id") or item.get("position") or len(results)),
                title=title,
                link=item.get("link"),
                summary=pub.get("summary"),
                authors=authors,
                year=year,
                cited_by=cited_by.get("total"),
                cites_id=cited_by.get("cites_id"),
                versions_total=versions.get("total"),
                cluster_id=versions.get("cluster_id"),
                title_sim=0.0,
            )
        )
    return results[:3]


def _extract_year(summary: str) -> int | None:
    match = re.search(r"\b(19|20)\d{2}\b", summary)
    if match:
        return int(match.group(0))
    return None


def parse_cite_strings(body: dict[str, Any]) -> tuple[str | None, str | None]:
    apa = None
    mla = None
    for block in body.get("citations") or []:
        title = (block.get("title") or "").upper()
        if "APA" in title:
            apa = block.get("snippet")
        if "MLA" in title:
            mla = block.get("snippet")
    return apa, mla


def parse_author_articles(body: dict[str, Any]) -> list[dict[str, Any]]:
    articles: list[dict[str, Any]] = []
    for item in body.get("articles") or body.get("organic_results") or []:
        articles.append({"title": item.get("title"), "year": item.get("year")})
    return articles


class ScholarClient:
    def __init__(self, client: SerpApiClient | None = None) -> None:
        self._client = client or SerpApiClient()

    async def find_work(
        self,
        entry: BibliographyEntry,
        *,
        audit_id: str | None,
        citation_id: str | None,
        tier2: bool = False,
    ) -> tuple[dict[str, Any], list[ScholarCandidate]]:
        params: dict[str, Any] = {"q": build_scholar_query(entry, tier2=tier2)}
        if entry.year:
            params["as_ylo"] = entry.year
            params["as_yhi"] = entry.year
        body, _receipt = await self._client.search(
            "google_scholar",
            params,
            audit_id=audit_id,
            citation_id=citation_id,
        )
        candidates = parse_scholar_candidates(body)
        if entry.title:
            for candidate in candidates:
                ratio, _ = compare_titles(entry.title, candidate.title)
                candidate.title_sim = ratio
        return body, candidates

    async def canonical_citation(
        self,
        result_id: str,
        *,
        audit_id: str | None,
        citation_id: str | None,
    ) -> tuple[dict[str, Any], str | None, str | None]:
        body, _receipt = await self._client.search(
            "google_scholar_cite",
            {"q": result_id},
            audit_id=audit_id,
            citation_id=citation_id,
        )
        apa, mla = parse_cite_strings(body)
        return body, apa, mla

    async def author_articles(
        self,
        author_id: str,
        *,
        audit_id: str | None,
        citation_id: str | None,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        body, _receipt = await self._client.search(
            "google_scholar_author",
            {"author_id": author_id},
            audit_id=audit_id,
            citation_id=citation_id,
        )
        return body, parse_author_articles(body)


def compare_citation_fields(entry: BibliographyEntry, scholar_string: str) -> ConcordanceReport:
    authors = "unknown"
    year = "unknown"
    venue = "unknown"
    if entry.authors:
        first = entry.authors[0].split()[-1].lower()
        if first and first in scholar_string.lower():
            authors = "agree"
        else:
            authors = "disagree"
    if entry.year and str(entry.year) in scholar_string:
        year = "agree"
    elif entry.year:
        year = "disagree"
    if entry.journal and entry.journal.lower() in scholar_string.lower():
        venue = "agree"
    return ConcordanceReport(
        source_format="APA",
        authors=authors,  # type: ignore[arg-type]
        year=year,  # type: ignore[arg-type]
        venue=venue,  # type: ignore[arg-type]
        scholar_string=scholar_string,
    )


scholar_client_singleton = ScholarClient()


def lists_work(articles: list[dict[str, Any]], title: str, threshold: float = 0.9) -> bool:
    for article in articles:
        article_title = article.get("title")
        if not article_title:
            continue
        ratio, _ = compare_titles(title, str(article_title))
        if ratio >= threshold:
            return True
    return False
