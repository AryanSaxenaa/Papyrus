from __future__ import annotations

from typing import Any

import httpx

from app.services.http_retry import get_with_throttle
from app.services.rate_limits import rate_limit_service
from app.text.identifiers import normalize_doi


class EuropePMCClient:
    """Europe PMC REST search API (no Apify)."""

    BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

    async def lookup_doi(self, doi: str) -> dict[str, Any] | None:
        if not await rate_limit_service.allow("europe_pmc"):
            return None
        normalized = normalize_doi(doi)
        if not normalized:
            return None
        return await self._search(f'DOI:"{normalized}"')

    async def lookup_title(self, title: str) -> dict[str, Any] | None:
        if not await rate_limit_service.allow("europe_pmc"):
            return None
        trimmed = title.strip()[:200]
        if not trimmed:
            return None
        return await self._search(f'TITLE:"{trimmed}"')

    async def _search(self, query: str) -> dict[str, Any] | None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await get_with_throttle(
                "europe_pmc",
                lambda: client.get(
                    self.BASE,
                    params={"query": query, "format": "json", "pageSize": 1, "resultType": "core"},
                ),
            )
            await rate_limit_service.record("europe_pmc")
            if response.status_code != 200:
                return None
            results = response.json().get("resultList", {}).get("result") or []
            if not results:
                return None
            return self._normalize(results[0])

    def _normalize(self, row: dict[str, Any]) -> dict[str, Any]:
        abstract = row.get("abstractText")
        pdf_url = None
        if row.get("isOpenAccess") == "Y" and row.get("pmcid"):
            pdf_url = f"https://europepmc.org/articles/PMC{row['pmcid']}?pdf=render"
        doi = row.get("doi")
        if isinstance(doi, str):
            doi = normalize_doi(doi) or doi
        return {
            "title": row.get("title"),
            "abstract": abstract,
            "authors": [row.get("authorString", "")] if row.get("authorString") else [],
            "year": int(row["pubYear"]) if row.get("pubYear") else None,
            "doi": doi,
            "pmid": row.get("pmid"),
            "pmcid": row.get("pmcid"),
            "open_access_pdf": pdf_url,
            "journal": row.get("journalTitle"),
        }


europe_pmc_client = EuropePMCClient()
