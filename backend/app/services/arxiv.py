from __future__ import annotations

import re
from typing import Any
from xml.etree import ElementTree as ET

import httpx

from app.services.http_retry import get_with_throttle
from app.services.rate_limits import rate_limit_service
from app.text.identifiers import normalize_doi

ARXIV_ID = re.compile(r"(?:arxiv[.:]?\s*)?(\d{4}\.\d{4,5}(?:v\d+)?)", re.I)
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


class ArxivClient:
    EXPORT = "https://export.arxiv.org/api/query"

    def extract_id(self, doi_or_text: str | None) -> str | None:
        if not doi_or_text:
            return None
        if "arxiv" in doi_or_text.lower():
            match = ARXIV_ID.search(doi_or_text)
            return match.group(1) if match else None
        match = ARXIV_ID.match(doi_or_text.strip())
        return match.group(1) if match else None

    async def fetch_revision_entries(self, arxiv_id: str) -> list[dict[str, Any]]:
        base_id = re.sub(r"v\d+$", "", arxiv_id, flags=re.I)
        if not await rate_limit_service.allow("arxiv"):
            return []
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await get_with_throttle(
                "arxiv",
                lambda: client.get(
                    self.EXPORT,
                    params={
                        "search_query": f"id:{base_id}",
                        "max_results": 15,
                        "sortBy": "submittedDate",
                        "sortOrder": "ascending",
                    },
                ),
            )
            await rate_limit_service.record("arxiv")
            response.raise_for_status()
            root = ET.fromstring(response.text)
            entries = root.findall("atom:entry", ATOM_NS)
            revisions: list[dict[str, Any]] = []
            for entry in entries:
                entry_id = _text(entry.find("atom:id", ATOM_NS)) or ""
                if base_id not in entry_id:
                    continue
                version_label = "v1"
                match = re.search(r"v(\d+)$", entry_id)
                if match:
                    version_label = f"v{match.group(1)}"
                published = _text(entry.find("atom:published", ATOM_NS))
                updated = _text(entry.find("atom:updated", ATOM_NS))
                revisions.append(
                    {
                        "label": f"arXiv {version_label}",
                        "date": (updated or published or "")[:10] or None,
                        "title": _text(entry.find("atom:title", ATOM_NS)),
                        "abstract": (_text(entry.find("atom:summary", ATOM_NS)) or "")[:1500] or None,
                    }
                )
            return revisions

    async def fetch(self, arxiv_id: str) -> dict[str, Any] | None:
        if not await rate_limit_service.allow("arxiv"):
            return None
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await get_with_throttle(
                "arxiv",
                lambda: client.get(self.EXPORT, params={"id_list": arxiv_id}),
            )
            await rate_limit_service.record("arxiv")
            if response.status_code != 200:
                return None
            root = ET.fromstring(response.text)
            entry = root.find("atom:entry", ATOM_NS)
            if entry is None:
                return None
            title = _text(entry.find("atom:title", ATOM_NS))
            summary = _text(entry.find("atom:summary", ATOM_NS))
            published = _text(entry.find("atom:published", ATOM_NS))
            authors = [
                _text(author.find("atom:name", ATOM_NS))
                for author in entry.findall("atom:author", ATOM_NS)
            ]
            doi_link = None
            pdf_url = None
            for link in entry.findall("atom:link", ATOM_NS):
                if link.attrib.get("title") == "doi":
                    doi_link = link.attrib.get("href")
                if link.attrib.get("type") == "application/pdf":
                    pdf_url = link.attrib.get("href")
            doi_value = None
            if doi_link:
                doi_value = normalize_doi(doi_link.replace("http://dx.doi.org/", "")) or doi_link
            return {
                "title": title,
                "abstract": summary,
                "authors": [a for a in authors if a],
                "year": int(published[:4]) if published else None,
                "doi": doi_value,
                "arxiv_id": arxiv_id,
                "published": published,
                "open_access_pdf": pdf_url,
            }


def _text(node: ET.Element | None) -> str | None:
    if node is None or node.text is None:
        return None
    return re.sub(r"\s+", " ", node.text).strip()


arxiv_client = ArxivClient()
