from __future__ import annotations

import httpx

from app.config import get_settings
from app.pipeline.evidence import _cosine


async def embedding_similarity(text_a: str, text_b: str) -> float | None:
    """Cosine similarity between two short texts via OpenAI embeddings."""
    settings = get_settings()
    if not settings.openai_api_key or not text_a.strip() or not text_b.strip():
        return None

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={"model": "text-embedding-3-small", "input": [text_a[:500], text_b[:500]]},
        )
        if response.status_code != 200:
            return None
        vectors = [row["embedding"] for row in response.json()["data"]]
        if len(vectors) < 2:
            return None
        return _cosine(vectors[0], vectors[1])
