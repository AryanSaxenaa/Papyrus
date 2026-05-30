from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings
from app.services.apify_client import ApifyClient
from app.services.rate_limits import rate_limit_service


class JournalMetadataClient:
    """CrossRef journal endpoint for Type 5 (date impossible) checks."""

    BASE = "https://api.crossref.org/journals"

    async def lookup_issn(self, issn: str) -> dict[str, Any] | None:
        if not await rate_limit_service.allow("crossref"):
            return None
        settings = get_settings()
        normalized = issn.replace("-", "")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE}/{normalized}",
                headers={
                    "User-Agent": f"Papyrus/2.0 (mailto:{settings.crossref_mailto})",
                    "Accept": "application/json",
                },
            )
            await rate_limit_service.record("crossref")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            message = response.json().get("message", {})
            return {
                "title": (message.get("title") or ""),
                "issn": normalized,
                "published_online": _year_from_parts(message.get("published-online", {}).get("date-parts")),
                "first_issue": _first_issue_year(message),
            }

    async def lookup_issn_apify(self, issn: str) -> dict[str, Any] | None:
        settings = get_settings()
        normalized = issn.replace("-", "")
        items = await ApifyClient().run_actor(
            settings.apify_actor_crossref_journals,
            {"issn": normalized, "maxItems": 1},
        )
        if not items:
            return None
        row = items[0]
        first_year = row.get("firstIssueYear") or row.get("first_issue_year") or row.get("startYear")
        return {
            "title": row.get("title") or row.get("journalTitle"),
            "issn": normalized,
            "published_online": int(first_year) if first_year else None,
            "first_issue": int(first_year) if first_year else None,
            "source": "apify",
        }


def _year_from_parts(parts: list | None) -> int | None:
    if not parts or not parts[0]:
        return None
    return int(parts[0][0]) if parts[0][0] else None


def _first_issue_year(message: dict[str, Any]) -> int | None:
    issues = message.get("issues") or []
    years = []
    for issue in issues:
        year = _year_from_parts(issue.get("published-online", {}).get("date-parts"))
        if year:
            years.append(year)
    return min(years) if years else _year_from_parts(message.get("published-online", {}).get("date-parts"))


def is_year_impossible(cited_year: int, journal_meta: dict[str, Any] | None) -> bool:
    if not journal_meta:
        return False
    first_year = journal_meta.get("first_issue") or journal_meta.get("published_online")
    if first_year and cited_year < int(first_year):
        return True
    return False


journal_client = JournalMetadataClient()
