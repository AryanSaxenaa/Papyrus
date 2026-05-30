from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings
from app.services.apify_client import ApifyClient
from app.services.rate_limits import rate_limit_service
from app.text.identifiers import normalize_doi


class EuropePMCClient:
    BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

    async def lookup_doi(self, doi: str) -> dict[str, Any] | None:
        if not await rate_limit_service.allow("europe_pmc"):
            return await self._lookup_apify(doi=normalize_doi(doi))
        normalized = normalize_doi(doi)
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                self.BASE,
                params={
                    "query": f'DOI:"{normalized}"',
                    "format": "json",
                    "pageSize": 1,
                },
            )
            await rate_limit_service.record("europe_pmc")
            if response.status_code != 200:
                return await self._lookup_apify(doi=normalized)
            results = response.json().get("resultList", {}).get("result") or []
            if not results:
                return await self._lookup_apify(doi=normalized)
            return self._normalize(results[0])

    async def lookup_title(self, title: str) -> dict[str, Any] | None:
        if not await rate_limit_service.allow("europe_pmc"):
            return await self._lookup_apify(title=title)
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                self.BASE,
                params={"query": f'TITLE:"{title[:200]}"', "format": "json", "pageSize": 1},
            )
            await rate_limit_service.record("europe_pmc")
            if response.status_code != 200:
                return await self._lookup_apify(title=title)
            results = response.json().get("resultList", {}).get("result") or []
            if not results:
                return await self._lookup_apify(title=title)
            return self._normalize(results[0])

    async def _lookup_apify(self, *, doi: str | None = None, title: str | None = None) -> dict[str, Any] | None:
        settings = get_settings()
        if not settings.apify_api_token:
            return None
        query = doi or title
        if not query:
            return None
        items = await ApifyClient().run_actor(
            settings.apify_actor_europe_pmc,
            {"query": query, "maxItems": 1},
        )
        if not items and settings.apify_actor_europe_pmc_search:
            items = await ApifyClient().run_actor(
                settings.apify_actor_europe_pmc_search,
                {"searchTerm": query, "maxResults": 1},
            )
        if not items:
            return None
        row = items[0]
        return {
            "title": row.get("title"),
            "abstract": row.get("abstract") or row.get("abstractText"),
            "authors": row.get("authors") or [],
            "year": int(row["year"]) if row.get("year") else None,
            "doi": row.get("doi"),
            "open_access_pdf": row.get("pdfUrl") or row.get("pdf_url"),
            "journal": row.get("journalTitle") or row.get("journal"),
            "via": "apify",
        }

    def _normalize(self, row: dict[str, Any]) -> dict[str, Any]:
        abstract = row.get("abstractText")
        pdf_url = None
        if row.get("isOpenAccess") == "Y" and row.get("pmcid"):
            pdf_url = f"https://europepmc.org/articles/PMC{row['pmcid']}?pdf=render"
        return {
            "title": row.get("title"),
            "abstract": abstract,
            "authors": [row.get("authorString", "")] if row.get("authorString") else [],
            "year": int(row["pubYear"]) if row.get("pubYear") else None,
            "doi": row.get("doi"),
            "pmid": row.get("pmid"),
            "pmcid": row.get("pmcid"),
            "open_access_pdf": pdf_url,
            "journal": row.get("journalTitle"),
        }


europe_pmc_client = EuropePMCClient()
