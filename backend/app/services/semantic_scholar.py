from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings


class SemanticScholarClient:
    BASE = "https://api.semanticscholar.org/graph/v1"

    def __init__(self) -> None:
        settings = get_settings()
        headers = {"User-Agent": "Papyrus/2.0"}
        if settings.semantic_scholar_api_key:
            headers["x-api-key"] = settings.semantic_scholar_api_key
        self._headers = headers

    async def search_title(self, title: str) -> dict[str, Any] | None:
        params = {
            "query": title,
            "limit": 1,
            "fields": "title,authors,year,externalIds,abstract,isOpenAccess,openAccessPdf",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.BASE}/paper/search", params=params, headers=self._headers)
            if response.status_code != 200:
                return None
            data = response.json().get("data") or []
            if not data:
                return None
            paper = data[0]
            external = paper.get("externalIds") or {}
            return {
                "title": paper.get("title"),
                "authors": [a.get("name", "") for a in paper.get("authors") or []],
                "year": paper.get("year"),
                "doi": external.get("DOI"),
                "abstract": paper.get("abstract"),
                "open_access_pdf": (paper.get("openAccessPdf") or {}).get("url"),
            }


semantic_scholar_client = SemanticScholarClient()
