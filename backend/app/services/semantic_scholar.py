from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings
from app.services.rate_limits import rate_limit_service


class SemanticScholarClient:
    BASE = "https://api.semanticscholar.org/graph/v1"

    def __init__(self) -> None:
        settings = get_settings()
        headers = {"User-Agent": "Papyrus/2.0"}
        if settings.semantic_scholar_api_key:
            headers["x-api-key"] = settings.semantic_scholar_api_key
        self._headers = headers

    async def lookup_doi(self, doi: str) -> dict[str, Any] | None:
        if not await rate_limit_service.allow("semantic_scholar"):
            return None
        normalized = doi.strip().removeprefix("https://doi.org/").removeprefix("http://doi.org/")
        fields = "title,authors,year,externalIds,abstract,isOpenAccess,openAccessPdf,publicationVenue"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE}/paper/DOI:{normalized}",
                params={"fields": fields},
                headers=self._headers,
            )
            await rate_limit_service.record("semantic_scholar")
            if response.status_code != 200:
                return None
            return self._normalize_paper(response.json())

    async def reference_dois(self, doi: str, limit: int = 50) -> list[str]:
        """Outbound reference DOIs for a resolved paper (bounded list)."""
        if not await rate_limit_service.allow("semantic_scholar"):
            return []
        normalized = doi.strip().removeprefix("https://doi.org/").removeprefix("http://doi.org/")
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.get(
                f"{self.BASE}/paper/DOI:{normalized}",
                params={"fields": "references.externalIds", "limit": limit},
                headers=self._headers,
            )
            await rate_limit_service.record("semantic_scholar")
            if response.status_code != 200:
                return []
            refs = response.json().get("references") or []
            dois: list[str] = []
            for ref in refs:
                external = ref.get("externalIds") or {}
                ref_doi = external.get("DOI")
                if ref_doi:
                    dois.append(ref_doi.strip().removeprefix("https://doi.org/"))
            return dois

    async def search_title(self, title: str) -> dict[str, Any] | None:
        if not await rate_limit_service.allow("semantic_scholar"):
            return None
        params = {
            "query": title,
            "limit": 1,
            "fields": "title,authors,year,externalIds,abstract,isOpenAccess,openAccessPdf",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.BASE}/paper/search", params=params, headers=self._headers)
            await rate_limit_service.record("semantic_scholar")
            if response.status_code != 200:
                return None
            data = response.json().get("data") or []
            if not data:
                return None
            return self._normalize_paper(data[0])

    def _normalize_paper(self, paper: dict[str, Any]) -> dict[str, Any]:
        external = paper.get("externalIds") or {}
        venue = paper.get("publicationVenue") or {}
        return {
            "title": paper.get("title"),
            "authors": [a.get("name", "") for a in paper.get("authors") or []],
            "year": paper.get("year"),
            "doi": external.get("DOI"),
            "abstract": paper.get("abstract"),
            "journal": venue.get("name"),
            "open_access_pdf": (paper.get("openAccessPdf") or {}).get("url"),
        }


semantic_scholar_client = SemanticScholarClient()
