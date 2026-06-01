from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings
from app.text.identifiers import normalize_doi


class UnpaywallClient:
    BASE = "https://api.unpaywall.org/v2"

    async def lookup(self, doi: str) -> dict[str, Any] | None:
        settings = get_settings()
        normalized = normalize_doi(doi)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE}/{normalized}",
                    params={"email": settings.unpaywall_email},
                )
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                payload = response.json()
                best = payload.get("best_oa_location") or {}
                pdf_url = best.get("url_for_pdf") or best.get("url")
                return {
                    "is_oa": payload.get("is_oa"),
                    "open_access_pdf": pdf_url,
                    "oa_url": pdf_url or best.get("url"),
                    "license": best.get("license"),
                    "host_type": best.get("host_type"),
                }
        except (httpx.HTTPError, httpx.TimeoutException, ValueError):
            return None


unpaywall_client = UnpaywallClient()
