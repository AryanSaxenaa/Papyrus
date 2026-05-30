from __future__ import annotations

import httpx

from app.config import get_settings
from app.text.similarity import cosine_similarity


async def _embed_batch(texts: list[str]) -> list[list[float]] | None:
    settings = get_settings()
    if not texts:
        return None

    backend = settings.embeddings_backend.lower()
    if backend == "snowflake" and settings.huggingface_api_key:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api-inference.huggingface.co/pipeline/feature-extraction/"
                + settings.snowflake_embedding_model,
                headers={"Authorization": f"Bearer {settings.huggingface_api_key}"},
                json={"inputs": texts, "options": {"wait_for_model": True}},
            )
            if response.status_code != 200:
                return None
            data = response.json()
            if isinstance(data, list) and data and isinstance(data[0], list):
                if isinstance(data[0][0], list):
                    return data  # type: ignore[return-value]
                return data  # type: ignore[return-value]

    if settings.openai_api_key:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={"model": "text-embedding-3-small", "input": texts},
            )
            if response.status_code != 200:
                return None
            return [row["embedding"] for row in response.json()["data"]]
    return None


async def embedding_rank_best_chunk(claim: str, chunks: list[str]) -> str | None:
    """Pick the chunk most similar to the claim using the configured embedding backend."""
    if not chunks or not claim.strip():
        return None
    if len(chunks) == 1:
        return chunks[0]
    vectors = await _embed_batch([claim[:500], *[c[:500] for c in chunks]])
    if not vectors or len(vectors) < 2:
        return None
    claim_vec = vectors[0]
    best_idx = 0
    best_score = -1.0
    for idx, chunk_vec in enumerate(vectors[1:]):
        score = cosine_similarity(claim_vec, chunk_vec)
        if score > best_score:
            best_score = score
            best_idx = idx
    return chunks[best_idx]


async def embedding_similarity(text_a: str, text_b: str) -> float | None:
    """Cosine similarity between two short texts via configured embedding backend."""
    if not text_a.strip() or not text_b.strip():
        return None
    vectors = await _embed_batch([text_a[:500], text_b[:500]])
    if not vectors or len(vectors) < 2:
        return None
    return cosine_similarity(vectors[0], vectors[1])
