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

    async def volume_has_issue_in_year(self, issn: str, volume: str, year: int) -> bool | None:
        """True if CrossRef lists works in this journal volume during year; False if not; None if unknown."""
        if not await rate_limit_service.allow("crossref"):
            return None
        settings = get_settings()
        normalized = issn.replace("-", "")
        filters = f"volume:{volume},from-issued-date:{year}-01-01,until-issued-date:{year}-12-31"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE}/{normalized}/works",
                params={"filter": filters, "rows": 1},
                headers={
                    "User-Agent": f"Papyrus/2.0 (mailto:{settings.crossref_mailto})",
                    "Accept": "application/json",
                },
            )
            await rate_limit_service.record("crossref")
            if response.status_code != 200:
                return None
            total = response.json().get("message", {}).get("total-results", 0)
            return int(total) > 0


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


journal_client = JournalMetadataClient()
