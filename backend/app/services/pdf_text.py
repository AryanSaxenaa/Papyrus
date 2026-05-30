from __future__ import annotations

from pathlib import Path

import fitz


def extract_paper_text(pdf_path: Path, max_chars: int = 80_000) -> str:
    doc = fitz.open(pdf_path)
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return text.strip()[:max_chars]
