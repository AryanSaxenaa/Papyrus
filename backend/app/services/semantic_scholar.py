from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings
from app.services.rate_limits import rate_limit_service
from app.text.identifiers import normalize_doi


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
        normalized = normalize_doi(doi)
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
