from __future__ import annotations

import re
from pathlib import Path
from xml.etree import ElementTree as ET

import httpx

from app.config import get_settings
from app.domain.models import BibliographyEntry, InlineCitation


NS = {"tei": "http://www.tei-c.org/ns/1.0"}


class GrobidClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._url = settings.grobid_url.rstrip("/")

    async def parse_pdf(
        self, pdf_path: Path
    ) -> tuple[list[BibliographyEntry], list[InlineCitation], str | None, list[str]]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            with pdf_path.open("rb") as handle:
                files = {"input": (pdf_path.name, handle, "application/pdf")}
                data = {"consolidateCitations": "1", "includeRawCitations": "1"}
                response = await client.post(
                    f"{self._url}/api/processFulltextDocument",
                    files=files,
                    data=data,
                )
            response.raise_for_status()
            tei_xml = response.text

        try:
            root = ET.fromstring(tei_xml)
        except ET.ParseError as exc:
            raise ValueError(f"Failed to parse GROBID XML response: {exc}") from exc
        title_el = root.find(".//tei:titleStmt/tei:title", NS)
        paper_title = title_el.text.strip() if title_el is not None and title_el.text else None

        paper_authors: list[str] = []
        for author in root.findall(".//tei:sourceDesc//tei:author/tei:persName", NS):
            name = f"{_text(author.find('tei:forename', NS))} {_text(author.find('tei:surname', NS))}".strip()
            if name:
                paper_authors.append(name)

        bibliography: list[BibliographyEntry] = []
        for idx, bibl in enumerate(root.findall(".//tei:listBibl/tei:biblStruct", NS), start=1):
            title = _text(bibl.find(".//tei:title[@level='a']", NS)) or _text(bibl.find(".//tei:title", NS))
            authors = [
                f"{_text(a.find('tei:forename', NS))} {_text(a.find('tei:surname', NS))}".strip()
                for a in bibl.findall(".//tei:author/tei:persName", NS)
            ]
            year = _int(_text(bibl.find(".//tei:date", NS)))
            journal = _text(bibl.find(".//tei:title[@level='j']", NS))
            doi = _extract_doi(bibl)
            raw = ET.tostring(bibl, encoding="unicode")
            bibliography.append(
                BibliographyEntry(
                    index=idx,
                    raw=raw,
                    authors=[a for a in authors if a],
                    title=title,
                    year=year,
                    journal=journal,
                    doi=doi,
                )
            )

        inline: list[InlineCitation] = []
        for ref in root.findall(".//tei:ref[@type='bibr']", NS):
            target = ref.attrib.get("target", "")
            match = re.search(r"#b(\d+)", target)
            if not match:
                continue
            bib_index = int(match.group(1)) + 1  # Convert from 0-based to 1-based to match bibliography
            marker = "".join(ref.itertext()).strip() or target
            parent = ref
            context = _context_window(parent)
            inline.append(
                InlineCitation(marker=marker, bibliography_index=bib_index, context_window=context)
            )

        return bibliography, inline, paper_title, paper_authors


def _text(node: ET.Element | None) -> str | None:
    if node is None:
        return None
    value = "".join(node.itertext()).strip()
    return value or None


def _int(value: str | None) -> int | None:
    if not value:
        return None
    match = re.search(r"\d{4}", value)
    return int(match.group(0)) if match else None


def _extract_doi(bibl: ET.Element) -> str | None:
    for idno in bibl.findall(".//tei:idno", NS):
        if idno.attrib.get("type") == "DOI" and idno.text:
            return idno.text.strip()
    return None


def _context_window(node: ET.Element) -> str:
    return re.sub(r"\s+", " ", "".join(node.itertext())).strip()[:800]


grobid_client = GrobidClient()
