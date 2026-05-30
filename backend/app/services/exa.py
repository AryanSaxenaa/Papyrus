from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings
from app.text.identifiers import author_title_query

EXA_ABSENCE_MESSAGE = (
    "Not found in any indexed source — signal only, not a verdict. Human review required."
)


class ExaClient:
    """Last-resort semantic search. Absence is never a hallucination verdict."""

    BASE = "https://api.exa.ai/search"

    async def weak_signal_search(self, title: str, authors: list[str] | None = None) -> dict[str, Any]:
        settings = get_settings()
        if not settings.exa_api_key:
            return {"found": False, "message": EXA_ABSENCE_MESSAGE, "skipped": True}

        query = author_title_query(title, authors)

        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                self.BASE,
                headers={"x-api-key": settings.exa_api_key, "Content-Type": "application/json"},
                json={"query": query, "numResults": 3, "type": "auto"},
            )
            if response.status_code != 200:
                return {"found": False, "message": EXA_ABSENCE_MESSAGE, "error": response.text[:200]}

            results = response.json().get("results") or []
            if not results:
                return {"found": False, "message": EXA_ABSENCE_MESSAGE}

            top = results[0]
            return {
                "found": True,
                "message": "Weak signal found via Exa — not a confirmed resolution.",
                "title": top.get("title"),
                "url": top.get("url"),
            }


exa_client = ExaClient()
