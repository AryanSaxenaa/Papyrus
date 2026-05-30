from __future__ import annotations

import asyncio
import logging

import httpx

from app.config import get_settings
from app.domain.enums import EvidenceTier, NliVerdict
from app.services.local_nli import classify_local
from app.services.ollama_nli import classify_ollama

logger = logging.getLogger(__name__)

NLI_MODEL = "cross-encoder/nli-deberta-v3-base"


async def classify_entailment(claim: str, evidence: str) -> NliVerdict | None:
    """NLI via configured backend chain, or None to use lexical fallback."""
    settings = get_settings()
    backend = settings.nli_backend.lower()

    if backend in {"auto", "ollama"}:
        result = await classify_ollama(claim, evidence)
        if result is not None:
            return result

    if backend in {"auto", "local"}:
        result = await asyncio.to_thread(classify_local, claim, evidence)
        if result is not None:
            return result

    if backend in {"auto", "hf"} and settings.huggingface_api_key:
        result = await _classify_huggingface(claim, evidence)
        if result is not None:
            return result

    if backend == "lexical":
        return None

    return None


async def _classify_huggingface(claim: str, evidence: str) -> NliVerdict | None:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(
            f"https://api-inference.huggingface.co/models/{NLI_MODEL}",
            headers={"Authorization": f"Bearer {settings.huggingface_api_key}"},
            json={"inputs": {"text": evidence[:2000], "text_pair": claim[:512]}},
        )
        if response.status_code != 200:
            logger.warning("HF NLI failed: %s", response.text[:200])
            return None
        label = _extract_label(response.json())
        return _map_label(label)


def _extract_label(payload: object) -> str | None:
    if isinstance(payload, list) and payload:
        item = payload[0]
        if isinstance(item, dict):
            if "label" in item:
                return str(item["label"]).upper()
            if "labels" in item and "scores" in item:
                labels = item["labels"]
                scores = item["scores"]
                if labels and scores:
                    return str(labels[int(max(range(len(scores)), key=scores.__getitem__))]).upper()
    if isinstance(payload, dict) and "label" in payload:
        return str(payload["label"]).upper()
    return None


def _map_label(label: str | None) -> NliVerdict | None:
    if not label:
        return None
    if "ENTAIL" in label:
        return NliVerdict.ENTAILS
    if "CONTRAD" in label:
        return NliVerdict.CONTRADICTS
    if "NEUTRAL" in label:
        return NliVerdict.NEUTRAL
    return None


def confidence_for_verdict(
    nli: NliVerdict,
    tier: EvidenceTier,
) -> tuple[str, str]:
    """Map NLI + tier to claim_alignment_verdict label and confidence token."""
    if nli == NliVerdict.ENTAILS:
        if tier == EvidenceTier.TIER_1:
            return "supported", "high"
        return "supported", "medium"
    if nli == NliVerdict.CONTRADICTS:
        if tier == EvidenceTier.TIER_1:
            return "claim_contradiction", "high"
        return "claim_contradiction", "medium"
    if tier == EvidenceTier.TIER_1:
        return "not_addressed", "medium"
    return "cannot_determine", "low"
