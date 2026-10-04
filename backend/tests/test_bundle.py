from __future__ import annotations

import zipfile
from io import BytesIO
from uuid import uuid4

from app.domain.models import AuditRun, CitationRecord, BibliographyEntry
from app.services.evidence.bundle import build_evidence_zip, verify_zip_bytes
from app.services.serpapi.ledger import serpapi_ledger


def test_evidence_bundle_verify_passes(monkeypatch, tmp_path):
    monkeypatch.setenv("AUDIT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PERSISTENCE_BACKEND", "json")
    from app.config import get_settings

    get_settings.cache_clear()

    audit = AuditRun(id=uuid4(), paper_title="Test paper", status="complete")
    audit.citations = [
        CitationRecord(
            index=1,
            bibliography=BibliographyEntry(index=1, raw="x", title="Paper"),
        )
    ]
    serpapi_ledger.append(
        audit_id=str(audit.id),
        citation_id=None,
        engine="google_scholar",
        params={"q": "Paper"},
        search_metadata_id="meta-1",
        json_endpoint="https://serpapi.com/searches/example.json",
        http_status=200,
        credits=1,
        cache_hit=False,
        latency_ms=10,
        raw_key="k1",
        sha256_raw="abc",
    )

    blob = build_evidence_zip(audit)
    assert verify_zip_bytes(blob) is True
    with zipfile.ZipFile(BytesIO(blob)) as zf:
        names = zf.namelist()
        assert "manifest.json" in names
        assert "verify.py" in names
        assert "api_key" not in zf.read("manifest.json").decode("utf-8").lower()


def test_evidence_bundle_tamper_fails(monkeypatch, tmp_path):
    monkeypatch.setenv("AUDIT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PERSISTENCE_BACKEND", "json")
    from app.config import get_settings

    get_settings.cache_clear()

    audit = AuditRun(id=uuid4(), status="complete")
    original = build_evidence_zip(audit)
    tampered = BytesIO()
    with zipfile.ZipFile(BytesIO(original), "r") as zin:
        with zipfile.ZipFile(tampered, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for info in zin.infolist():
                data = zin.read(info.filename)
                if info.filename == "verdicts.json":
                    data = data + b" "
                zout.writestr(info, data)
    assert verify_zip_bytes(tampered.getvalue()) is False
