from __future__ import annotations

import re
from pathlib import Path
from xml.etree import ElementTree as ET

import httpx

from app.config import get_settings
from app.domain.models import BibliographyEntry, InlineCitation
from app.text.context_window import three_sentence_window


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
            volume = _bibl_scope(bibl, "volume")
            issue = _bibl_scope(bibl, "issue")
            pages = _bibl_scope(bibl, "page") or _bibl_scope(bibl, "pages")
            url = _extract_url(bibl)
            raw = ET.tostring(bibl, encoding="unicode")
            bibliography.append(
                BibliographyEntry(
                    index=idx,
                    raw=raw,
                    authors=[a for a in authors if a],
                    title=title,
                    year=year,
                    journal=journal,
                    volume=volume,
                    issue=issue,
                    pages=pages,
                    doi=doi,
                    url=url,
                )
            )

        inline: list[InlineCitation] = []
        for paragraph in root.findall(".//tei:p", NS):
            p_text = re.sub(r"\s+", " ", "".join(paragraph.itertext())).strip()
            if not p_text:
                continue
            for ref in paragraph.findall(".//tei:ref[@type='bibr']", NS):
                target = ref.attrib.get("target", "")
                match = re.search(r"#b(\d+)", target)
                if not match:
                    continue
                bib_index = int(match.group(1)) + 1
                marker = "".join(ref.itertext()).strip() or target
                context = three_sentence_window(p_text, marker)
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


def _extract_url(bibl: ET.Element) -> str | None:
    for idno in bibl.findall(".//tei:idno", NS):
        id_type = (idno.attrib.get("type") or "").lower()
        if id_type in {"url", "uri"} and idno.text:
            return idno.text.strip()
    return None


def _bibl_scope(bibl: ET.Element, unit: str) -> str | None:
    for scope in bibl.findall(f".//tei:biblScope[@unit='{unit}']", NS):
        if scope.text:
            return scope.text.strip()
        start = scope.attrib.get("from")
        end = scope.attrib.get("to")
        if start and end:
            return f"{start}-{end}"
        if start:
            return start
    return None


grobid_client = GrobidClient()
