"""PyMuPDF fallback when GROBID output is sparse or unavailable."""

from __future__ import annotations

import re
from pathlib import Path

import fitz

from app.domain.models import BibliographyEntry, InlineCitation


REFERENCES_HEADERS = re.compile(r"^(references|bibliography|works cited)\s*$", re.I)
DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)
YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")


def parse_pdf_fallback(pdf_path: Path) -> tuple[list[BibliographyEntry], list[InlineCitation], str | None]:
    doc = fitz.open(pdf_path)
    text = "\n".join(page.get_text() for page in doc)
    doc.close()

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    paper_title = lines[0][:200] if lines else None

    ref_start = None
    for idx, line in enumerate(lines):
        if REFERENCES_HEADERS.match(line):
            ref_start = idx + 1
            break

    bibliography: list[BibliographyEntry] = []
    if ref_start is not None:
        chunk = lines[ref_start:]
        entries = _split_reference_block(chunk)
        for index, entry_lines in enumerate(entries, start=1):
            raw = " ".join(entry_lines)
            doi_match = DOI_PATTERN.search(raw)
            year_match = YEAR_PATTERN.search(raw)
            bibliography.append(
                BibliographyEntry(
                    index=index,
                    raw=raw,
                    title=_guess_title(entry_lines),
                    year=int(year_match.group(0)) if year_match else None,
                    doi=doi_match.group(0) if doi_match else None,
                )
            )

    inline: list[InlineCitation] = []
    for match in re.finditer(r"\[(\d{1,3})\]", text):
        marker = match.group(0)
        bib_index = int(match.group(1))
        start = max(0, match.start() - 200)
        end = min(len(text), match.end() + 200)
        inline.append(
            InlineCitation(
                marker=marker,
                bibliography_index=bib_index,
                context_window=text[start:end].strip(),
            )
        )

    return bibliography, inline, paper_title


def _split_reference_block(lines: list[str]) -> list[list[str]]:
    entries: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if re.match(r"^\[\d+\]", line) or re.match(r"^\d+\.", line):
            if current:
                entries.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        entries.append(current)
    if not entries and lines:
        entries = [lines]
    return entries


def _guess_title(entry_lines: list[str]) -> str | None:
    if not entry_lines:
        return None
    candidate = entry_lines[0]
    candidate = re.sub(r"^\[\d+\]\s*", "", candidate)
    candidate = re.sub(r"^\d+\.\s*", "", candidate)
    return candidate[:240] if candidate else None
