from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings


class FirecrawlClient:
    """Targeted landing-page scrape when structured metadata lacks an abstract."""

    BASE = "https://api.firecrawl.dev/v1/scrape"

    async def scrape_landing_page(self, url: str) -> dict[str, Any] | None:
        settings = get_settings()
        if not settings.firecrawl_api_key:
            return None

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                self.BASE,
                headers={
                    "Authorization": f"Bearer {settings.firecrawl_api_key}",
                    "Content-Type": "application/json",
                },
                json={"url": url, "formats": ["markdown"], "onlyMainContent": True},
            )
            if response.status_code != 200:
                return None
            data = response.json().get("data") or {}
            markdown = data.get("markdown") or ""
            metadata = data.get("metadata") or {}
            abstract = _extract_abstract(markdown)
            return {
                "title": metadata.get("title"),
                "abstract": abstract or markdown[:2000] if markdown else None,
                "source_url": url,
            }


def _extract_abstract(markdown: str) -> str | None:
    lowered = markdown.lower()
    for heading in ("## abstract", "# abstract", "**abstract**"):
        idx = lowered.find(heading)
        if idx == -1:
            continue
        chunk = markdown[idx : idx + 2500]
        lines = [line.strip() for line in chunk.splitlines() if line.strip()]
        if len(lines) > 1:
            return " ".join(lines[1:])[:2000]
    return None


firecrawl_client = FirecrawlClient()
