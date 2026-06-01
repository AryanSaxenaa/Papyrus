from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from app.config import get_settings
from app.services.http_retry import get_with_throttle
from app.services.rate_limits import rate_limit_service
from app.text.identifiers import normalize_doi

_OPENALEX_RATE_LIMIT_STATUSES = {429, 403}


class OpenAlexClient:
    BASE = "https://api.openalex.org"

    def _params(self) -> dict[str, str]:
        settings = get_settings()
        params: dict[str, str] = {}
        if settings.openalex_mailto:
            params["mailto"] = settings.openalex_mailto
        if settings.openalex_api_key:
            params["api_key"] = settings.openalex_api_key
        return params

    async def lookup_doi(self, doi: str) -> dict[str, Any] | None:
        normalized = normalize_doi(doi)
        if not normalized:
            return None
        if not await rate_limit_service.allow("openalex"):
            return None
        try:
            result, _rate_limited = await self._lookup_doi_native(normalized)
            return result
        except (httpx.HTTPError, httpx.TimeoutException, ValueError):
            return None

    async def verify_journal_issn(self, issn: str) -> dict[str, Any] | None:
        """OpenAlex source lookup for ISSN-based journal existence verification."""
        if not await rate_limit_service.allow("openalex"):
            return None
        normalized = issn.replace("-", "")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await get_with_throttle(
                    "openalex",
                    lambda: client.get(
                        f"{self.BASE}/sources",
                        params={**self._params(), "filter": f"issn:{normalized}", "per_page": 1},
                    ),
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
        except (httpx.HTTPError, httpx.TimeoutException, ValueError):
            return None

    async def search_title(self, title: str) -> dict[str, Any] | None:
        if not await rate_limit_service.allow("openalex"):
            return None
        try:
            result, _rate_limited = await self._search_title_native(title)
            return result
        except (httpx.HTTPError, httpx.TimeoutException, ValueError):
            return None

    async def _lookup_doi_native(self, normalized_doi: str) -> tuple[dict[str, Any] | None, bool]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await get_with_throttle(
                "openalex",
                lambda: client.get(
                    f"{self.BASE}/works/https://doi.org/{quote(normalized_doi, safe='')}",
                    params=self._params(),
                ),
            )
            await rate_limit_service.record("openalex")
            if response.status_code in _OPENALEX_RATE_LIMIT_STATUSES:
                return None, True
            if response.status_code != 200:
                return None, False
            return self._normalize_work(response.json()), False

    async def _search_title_native(self, title: str) -> tuple[dict[str, Any] | None, bool]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await get_with_throttle(
                "openalex",
                lambda: client.get(
                    f"{self.BASE}/works",
                    params={**self._params(), "search": title, "per_page": 1},
                ),
            )
            await rate_limit_service.record("openalex")
            if response.status_code in _OPENALEX_RATE_LIMIT_STATUSES:
                return None, True
            if response.status_code != 200:
                return None, False
            results = response.json().get("results") or []
            if not results:
                return None, False
            return self._normalize_work(results[0]), False

    def _normalize_work(self, work: dict[str, Any]) -> dict[str, Any]:
        doi = normalize_doi((work.get("doi") or "").removeprefix("https://doi.org/")) or None
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
            "doi": doi,
            "abstract": abstract,
        }


def _reconstruct_abstract(inverted: dict[str, list[int]]) -> str:
    positions: dict[int, str] = {}
    for word, idxs in inverted.items():
        for idx in idxs:
            positions[idx] = word
    return " ".join(positions[i] for i in sorted(positions))


openalex_client = OpenAlexClient()
