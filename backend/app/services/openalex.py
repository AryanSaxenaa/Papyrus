from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from app.config import get_settings


class OpenAlexClient:
    BASE = "https://api.openalex.org"

    def __init__(self) -> None:
        settings = get_settings()
        self._params = {"mailto": settings.openalex_mailto}

    async def search_title(self, title: str) -> dict[str, Any] | None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE}/works",
                params={**self._params, "search": title, "per_page": 1},
            )
            if response.status_code != 200:
                return None
            results = response.json().get("results") or []
            if not results:
                return None
            work = results[0]
            doi = (work.get("doi") or "").removeprefix("https://doi.org/")
            authorships = work.get("authorships") or []
            authors = [
                (a.get("author") or {}).get("display_name", "")
                for a in authorships
            ]
            return {
                "title": work.get("title"),
                "authors": [a for a in authors if a],
                "year": work.get("publication_year"),
                "doi": doi or None,
                "abstract": work.get("abstract"),
            }


openalex_client = OpenAlexClient()
