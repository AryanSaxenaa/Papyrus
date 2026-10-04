"""Shipped Shepherd replay set must come from a real sample-PDF audit, not a synthetic stub."""

from __future__ import annotations

import json
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "replay" / "demo-a"


def test_demo_a_manifest_from_sample_pdf() -> None:
    manifest = json.loads((FIXTURE / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["source_pdf"] == "2108.12837v1.pdf"
    assert manifest["citation_count"] >= 5


def test_demo_a_audit_has_real_resolution_traces() -> None:
    audit = json.loads((FIXTURE / "audit.json").read_text(encoding="utf-8"))
    citations = audit.get("citations") or []
    assert len(citations) >= 5
    with_attempts = [c for c in citations if c.get("resolution_attempts")]
    assert len(with_attempts) >= 3
    assert audit.get("paper_title")
