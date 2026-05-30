from __future__ import annotations

from app.config import get_settings
from app.domain.enums import CitationIntent
from app.domain.models import BibliographyEntry, InlineCitation
from app.services.deepseek import deepseek_client
from app.services.openrouter import openrouter_client


async def _get_client():
    settings = get_settings()
    if settings.llm_backend == "openrouter" and settings.openrouter_api_key:
        return openrouter_client
    return deepseek_client


async def classify_intent(context: str) -> CitationIntent | None:
    client = await _get_client()
    return await client.classify_intent(context)


async def extract_claim(context: str) -> str | None:
    client = await _get_client()
    return await client.extract_claim(context)


async def parse_pdf_citations(
    pdf_text: str,
) -> tuple[list[BibliographyEntry], list[InlineCitation], str | None, list[str]] | None:
    client = await _get_client()
    return await client.parse_pdf_citations(pdf_text)
