from __future__ import annotations

import hashlib
import json
from typing import Any

import httpx

from app.config import get_settings
from app.domain.enums import ResolutionSource
from app.services.cache import cache_service
from app.text.identifiers import author_title_query, normalize_doi
from app.text.similarity import compare_titles
from app.services.rate_limits import rate_limit_service

APIFY_BASE = "https://api.apify.com/v2"
_ARXIV_MERGE_FIELDS = ("abstract", "authors", "doi", "open_access_pdf")


class ApifyClient:
    """Structured retrieval fallback when direct APIs miss or rate-limit."""

    async def run_actor(self, actor_id: str, run_input: dict[str, Any]) -> list[dict[str, Any]] | None:
        settings = get_settings()
        if not settings.apify_api_token:
            return None
        if not await rate_limit_service.allow("apify"):
            return None

        cache_key = hashlib.sha256(f"{actor_id}:{json.dumps(run_input, sort_keys=True)}".encode()).hexdigest()
        cached = await cache_service.get_json("actor", cache_key)
        if cached is not None:
            return cached.get("items")

        actor_path = actor_id.replace("/", "~")
        url = f"{APIFY_BASE}/acts/{actor_path}/run-sync-get-dataset-items"
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                url,
                params={"token": settings.apify_api_token, "timeout": 120},
                json=run_input,
            )
            await rate_limit_service.record("apify")
            if response.status_code not in {200, 201}:
                return None
            items = response.json()
            if not isinstance(items, list):
                return None
            await cache_service.set_json("actor", cache_key, {"items": items})
            return items

    async def resolve_academic_mcp(self, title: str, authors: list[str] | None = None) -> dict[str, Any] | None:
        settings = get_settings()
        query = author_title_query(title, authors)
        items = await self.run_actor(
            settings.apify_actor_academic_mcp,
            {"query": query, "searchQuery": query, "searchTerms": query, "maxResults": 1, "maxItems": 1},
        )
        if not items:
            return None
        return _normalize_academic_item(items[0])

    async def resolve_by_title(self, title: str, authors: list[str] | None = None) -> dict[str, Any] | None:
        settings = get_settings()
        query = author_title_query(title, authors)

        mcp = await self.resolve_academic_mcp(title, authors)
        if mcp:
            return mcp

        openalex_items = await self.run_actor(
            settings.apify_actor_openalex,
            {"searchTerms": query, "maxItems": 1},
        )
        if openalex_items:
            return _normalize_openalex_item(openalex_items[0])

        epmc_items = await self.run_actor(
            settings.apify_actor_europe_pmc,
            {"searchQuery": title, "maxResults": 1},
        )
        if epmc_items:
            return _normalize_epmc_item(epmc_items[0])
        return None

    async def resolve_arxiv(self, arxiv_id: str) -> dict[str, Any] | None:
        settings = get_settings()
        primary = await self._resolve_arxiv_actor(settings.apify_actor_arxiv, arxiv_id)
        if not primary:
            return await self._resolve_arxiv_actor(settings.apify_actor_arxiv_secondary, arxiv_id)
        if all(primary.get(field) for field in _ARXIV_MERGE_FIELDS):
            return primary
        secondary = await self._resolve_arxiv_actor(settings.apify_actor_arxiv_secondary, arxiv_id)
        return self._merge_arxiv_results(primary, secondary, settings.apify_actor_arxiv_secondary)

    def _merge_arxiv_results(
        self,
        primary: dict[str, Any],
        secondary: dict[str, Any] | None,
        secondary_actor: str,
    ) -> dict[str, Any]:
        if not secondary:
            return primary
        p_title = primary.get("title") or ""
        s_title = secondary.get("title") or ""
        if p_title and s_title:
            ratio, _ = compare_titles(p_title, s_title)
            primary["arxiv_cross_validation"] = {
                "secondary_actor": secondary_actor,
                "title_similarity": round(ratio, 3),
            }
        for field in _ARXIV_MERGE_FIELDS:
            if not primary.get(field) and secondary.get(field):
                primary[field] = secondary.get(field)
        return primary

    async def _resolve_arxiv_actor(self, actor_id: str, arxiv_id: str) -> dict[str, Any] | None:
        items = await self.run_actor(actor_id, {"searchQuery": arxiv_id, "maxItems": 1})
        if not items:
            return None
        row = items[0]
        return {
            "title": row.get("title"),
            "abstract": row.get("abstract"),
            "authors": row.get("authors") or [],
            "year": _year_from_row(row),
            "doi": row.get("doi"),
            "open_access_pdf": row.get("pdfUrl") or row.get("pdf_url"),
            "source": ResolutionSource.APIFY.value,
            "apify_actor": actor_id,
        }

    async def resolve_openalex_secondary(self, title: str) -> dict[str, Any] | None:
        settings = get_settings()
        items = await self.run_actor(
            settings.apify_actor_openalex_secondary,
            {"searchTerms": title, "search": title, "query": title, "maxItems": 1},
        )
        if not items:
            return None
        normalized = _normalize_openalex_item(items[0])
        normalized["via"] = "openalex_apify_secondary"
        normalized["apify_actor"] = settings.apify_actor_openalex_secondary
        return normalized


async def apify_fallback_resolve(
    title: str | None,
    authors: list[str] | None,
    arxiv_id: str | None,
) -> dict[str, Any] | None:
    client = ApifyClient()
    if arxiv_id:
        result = await client.resolve_arxiv(arxiv_id)
        if result:
            return result
    if title:
        return await client.resolve_by_title(title, authors)
    return None


def _normalize_academic_item(row: dict[str, Any]) -> dict[str, Any]:
    title = row.get("title") or row.get("paperTitle") or row.get("name")
    abstract = row.get("abstract") or row.get("summary") or row.get("snippet")
    authors = row.get("authors") or row.get("authorNames") or []
    if isinstance(authors, str):
        authors = [authors]
    doi = row.get("doi") or row.get("DOI")
    if isinstance(doi, str):
        doi = normalize_doi(doi)
    return {
        "title": title,
        "abstract": abstract,
        "authors": authors if isinstance(authors, list) else [],
        "year": _year_from_row(row),
        "doi": doi,
        "open_access_pdf": row.get("pdfUrl") or row.get("pdf_url") or row.get("openAccessPdf"),
        "source": ResolutionSource.APIFY.value,
        "via": "academic_mcp",
    }


def _normalize_openalex_item(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": row.get("title") or row.get("display_name"),
        "abstract": row.get("abstract"),
        "authors": row.get("authors") or [],
        "year": row.get("year") or row.get("publication_year"),
        "doi": normalize_doi(row.get("doi") or "") or None,
        "source": ResolutionSource.APIFY.value,
    }


def _normalize_epmc_item(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": row.get("title"),
        "abstract": row.get("abstractText") or row.get("abstract"),
        "authors": [row.get("authorString")] if row.get("authorString") else [],
        "year": int(row["pubYear"]) if row.get("pubYear") else None,
        "doi": row.get("doi"),
        "source": ResolutionSource.APIFY.value,
    }


def _year_from_row(row: dict[str, Any]) -> int | None:
    for key in ("year", "publishedYear", "publicationYear"):
        if row.get(key):
            return int(row[key])
    return None
