from __future__ import annotations

import json
import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
from app.domain.enums import CitationIntent
from app.domain.models import BibliographyEntry, InlineCitation


class DeepSeekClient:
    async def _chat(self, system: str, user: str) -> str | None:
        settings = get_settings()
        if not settings.enable_deepseek or not settings.deepseek_api_key:
            return None

        try:
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
                    logger.warning(
                        "DeepSeek chat failed: HTTP %s — %s",
                        response.status_code,
                        response.text[:200],
                    )
                    return None
                data = response.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content")
        except (httpx.HTTPError, httpx.TimeoutException, ValueError, KeyError, IndexError) as exc:
            logger.warning("DeepSeek chat request failed: %s", exc)
            return None

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

    async def parse_pdf_citations(
        self, pdf_text: str
    ) -> tuple[list[BibliographyEntry], list[InlineCitation], str | None, list[str]] | None:
        """Structured bibliography + inline map when GROBID output is unusable."""
        raw = await self._chat(
            "Parse an academic PDF text into bibliography and inline citations. "
            'Return JSON: {"paper_title": str|null, "paper_authors": [str], '
            '"bibliography": [{"index": int, "raw": str, "authors": [str], "title": str|null, '
            '"year": int|null, "journal": str|null, "volume": str|null, "issue": str|null, '
            '"pages": str|null, "doi": str|null}], '
            '"inline": [{"marker": str, "bibliography_index": int, "context_window": str}]}. '
            "context_window must be the citing sentence(s) around the marker (max 3 sentences).",
            pdf_text[:28000],
        )
        if not raw:
            return None
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return None
        bibliography: list[BibliographyEntry] = []
        for row in payload.get("bibliography") or []:
            if not isinstance(row, dict):
                continue
            bibliography.append(
                BibliographyEntry(
                    index=int(row.get("index") or len(bibliography) + 1),
                    raw=str(row.get("raw") or ""),
                    authors=[str(a) for a in row.get("authors") or [] if a],
                    title=row.get("title"),
                    year=int(row["year"]) if row.get("year") else None,
                    journal=row.get("journal"),
                    volume=str(row["volume"]) if row.get("volume") else None,
                    issue=str(row["issue"]) if row.get("issue") else None,
                    pages=str(row["pages"]) if row.get("pages") else None,
                    doi=row.get("doi"),
                )
            )
        if not bibliography:
            return None
        inline: list[InlineCitation] = []
        for row in payload.get("inline") or []:
            if not isinstance(row, dict):
                continue
            inline.append(
                InlineCitation(
                    marker=str(row.get("marker") or ""),
                    bibliography_index=int(row.get("bibliography_index") or 0),
                    context_window=str(row.get("context_window") or "")[:1200],
                )
            )
        paper_title = payload.get("paper_title")
        paper_authors = [str(a) for a in payload.get("paper_authors") or [] if a]
        return bibliography, inline, paper_title if isinstance(paper_title, str) else None, paper_authors

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
