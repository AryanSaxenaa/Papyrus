from __future__ import annotations

import hashlib
from pathlib import Path

import fitz
import httpx

from app.config import get_settings
from app.services.cache import cache_service

MAX_BYTES = 8 * 1024 * 1024


class FullTextService:
    async def fetch_open_access_text(self, pdf_url: str) -> str | None:
        cache_key = hashlib.sha256(pdf_url.encode()).hexdigest()
        cached = await cache_service.get_json("fulltext", cache_key)
        if cached and cached.get("text"):
            return cached["text"]

        settings = get_settings()
        cache_dir = Path(settings.audit_data_dir) / "fulltext"
        cache_dir.mkdir(parents=True, exist_ok=True)
        file_path = cache_dir / f"{cache_key}.pdf"

        try:
            async with httpx.AsyncClient(timeout=90.0, follow_redirects=True) as client:
                response = await client.get(pdf_url)
                response.raise_for_status()
                if len(response.content) > MAX_BYTES:
                    return None
                content_type = response.headers.get("content-type", "").lower()
                if "pdf" not in content_type and not pdf_url.lower().endswith(".pdf"):
                    return None
                file_path.write_bytes(response.content)

            doc = fitz.open(file_path)
            text = "\n".join(page.get_text() for page in doc)
            doc.close()
            text = text.strip()
            if not text:
                return None

            snippet = text[:120_000]
            await cache_service.set_json("fulltext", cache_key, {"text": snippet})
            return snippet
        except (httpx.HTTPError, OSError, RuntimeError, ValueError):
            return None
        finally:
            if file_path.exists():
                file_path.unlink(missing_ok=True)


fulltext_service = FullTextService()
