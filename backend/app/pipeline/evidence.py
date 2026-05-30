from __future__ import annotations

import difflib
import re
from datetime import datetime, timezone

from app.config import get_settings
from app.services.embeddings import embedding_rank_best_chunk
from app.domain.enums import EvidenceTier, ResolutionSource
from app.domain.models import CitationRecord

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def chunk_text(text: str, max_chars: int = 2048) -> list[str]:
    sentences = [s.strip() for s in SENTENCE_SPLIT.split(text) if s.strip()]
    if not sentences:
        return [text[:max_chars]] if text else []

    chunks: list[str] = []
    current: list[str] = []
    length = 0
    for sentence in sentences:
        if length + len(sentence) > max_chars and current:
            chunks.append(" ".join(current))
            current = [sentence]
            length = len(sentence)
        else:
            current.append(sentence)
            length += len(sentence)
    if current:
        chunks.append(" ".join(current))
    return chunks


def rank_chunks_lexical(claim: str, chunks: list[str]) -> str | None:
    if not chunks:
        return None
    scored = [
        (difflib.SequenceMatcher(None, claim.lower(), chunk.lower()).ratio(), chunk)
        for chunk in chunks
    ]
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[0][1]


async def retrieve_passage(claim: str, text: str | None) -> str | None:
    if not text or not claim:
        return text
    chunks = chunk_text(text)
    if len(chunks) == 1:
        return chunks[0]
    settings = get_settings()
    if settings.openai_api_key or (
        settings.embeddings_backend.lower() == "snowflake" and settings.huggingface_api_key
    ):
        ranked = await embedding_rank_best_chunk(claim, chunks)
        if ranked:
            return ranked
    return rank_chunks_lexical(claim, chunks)


def full_evidence_text(record: CitationRecord) -> str | None:
    for attempt in record.resolution_attempts:
        payload = attempt.payload or {}
        if payload.get("full_text"):
            return payload["full_text"]
    parts: list[str] = []
    for attempt in record.resolution_attempts:
        payload = attempt.payload or {}
        if payload.get("abstract"):
            parts.append(payload["abstract"])
        if payload.get("text"):
            parts.append(payload["text"])
    if parts:
        return "\n\n".join(parts)
    if record.resolved_title:
        return record.resolved_title
    return None


def build_evidence_provenance(record: CitationRecord) -> str | None:
    tier = record.evidence_tier
    if tier == EvidenceTier.TIER_4:
        return None
    if tier == EvidenceTier.TIER_1:
        for attempt in reversed(record.resolution_attempts):
            if attempt.source == ResolutionSource.FULLTEXT and attempt.success:
                return f"Tier 1 — open-access full text via {attempt.source.value}"
            payload = attempt.payload or {}
            if payload.get("full_text"):
                return f"Tier 1 — full text from {attempt.source.value}"
        if record.oa_pdf_url:
            return "Tier 1 — open-access PDF (Unpaywall)"
        return "Tier 1 — full text"
    if tier == EvidenceTier.TIER_2:
        for attempt in record.resolution_attempts:
            payload = attempt.payload or {}
            if attempt.success and payload.get("abstract"):
                return f"Tier 2 — abstract from {attempt.source.value}"
        return "Tier 2 — abstract only"
    if tier == EvidenceTier.TIER_3:
        return "Tier 3 — metadata only (title/authors/year)"
    return None


async def refresh_evidence_passage(record: CitationRecord) -> None:
    claim = record.claim_user_corrected or record.extracted_claim or ""
    text = full_evidence_text(record)
    record.evidence_passage = await retrieve_passage(claim, text) if claim else text
    record.evidence_provenance = build_evidence_provenance(record)
    record.evidence_retrieved_at = datetime.now(timezone.utc)
