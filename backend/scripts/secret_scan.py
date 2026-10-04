#!/usr/bin/env python3
"""Scan tracked paths for accidental secrets. Exit 1 if any pattern matches."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # URL query params only (not Python dict keys or redaction regexes).
    ("api_key query param", re.compile(r"[?&]api_key=[A-Za-z0-9_\-]{16,}", re.I)),
    ("Bearer token", re.compile(r"Bearer\s+[A-Za-z0-9._\-]{20,}")),
    ("SERPAPI key assignment", re.compile(r"SERPAPI_API_KEY\s*=\s*[^\s#\r\n][A-Za-z0-9_\-]{7,}", re.I)),
    ("OpenAI-style sk-", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("long hex secret", re.compile(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", re.I)),
]

DEFAULT_PATHS = [
    ROOT / "backend" / "app",
    ROOT / "backend" / "tests",
    ROOT / "backend" / "scripts",
    ROOT / "docs",
    ROOT / "frontend" / "src",
]

SKIP_SUFFIXES = {".png", ".jpg", ".pdf", ".woff2", ".ico"}


def scan_file(path: Path) -> list[str]:
    if path.suffix.lower() in SKIP_SUFFIXES:
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    hits: list[str] = []
    for name, pattern in PATTERNS:
        if pattern.search(text):
            hits.append(f"{path.relative_to(ROOT)}: matched {name}")
    return hits


def main(argv: list[str]) -> int:
    paths = [Path(p) for p in argv[1:]] if len(argv) > 1 else DEFAULT_PATHS
    failures: list[str] = []
    for base in paths:
        if base.is_file():
            failures.extend(scan_file(base))
            continue
        if not base.exists():
            continue
        for file in base.rglob("*"):
            if file.is_file() and "node_modules" not in file.parts:
                if "__pycache__" in file.parts:
                    continue
                rel = file.relative_to(ROOT).as_posix()
                if rel in {"backend/tests/test_secret_scan.py", "docs/spec/PAPYRUS-FULL-SPEC.md"}:
                    continue
                if rel.startswith("docs/spec/"):
                    continue
                failures.extend(scan_file(file))
    if failures:
        for line in failures:
            print(line, file=sys.stderr)
        return 1
    print("secret scan: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
