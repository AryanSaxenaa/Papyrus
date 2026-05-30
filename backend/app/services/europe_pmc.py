from __future__ import annotations

from typing import Any

import httpx

from app.text.identifiers import normalize_doi


class EuropePMCClient:
    BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

    async def lookup_doi(self, doi: str) -> dict[str, Any] | None:
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
            if response.status_code != 200:
                return None
            results = response.json().get("resultList", {}).get("result") or []
            if not results:
                return None
            return self._normalize(results[0])

    async def lookup_title(self, title: str) -> dict[str, Any] | None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                self.BASE,
                params={"query": f'TITLE:"{title[:200]}"', "format": "json", "pageSize": 1},
            )
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
