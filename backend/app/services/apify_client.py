from __future__ import annotations

import hashlib
import json
from typing import Any

import httpx

from app.config import get_settings
from app.domain.enums import ResolutionSource
from app.services.cache import cache_service
from app.services.rate_limits import rate_limit_service

APIFY_BASE = "https://api.apify.com/v2"


class ApifyClient:
    """Structured retrieval fallback when direct APIs miss or rate-limit."""

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

    async def resolve_by_title(self, title: str, authors: list[str] | None = None) -> dict[str, Any] | None:
        settings = get_settings()
        query = f"{authors[0]} {title}" if authors else title

        openalex_items = await self.run_actor(
            settings.apify_actor_openalex,
            {"searchTerms": query, "maxItems": 1},
        )
        if openalex_items:
            return _normalize_openalex_item(openalex_items[0])

        epmc_items = await self.run_actor(
            settings.apify_actor_europe_pmc,
            {"searchQuery": title, "maxResults": 1},
        )
        if epmc_items:
            return _normalize_epmc_item(epmc_items[0])
        return None

    async def resolve_arxiv(self, arxiv_id: str) -> dict[str, Any] | None:
        settings = get_settings()
        items = await self.run_actor(
            settings.apify_actor_arxiv,
            {"searchQuery": arxiv_id, "maxItems": 1},
        )
        if not items:
            return None
        row = items[0]
        return {
            "title": row.get("title"),
            "abstract": row.get("abstract"),
            "authors": row.get("authors") or [],
            "year": _year_from_row(row),
            "doi": row.get("doi"),
            "open_access_pdf": row.get("pdfUrl") or row.get("pdf_url"),
            "source": ResolutionSource.APIFY.value,
        }


async def apify_fallback_resolve(
    title: str | None,
    authors: list[str] | None,
    arxiv_id: str | None,
) -> dict[str, Any] | None:
    client = ApifyClient()
    if arxiv_id:
        result = await client.resolve_arxiv(arxiv_id)
        if result:
            return result
    if title:
        return await client.resolve_by_title(title, authors)
    return None


def _normalize_openalex_item(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": row.get("title") or row.get("display_name"),
        "abstract": row.get("abstract"),
        "authors": row.get("authors") or [],
        "year": row.get("year") or row.get("publication_year"),
        "doi": (row.get("doi") or "").removeprefix("https://doi.org/") or None,
        "source": ResolutionSource.APIFY.value,
    }


def _normalize_epmc_item(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": row.get("title"),
        "abstract": row.get("abstractText") or row.get("abstract"),
        "authors": [row.get("authorString")] if row.get("authorString") else [],
        "year": int(row["pubYear"]) if row.get("pubYear") else None,
        "doi": row.get("doi"),
        "source": ResolutionSource.APIFY.value,
    }


def _year_from_row(row: dict[str, Any]) -> int | None:
    for key in ("year", "publishedYear", "publicationYear"):
        if row.get(key):
            return int(row[key])
    return None
