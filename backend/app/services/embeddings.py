from __future__ import annotations

from typing import cast

import httpx

from app.config import get_settings
from app.text.similarity import cosine_similarity


def embeddings_api_enabled() -> bool:
    """True only when the chosen embeddings backend has credentials (no paid calls otherwise)."""
    settings = get_settings()
    backend = settings.embeddings_backend.lower()
    if backend == "lexical":
        return False
    if backend == "openrouter":
        return bool(settings.openrouter_api_key)
    if backend == "openai":
        return bool(settings.openai_api_key)
    if backend == "snowflake":
        return bool(settings.huggingface_api_key)
    return False


async def _embed_batch(texts: list[str]) -> list[list[float]] | None:
    settings = get_settings()
    if not texts or not embeddings_api_enabled():
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
                return cast(list[list[float]], data)

    if backend == "openrouter" and settings.openrouter_api_key:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.openrouter_base_url}/embeddings",
                headers={"Authorization": f"Bearer {settings.openrouter_api_key}"},
                json={"model": "text-embedding-3-small", "input": texts},
            )
            if response.status_code != 200:
                return None
            return [row["embedding"] for row in response.json()["data"]]

    if backend == "openai" and settings.openai_api_key:
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
    if not text_a.strip() or not text_b.strip():
        return None
    vectors = await _embed_batch([text_a[:500], text_b[:500]])
    if not vectors or len(vectors) < 2:
        return None
    return cosine_similarity(vectors[0], vectors[1])
