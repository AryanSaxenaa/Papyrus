from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings
from app.services.http_retry import get_with_throttle
from app.services.rate_limits import rate_limit_service
from app.text.identifiers import normalize_doi


class CrossRefClient:
    BASE = "https://api.crossref.org/works"

    def __init__(self) -> None:
        settings = get_settings()
        self._mailto = settings.crossref_mailto or ""
        self._headers = {
            "User-Agent": f"Papyrus/2.0 (mailto:{self._mailto})",
            "Accept": "application/json",
        }

    def _params(self) -> dict[str, str]:
        if self._mailto:
            return {"mailto": self._mailto}
        return {}

    async def resolve_doi(self, doi: str) -> dict[str, Any] | None:
        if not await rate_limit_service.allow("crossref"):
            return None
        normalized = normalize_doi(doi)
        if not normalized:
            return None
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await get_with_throttle(
                    "crossref",
                    lambda: client.get(
                        f"{self.BASE}/{normalized}",
                        headers=self._headers,
                        params=self._params(),
                    ),
                )
                await rate_limit_service.record("crossref")
                if response.status_code == 404:
                    return None
                if response.status_code >= 400:
                    return None
                message = response.json().get("message", {})
                result = self._normalize(message)
                if not result.get("abstract"):
                    negotiated = await self._negotiate_doi(client, normalized)
                    if negotiated:
                        result["abstract"] = negotiated.get("abstract") or result.get("abstract")
                        result["title"] = result.get("title") or negotiated.get("title")
                return result
        except (httpx.HTTPError, httpx.TimeoutException, ValueError):
            return None

    async def _negotiate_doi(self, client: httpx.AsyncClient, doi: str) -> dict[str, Any] | None:
        try:
            headers = {
                **self._headers,
                "Accept": "application/vnd.citationstyles.csl+json",
            }
            response = await get_with_throttle(
                "crossref",
                lambda: client.get(
                    f"https://doi.org/{doi}",
                    headers=headers,
                    follow_redirects=True,
                ),
            )
            if response.status_code != 200:
                return None
            try:
                payload = response.json()
            except ValueError:
                return None
        except (httpx.HTTPError, httpx.TimeoutException):
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
        doi_value = message.get("DOI")
        if isinstance(doi_value, str):
            doi_value = normalize_doi(doi_value) or doi_value
        return {
            "title": title,
            "authors": authors,
            "year": year,
            "journal": (message.get("container-title") or [""])[0],
            "volume": message.get("volume"),
            "issue": message.get("issue"),
            "doi": doi_value,
            "issn": issn_list[0] if issn_list else None,
            "abstract": message.get("abstract"),
            "retracted": retracted,
            "raw": message,
        }


crossref_client = CrossRefClient()
