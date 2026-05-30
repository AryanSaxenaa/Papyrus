from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings
from app.services.rate_limits import rate_limit_service
from app.text.identifiers import normalize_doi


class CrossRefClient:
    BASE = "https://api.crossref.org/works"

    def __init__(self) -> None:
        settings = get_settings()
        self._headers = {
            "User-Agent": f"Papyrus/2.0 (mailto:{settings.crossref_mailto})",
            "Accept": "application/json",
        }

    async def resolve_doi(self, doi: str) -> dict[str, Any] | None:
        if not await rate_limit_service.allow("crossref"):
            return None
        normalized = normalize_doi(doi)
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.BASE}/{normalized}", headers=self._headers)
            await rate_limit_service.record("crossref")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            message = response.json().get("message", {})
            result = self._normalize(message)
            if not result.get("abstract"):
                negotiated = await self._negotiate_doi(client, normalized)
                if negotiated:
                    result["abstract"] = negotiated.get("abstract") or result.get("abstract")
                    result["title"] = result.get("title") or negotiated.get("title")
            return result

    async def _negotiate_doi(self, client: httpx.AsyncClient, doi: str) -> dict[str, Any] | None:
        headers = {
            **self._headers,
            "Accept": "application/vnd.citationstyles.csl+json",
        }
        response = await client.get(f"https://doi.org/{doi}", headers=headers, follow_redirects=True)
        if response.status_code != 200:
            return None
        try:
            payload = response.json()
        except ValueError:
            return None
        title = payload.get("title")
        if isinstance(title, list):
            title = title[0] if title else None
        return {"title": title, "abstract": payload.get("abstract")}

    def _normalize(self, message: dict[str, Any]) -> dict[str, Any]:
        title = (message.get("title") or [""])[0]
        authors = []
        for item in message.get("author", []):
            given = item.get("given", "")
            family = item.get("family", "")
            authors.append(f"{given} {family}".strip())
        issued = message.get("issued", {}).get("date-parts", [[None]])[0]
        year = issued[0] if issued else None
        retracted = any(
            update.get("type") == "retraction"
            for update in message.get("update-to", [])
        ) or message.get("update-type") == "retraction"
        issn_list = message.get("ISSN") or []
        return {
            "title": title,
            "authors": authors,
            "year": year,
            "journal": (message.get("container-title") or [""])[0],
            "volume": message.get("volume"),
            "issue": message.get("issue"),
            "doi": message.get("DOI"),
            "issn": issn_list[0] if issn_list else None,
            "abstract": message.get("abstract"),
            "retracted": retracted,
            "raw": message,
        }


crossref_client = CrossRefClient()
