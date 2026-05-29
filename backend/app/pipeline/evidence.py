from __future__ import annotations

import difflib
import re

import httpx

from app.config import get_settings

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
