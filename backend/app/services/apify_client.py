from __future__ import annotations

import hashlib
import json
from typing import Any

import httpx

from app.config import get_settings
from app.domain.enums import ResolutionSource
from app.services.cache import cache_service
from app.text.similarity import coerce_author_list, compare_titles
from app.services.rate_limits import rate_limit_service

APIFY_BASE = "https://api.apify.com/v2"
_ARXIV_MERGE_FIELDS = ("abstract", "authors", "doi", "open_access_pdf")


class ApifyClient:
    """Apify fallbacks limited to arXiv metadata (and optional CrossRef journal ISSN lookup)."""

    async def run_actor(self, actor_id: str, run_input: dict[str, Any]) -> list[dict[str, Any]] | None:
        settings = get_settings()
        if not settings.apify_api_token:
            return None
        if not await rate_limit_service.allow("apify"):
            return None

        cache_key = hashlib.sha256(f"{actor_id}:{json.dumps(run_input, sort_keys=True)}".encode()).hexdigest()
        cached = await cache_service.get_json("actor", cache_key)
        if cached is not None:
            return cached.get("items")

        actor_path = actor_id.replace("/", "~")
        url = f"{APIFY_BASE}/acts/{actor_path}/run-sync-get-dataset-items"
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    url,
                    params={"token": settings.apify_api_token, "timeout": 120},
                    json=run_input,
                )
                await rate_limit_service.record("apify")
                if response.status_code not in {200, 201}:
                    return None
                items = response.json()
                if not isinstance(items, list):
                    return None
                await cache_service.set_json("actor", cache_key, {"items": items})
                return items
        except (httpx.HTTPError, OSError):
            return None

    async def resolve_arxiv(self, arxiv_id: str) -> dict[str, Any] | None:
        settings = get_settings()
        primary = await self._resolve_arxiv_actor(settings.apify_actor_arxiv, arxiv_id)
        if not primary:
            return await self._resolve_arxiv_actor(settings.apify_actor_arxiv_secondary, arxiv_id)
        if all(primary.get(field) for field in _ARXIV_MERGE_FIELDS):
            return primary
        secondary = await self._resolve_arxiv_actor(settings.apify_actor_arxiv_secondary, arxiv_id)
        return self._merge_arxiv_results(primary, secondary, settings.apify_actor_arxiv_secondary)

    def _merge_arxiv_results(
        self,
        primary: dict[str, Any],
        secondary: dict[str, Any] | None,
        secondary_actor: str,
    ) -> dict[str, Any]:
        if not secondary:
            return primary
        p_title = primary.get("title") or ""
        s_title = secondary.get("title") or ""
        if p_title and s_title:
            ratio, _ = compare_titles(p_title, s_title)
            primary["arxiv_cross_validation"] = {
                "secondary_actor": secondary_actor,
                "title_similarity": round(ratio, 3),
            }
        for field in _ARXIV_MERGE_FIELDS:
            if not primary.get(field) and secondary.get(field):
                primary[field] = secondary.get(field)
        return primary

    async def _resolve_arxiv_actor(self, actor_id: str, arxiv_id: str) -> dict[str, Any] | None:
        items = await self.run_actor(actor_id, {"searchQuery": arxiv_id, "maxItems": 1})
        if not items:
            return None
        row = items[0]
        return {
            "title": row.get("title"),
            "abstract": row.get("abstract"),
            "authors": coerce_author_list(row.get("authors") or []),
            "year": _year_from_row(row),
            "doi": row.get("doi"),
            "open_access_pdf": row.get("pdfUrl") or row.get("pdf_url"),
            "source": ResolutionSource.APIFY.value,
            "apify_actor": actor_id,
        }


async def apify_fallback_resolve(
    title: str | None,
    authors: list[str] | None,
    arxiv_id: str | None,
) -> dict[str, Any] | None:
    """Last-resort Apify path: arXiv ID only (OpenAlex and Europe PMC use direct APIs)."""
    _ = title, authors
    if not arxiv_id:
        return None
    return await ApifyClient().resolve_arxiv(arxiv_id)


def _year_from_row(row: dict[str, Any]) -> int | None:
    for key in ("year", "publishedYear", "publicationYear"):
        if row.get(key):
            return int(row[key])
    return None
