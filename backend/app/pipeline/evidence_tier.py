from __future__ import annotations

from app.domain.enums import EvidenceTier


def tier_from_resolved(resolved: dict) -> EvidenceTier:
    if resolved.get("full_text"):
        return EvidenceTier.TIER_1
    if resolved.get("open_access_pdf") or resolved.get("oa_url"):
        return EvidenceTier.TIER_1
    if resolved.get("abstract"):
        return EvidenceTier.TIER_2
    if resolved.get("title"):
        return EvidenceTier.TIER_3
    return EvidenceTier.TIER_4


def tier_with_scholar(current: EvidenceTier, *, scholar_corroborated: bool) -> EvidenceTier:
    if not scholar_corroborated:
        return current
    if current == EvidenceTier.TIER_4:
        return EvidenceTier.TIER_3
    return current
