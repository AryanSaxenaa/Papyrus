from __future__ import annotations

import httpx

from app.config import get_settings
from app.pipeline.evidence import _cosine


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


async def embedding_similarity(text_a: str, text_b: str) -> float | None:
    """Cosine similarity between two short texts via configured embedding backend."""
    if not text_a.strip() or not text_b.strip():
        return None
    vectors = await _embed_batch([text_a[:500], text_b[:500]])
    if not vectors or len(vectors) < 2:
        return None
    return _cosine(vectors[0], vectors[1])
