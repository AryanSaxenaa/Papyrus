from __future__ import annotations

import json

import httpx

from app.config import get_settings
from app.domain.enums import CitationIntent


class DeepSeekClient:
    async def _chat(self, system: str, user: str) -> str | None:
        settings = get_settings()
        if not settings.enable_deepseek or not settings.deepseek_api_key:
            return None

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.deepseek_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.deepseek_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.deepseek_model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0,
                    "response_format": {"type": "json_object"},
                },
            )
            if response.status_code != 200:
                return None
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def classify_intent(self, context: str) -> CitationIntent | None:
        raw = await self._chat(
            "Classify citation intent. Return JSON: {\"intent\": \"evidentiary|methodological|contrastive|background\"}",
            f"Citation context:\n{context[:1200]}",
        )
        if not raw:
            return None
        try:
            payload = json.loads(raw)
            return CitationIntent(payload["intent"])
        except (KeyError, ValueError, json.JSONDecodeError):
            return None

    async def extract_claim(self, context: str) -> str | None:
        raw = await self._chat(
            "Extract the single factual claim attributed to the cited source. Return JSON: {\"claim\": \"...\"}",
            f"Citation context:\n{context[:1200]}",
        )
        if not raw:
            return None
        try:
            payload = json.loads(raw)
            claim = payload.get("claim")
            return claim.strip() if isinstance(claim, str) and claim.strip() else None
        except (json.JSONDecodeError, AttributeError):
            return None


deepseek_client = DeepSeekClient()
