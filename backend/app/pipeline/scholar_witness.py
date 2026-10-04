from __future__ import annotations

from uuid import UUID

from app.config import get_settings
from app.domain.enums import EvidenceTier, HallucinationType, ResolutionSource
from app.domain.models import CitationRecord, ResolutionAttempt, ScholarEvidence
from app.pipeline.scholar_match import match_scholar_candidates
from app.pipeline.scholar_verdicts import apply_scholar_post_rules
from app.services.events import event_bus
from app.services.serpapi.scholar import (
    ScholarClient,
    compare_citation_fields,
    lists_work,
    scholar_client_singleton,
)


def scope_includes(record: CitationRecord) -> bool:
    settings = get_settings()
    scope = settings.serpapi_scope
    if scope == "off":
        return False
    if scope == "all":
        return True
    return record.evidence_tier == EvidenceTier.TIER_4


async def run_scholar_witness(
    audit_id: UUID,
    record: CitationRecord,
    *,
    scholar_client: ScholarClient | None = None,
) -> ScholarEvidence | None:
    settings = get_settings()
    if not settings.serpapi_active():
        return ScholarEvidence(state="disabled")
    if not scope_includes(record):
        return ScholarEvidence(state="skipped", skipped_reason="scope")

    client = scholar_client or scholar_client_singleton()
    cited = record.bibliography
    audit_key = str(audit_id)

    try:
        _body, candidates = await client.find_work(
            cited,
            audit_id=audit_key,
            citation_id=record.id,
        )
    except Exception as exc:  # noqa: BLE001 — witness must not break pipeline
        return ScholarEvidence(state="fetch_error", skipped_reason=str(exc)[:200])

    best, state = match_scholar_candidates(cited, candidates)
    if state == "miss" and cited.title:
        try:
            _body2, candidates2 = await client.find_work(
                cited,
                audit_id=audit_key,
                citation_id=record.id,
                tier2=True,
            )
            best, state = match_scholar_candidates(cited, candidates2)
        except Exception:
            pass

    evidence = ScholarEvidence(state=state, best=best)
    record.resolution_attempts.append(
        ResolutionAttempt(
            source=ResolutionSource.SERPAPI_SCHOLAR,
            query=cited.title or cited.raw,
            success=state in {"match", "near", "match_field_conflict"},
            summary=state,
            payload={"best": best.model_dump() if best else None},
        )
    )
    event_bus.emit(
        audit_id,
        "serpapi.call",
        f"Scholar witness: {state}",
        citation_index=record.index,
        engine="google_scholar",
    )

    if state in {"near", "match_field_conflict"} and best:
        try:
            _cite_body, apa, _mla = await client.canonical_citation(
                best.result_id,
                audit_id=audit_key,
                citation_id=record.id,
            )
            if apa:
                evidence.concordance = compare_citation_fields(cited, apa)
                record.resolution_attempts.append(
                    ResolutionAttempt(
                        source=ResolutionSource.SERPAPI_SCHOLAR_CITE,
                        query=best.result_id,
                        success=True,
                        summary="cite",
                        payload={"apa": apa},
                    )
                )
        except Exception:
            pass

    if state in {"match", "match_field_conflict"} and best and best.authors:
        author_id = None
        for author in best.authors:
            if isinstance(author, dict) and author.get("author_id"):
                author_id = str(author["author_id"])
                break
        if author_id:
            try:
                _auth_body, articles = await client.author_articles(
                    author_id,
                    audit_id=audit_key,
                    citation_id=record.id,
                )
                if cited.title and lists_work(articles, cited.title):
                    evidence.author_presence = "confirmed"
                    evidence.author_matched_title = cited.title
                else:
                    evidence.author_presence = "unknown"
                record.resolution_attempts.append(
                    ResolutionAttempt(
                        source=ResolutionSource.SERPAPI_SCHOLAR_AUTHOR,
                        query=author_id,
                        success=evidence.author_presence == "confirmed",
                        summary=evidence.author_presence,
                    )
                )
            except Exception:
                evidence.author_presence = "unknown"

    if evidence.receipts:
        record.serpapi_receipts.extend(evidence.receipts)
    record.scholar = evidence
    apply_scholar_post_rules(record, evidence)
    return evidence
