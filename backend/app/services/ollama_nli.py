from __future__ import annotations

import logging

import httpx

from app.config import get_settings
from app.domain.enums import NliVerdict

logger = logging.getLogger(__name__)

PROMPT = """You are an NLI classifier. Given a CLAIM and EVIDENCE passage, respond with exactly one word:
ENTAILS, CONTRADICTS, or NEUTRAL.

CLAIM: {claim}

EVIDENCE: {evidence}

Verdict:"""


async def classify_ollama(claim: str, evidence: str) -> NliVerdict | None:
    settings = get_settings()
    if not settings.ollama_base_url:
        return None

    prompt = PROMPT.format(claim=claim[:512], evidence=evidence[:1500])
    url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            url,
            json={
                "model": settings.ollama_nli_model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0},
            },
        )
        if response.status_code != 200:
            logger.warning("Ollama NLI failed: %s", response.text[:200])
            return None
        text = (response.json().get("response") or "").strip().upper()
        if "CONTRADICT" in text:
            return NliVerdict.CONTRADICTS
        if "ENTAIL" in text:
            return NliVerdict.ENTAILS
        if "NEUTRAL" in text:
            return NliVerdict.NEUTRAL
    return None
