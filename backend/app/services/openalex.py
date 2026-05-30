from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from app.config import get_settings
from app.services.rate_limits import rate_limit_service

_OPENALEX_FALLBACK_STATUSES = {429, 403}


class OpenAlexClient:
    BASE = "https://api.openalex.org"

    def __init__(self) -> None:
        settings = get_settings()
        self._params = {"mailto": settings.openalex_mailto}

    async def lookup_doi(self, doi: str) -> dict[str, Any] | None:
        normalized = doi.strip().removeprefix("https://doi.org/").removeprefix("http://doi.org/")
        if not await rate_limit_service.allow("openalex"):
            return await self._apify_secondary_fallback(normalized)
        result, rate_limited = await self._lookup_doi_native(normalized)
        if result is not None:
            return result
        if rate_limited:
            return await self._apify_secondary_fallback(normalized)
        return None

    async def verify_journal_issn(self, issn: str) -> dict[str, Any] | None:
        """OpenAlex source lookup for ISSN-based journal existence verification."""
        if not await rate_limit_service.allow("openalex"):
            return None
        normalized = issn.replace("-", "")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE}/sources",
                params={**self._params, "filter": f"issn:{normalized}", "per_page": 1},
            )
            await rate_limit_service.record("openalex")
            if response.status_code != 200:
                return None
            results = response.json().get("results") or []
            if not results:
                return None
            source = results[0]
            return {
                "id": source.get("id"),
                "display_name": source.get("display_name"),
                "issn_l": source.get("issn_l"),
                "type": source.get("type"),
                "first_publication_year": source.get("first_publication_year"),
            }

    async def search_title(self, title: str) -> dict[str, Any] | None:
        if not await rate_limit_service.allow("openalex"):
            return await self._apify_secondary_fallback(title)
        result, rate_limited = await self._search_title_native(title)
        if result is not None:
            return result
        if rate_limited:
            return await self._apify_secondary_fallback(title)
        return None

    async def _lookup_doi_native(self, normalized_doi: str) -> tuple[dict[str, Any] | None, bool]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE}/works/https://doi.org/{quote(normalized_doi, safe='')}",
                params=self._params,
            )
            await rate_limit_service.record("openalex")
            if response.status_code in _OPENALEX_FALLBACK_STATUSES:
                return None, True
            if response.status_code != 200:
                return None, False
            return self._normalize_work(response.json()), False

    async def _search_title_native(self, title: str) -> tuple[dict[str, Any] | None, bool]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE}/works",
                params={**self._params, "search": title, "per_page": 1},
            )
            await rate_limit_service.record("openalex")
            if response.status_code in _OPENALEX_FALLBACK_STATUSES:
                return None, True
            if response.status_code != 200:
                return None, False
            results = response.json().get("results") or []
            if not results:
                return None, False
            return self._normalize_work(results[0]), False

    async def _apify_secondary_fallback(self, title_or_query: str) -> dict[str, Any] | None:
        from app.services.apify_client import ApifyClient

        return await ApifyClient().resolve_openalex_secondary(title_or_query)

    def _normalize_work(self, work: dict[str, Any]) -> dict[str, Any]:
        doi = (work.get("doi") or "").removeprefix("https://doi.org/")
        authorships = work.get("authorships") or []
        authors = [(a.get("author") or {}).get("display_name", "") for a in authorships]
        abstract = work.get("abstract")
        if abstract is None:
            inverted = work.get("abstract_inverted_index")
            if isinstance(inverted, dict):
                abstract = _reconstruct_abstract(inverted)
        return {
            "title": work.get("title"),
            "authors": [a for a in authors if a],
            "year": work.get("publication_year"),
            "doi": doi or None,
            "abstract": abstract,
        }


def _reconstruct_abstract(inverted: dict[str, list[int]]) -> str:
    positions: dict[int, str] = {}
    for word, idxs in inverted.items():
        for idx in idxs:
            positions[idx] = word
    return " ".join(positions[i] for i in sorted(positions))


openalex_client = OpenAlexClient()
