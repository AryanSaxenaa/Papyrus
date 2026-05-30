from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

import httpx

ARXIV_ABS = re.compile(r"arxiv\.org/abs/([\d.]+v?\d*)", re.I)
ARXIV_PDF = re.compile(r"arxiv\.org/pdf/([\d.]+v?\d*)", re.I)
DOI_URL = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)


class UrlFetchService:
    async def download_pdf(self, url: str, destination: Path) -> Path:
        pdf_url = self.resolve_pdf_url(url)
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            response = await client.get(pdf_url)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "pdf" not in content_type.lower() and not pdf_url.lower().endswith(".pdf"):
                raise ValueError("URL did not return a PDF — try uploading the file directly")
            destination.write_bytes(response.content)
        return destination

    def resolve_pdf_url(self, url: str) -> str:
        parsed = urlparse(url.strip())
        host = (parsed.netloc or "").lower()
        path = parsed.path or ""

        arxiv_match = ARXIV_ABS.search(url) or ARXIV_PDF.search(url)
        if arxiv_match or "arxiv.org" in host:
            paper_id = arxiv_match.group(1) if arxiv_match else path.strip("/").split("/")[-1]
            return f"https://arxiv.org/pdf/{paper_id}.pdf"

        if "doi.org" in host or DOI_URL.search(url):
            doi = DOI_URL.search(url)
            doi_value = doi.group(0) if doi else path.strip("/")
            return f"https://doi.org/{doi_value}"

        if url.lower().endswith(".pdf"):
            return url

        raise ValueError(
            "Unsupported URL. Use arXiv, DOI, or a direct PDF link. "
            "PubMed/SSRN landing pages require Firecrawl (not yet enabled)."
        )

    def infer_title_hint(self, url: str) -> str | None:
        arxiv_match = ARXIV_ABS.search(url) or ARXIV_PDF.search(url)
        if arxiv_match:
            return f"arXiv:{arxiv_match.group(1)}"
        return url[:120]


url_fetch_service = UrlFetchService()
