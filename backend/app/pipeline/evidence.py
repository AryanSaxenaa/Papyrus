from __future__ import annotations

import difflib
from datetime import datetime, timezone

from app.config import get_settings
from app.services.embeddings import embedding_rank_best_chunk, embeddings_api_enabled
from app.domain.enums import EvidenceTier, ResolutionSource
from app.domain.models import CitationRecord
from app.text.sentences import split_sentences

try:
    import tiktoken

    _enc = tiktoken.get_encoding("cl100k_base")

    def _token_count(text: str) -> int:
        return len(_enc.encode(text, disallowed_special=()))
except ImportError:
    _enc = None

    def _token_count(text: str) -> int:
        return max(1, len(text.split()))


def chunk_text(text: str, max_tokens: int = 512, overlap_tokens: int = 64) -> list[str]:
    """Split text into overlapping chunks of approximately max_tokens tokens.

    Respects sentence boundaries where possible. Overlap ensures claims
    straddling chunk boundaries are still retrievable.
    """
    sentences = split_sentences(text)
    if not sentences:
        return [text[:max_tokens * 4]] if text else []

    if _token_count(text) <= max_tokens:
        return [text]

    chunks: list[str] = []
    i = 0
    while i < len(sentences):
        chunk: list[str] = []
        token_count = 0
        j = i
        while j < len(sentences):
            s_tokens = _token_count(sentences[j])
            if token_count + s_tokens > max_tokens and chunk:
                break
            chunk.append(sentences[j])
            token_count += s_tokens
            j += 1

        if not chunk and j < len(sentences):
            chunk.append(sentences[j])
            j += 1

        chunks.append(" ".join(chunk))

        overlap_tok = 0
        overlap_count = 0
        for k in range(j - 1, i - 1, -1):
            s_tokens = _token_count(sentences[k])
            if overlap_tok + s_tokens > overlap_tokens and overlap_count > 0:
                break
            overlap_count += 1
            overlap_tok += s_tokens

        i = j - overlap_count

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
    if embeddings_api_enabled():
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


TIER_2_ABSTRACT_CAVEAT = (
    "Analysis based on abstract only — full text unavailable. Specific numerical claims, "
    "methods details, and supplementary results cannot be verified from the abstract alone."
)


async def refresh_evidence_passage(record: CitationRecord) -> None:
    claim = record.claim_user_corrected or record.extracted_claim or ""
    text = full_evidence_text(record)
    record.evidence_passage = await retrieve_passage(claim, text) if claim else text
    record.evidence_provenance = build_evidence_provenance(record)
    record.evidence_retrieved_at = datetime.now(timezone.utc)
    if record.evidence_tier == EvidenceTier.TIER_2:
        record.abstract_only_caveat = TIER_2_ABSTRACT_CAVEAT
    else:
        record.abstract_only_caveat = None
