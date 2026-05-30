from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

import httpx

from app.services.firecrawl import firecrawl_client
from app.services.unpaywall import unpaywall_client

ARXIV_ABS = re.compile(r"arxiv\.org/abs/([\d.]+v?\d*)", re.I)
ARXIV_PDF = re.compile(r"arxiv\.org/pdf/([\d.]+v?\d*)", re.I)
DOI_URL = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)
PMC_PDF = re.compile(r"(https?://[^\s\"']+/pdf/[^\s\"']+\.pdf)", re.I)
PMID_PATTERN = re.compile(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", re.I)


class UrlFetchService:
    async def download_pdf(self, url: str, destination: Path) -> Path:
        pdf_url = await self.resolve_pdf_url_async(url)
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            response = await client.get(pdf_url)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "pdf" not in content_type.lower() and not pdf_url.lower().endswith(".pdf"):
                raise ValueError("URL did not return a PDF — try uploading the file directly")
            destination.write_bytes(response.content)
        return destination

    async def resolve_pdf_url_async(self, url: str) -> str:
        try:
            return self.resolve_pdf_url(url)
        except ValueError:
            oa_pdf = await self._resolve_doi_open_access(url)
            if oa_pdf:
                return oa_pdf
            landing = await self._resolve_landing_pdf(url)
            if landing:
                return landing
            raise ValueError(
                "Could not resolve a PDF from this URL. Supported: arXiv, DOI with open access, "
                "PubMed/PMC (via Firecrawl), and direct .pdf links."
            )

    async def _resolve_doi_open_access(self, url: str) -> str | None:
        doi_match = DOI_URL.search(url)
        if not doi_match and "doi.org" not in urlparse(url).netloc.lower():
            return None
        doi = doi_match.group(0) if doi_match else urlparse(url).path.strip("/")
        if not doi:
            return None
        unpaywall = await unpaywall_client.lookup(doi)
        if not unpaywall:
            return None
        return unpaywall.get("open_access_pdf") or unpaywall.get("oa_url")

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

        raise ValueError("Unsupported direct URL pattern")

    async def _resolve_landing_pdf(self, url: str) -> str | None:
        host = urlparse(url).netloc.lower()
        if "ncbi.nlm.nih.gov" in host or "pubmed" in host:
            return await self._pubmed_pdf(url)
        if "ssrn.com" in host:
            return await self._ssrn_pdf(url)
        scraped = await firecrawl_client.scrape_landing_page(url)
        if not scraped:
            return None
        return self._pdf_from_scrape(scraped)

    def _pdf_from_scrape(self, scraped: dict) -> str | None:
        body = scraped.get("markdown") or scraped.get("abstract") or ""
        match = PMC_PDF.search(body)
        return match.group(1) if match else None

    async def _ssrn_pdf(self, url: str) -> str | None:
        scraped = await firecrawl_client.scrape_landing_page(url)
        if scraped:
            return self._pdf_from_scrape(scraped)
        return None

    async def _pubmed_pdf(self, url: str) -> str | None:
        scraped = await firecrawl_client.scrape_landing_page(url)
        if scraped:
            found = self._pdf_from_scrape(scraped)
            if found:
                return found
        pmid_match = PMID_PATTERN.search(url)
        if pmid_match:
            pmc_search = await firecrawl_client.scrape_landing_page(
                f"https://pubmed.ncbi.nlm.nih.gov/{pmid_match.group(1)}/"
            )
            if pmc_search:
                return self._pdf_from_scrape(pmc_search)
        return None


url_fetch_service = UrlFetchService()
