from __future__ import annotations

import difflib
import re
from datetime import datetime, timezone

import httpx

from app.config import get_settings
from app.domain.enums import EvidenceTier, ResolutionSource
from app.domain.models import CitationRecord

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def chunk_text(text: str, max_chars: int = 2200) -> list[str]:
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


async def rank_chunks_openai(claim: str, chunks: list[str]) -> str | None:
    settings = get_settings()
    if not settings.openai_api_key or not chunks:
        return rank_chunks_lexical(claim, chunks)

    async with httpx.AsyncClient(timeout=60.0) as client:
        embed_response = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={"model": "text-embedding-3-small", "input": [claim, *chunks]},
        )
        if embed_response.status_code != 200:
            return rank_chunks_lexical(claim, chunks)

        vectors = [row["embedding"] for row in embed_response.json()["data"]]
        claim_vec = vectors[0]
        best_idx = 0
        best_score = -1.0
        for idx, chunk_vec in enumerate(vectors[1:]):
            score = _cosine(claim_vec, chunk_vec)
            if score > best_score:
                best_score = score
                best_idx = idx
        return chunks[best_idx]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


async def retrieve_passage(claim: str, text: str | None) -> str | None:
    if not text or not claim:
        return text
    chunks = chunk_text(text)
    if len(chunks) == 1:
        return chunks[0]
    settings = get_settings()
    if settings.openai_api_key:
        return await rank_chunks_openai(claim, chunks)
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
