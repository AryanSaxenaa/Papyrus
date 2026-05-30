from __future__ import annotations

from typing import Any


def is_year_impossible(cited_year: int, journal_meta: dict[str, Any] | None) -> bool:
    if not journal_meta:
        return False
    first_year = journal_meta.get("first_issue") or journal_meta.get("published_online")
    if first_year and cited_year < int(first_year):
        return True
    return False


def is_resolved_metadata_mismatch(
    cited_year: int | None,
    cited_volume: str | None,
    crossref: dict[str, Any],
) -> bool:
    """Same DOI resolved — cited year/volume must match CrossRef record."""
    resolved_year = crossref.get("year")
    if cited_year is not None and resolved_year is not None:
        try:
            if int(cited_year) != int(resolved_year):
                return True
        except (TypeError, ValueError):
            # Unparseable year on either side — skip year check, still compare volume below.
            pass
    resolved_volume = crossref.get("volume")
    if cited_volume and resolved_volume:
        if str(cited_volume).strip().lower() != str(resolved_volume).strip().lower():
            return True
    return False
