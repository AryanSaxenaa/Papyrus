"""HTTP surface tests for audit, bulk, mutations, and live ingest guards."""
from __future__ import annotations

import io
import json
import shutil
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "replay" / "demo-a"
MINIMAL_PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    audit_dir = tmp_path / "audits"
    fixture_dest = audit_dir / "fixtures" / "demo-a"
    fixture_dest.mkdir(parents=True)
    shutil.copy(FIXTURES / "audit.json", fixture_dest / "audit.json")
    shutil.copy(FIXTURES / "events.jsonl", fixture_dest / "events.jsonl")

    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("PERSISTENCE_BACKEND", "json")
    monkeypatch.setenv("AUDIT_DATA_DIR", str(audit_dir))
    monkeypatch.setenv("PAPYRUS_MODE", "live")
    monkeypatch.setenv("PUBLIC_DEMO_MODE", "true")
    monkeypatch.setenv("LIVE_ACCESS_CODE", "test-access-code")
    monkeypatch.setenv("NLI_BACKEND", "lexical")
    monkeypatch.setenv("EMBEDDINGS_BACKEND", "lexical")
    monkeypatch.setenv("USE_CELERY_BACKGROUND", "false")

    from app.config import get_settings

    get_settings.cache_clear()
    from app.main import create_app

    with TestClient(create_app()) as client:
        yield client
    get_settings.cache_clear()


def _wait_audit(client: TestClient, audit_id: str, timeout_s: float = 30.0) -> dict:
    import time

    deadline = time.time() + timeout_s
    last: dict = {}
    while time.time() < deadline:
        response = client.get(f"/api/audits/{audit_id}")
        assert response.status_code == 200
        last = response.json()
        if last.get("status") in ("complete", "failed"):
            return last
        time.sleep(0.3)
    return last


def test_replay_mutations_delete_and_reports(api_client: TestClient) -> None:
    created = api_client.post("/api/audits/replay/demo-a")
    assert created.status_code == 202
    audit_id = created.json()["id"]
    audit = _wait_audit(api_client, audit_id)
    assert audit["status"] == "complete"
    assert audit["citations"]

    citation_id = audit["citations"][0]["id"]

    intent = api_client.patch(
        f"/api/audits/{audit_id}/citations/{citation_id}/intent",
        json={"intent": "methodological"},
    )
    assert intent.status_code == 200

    claim = api_client.patch(
        f"/api/audits/{audit_id}/citations/{citation_id}/claim",
        json={"claim": "Demo claim for alignment."},
    )
    assert claim.status_code == 200

    approve = api_client.post(f"/api/audits/{audit_id}/citations/{citation_id}/approve-claim")
    assert approve.status_code == 200

    rerun_nli = api_client.post(f"/api/audits/{audit_id}/citations/{citation_id}/rerun-nli")
    assert rerun_nli.status_code == 200

    with patch("app.pipeline.resolution.resolve_record", new_callable=AsyncMock):
        rerun = api_client.post(f"/api/audits/{audit_id}/citations/{citation_id}/rerun")
    assert rerun.status_code == 200

    assert api_client.get(f"/api/audits/{audit_id}/bundle.zip").status_code == 200
    assert api_client.get(f"/api/audits/{audit_id}/report.pdf").status_code == 200

    deleted = api_client.delete(f"/api/audits/{audit_id}")
    assert deleted.status_code == 204
    assert api_client.get(f"/api/audits/{audit_id}").status_code == 404


def test_live_ingest_guard_and_accept(api_client: TestClient) -> None:
    blocked = api_client.post("/api/audits/doi", json={"doi": "10.1038/nature12373"})
    assert blocked.status_code == 403

    headers = {"X-Access-Code": "test-access-code"}
    with patch("app.api.routes.enqueue_doi_audit", new_callable=AsyncMock) as enqueue:
        accepted = api_client.post(
            "/api/audits/doi",
            json={"doi": "10.1038/nature12373"},
            headers=headers,
        )
    assert accepted.status_code == 202
    enqueue.assert_awaited_once()

    with patch("app.api.routes.enqueue_url_audit", new_callable=AsyncMock) as enqueue_url:
        url_res = api_client.post(
            "/api/audits/url",
            json={"url": "https://arxiv.org/abs/2301.00001"},
            headers=headers,
        )
    assert url_res.status_code == 202
    enqueue_url.assert_awaited_once()

    with patch("app.api.routes.enqueue_pdf_audit", new_callable=AsyncMock) as enqueue_pdf:
        pdf_res = api_client.post(
            "/api/audits",
            headers=headers,
            files={"file": ("sample.pdf", MINIMAL_PDF, "application/pdf")},
        )
    assert pdf_res.status_code == 202
    enqueue_pdf.assert_awaited_once()


def test_bulk_job_surface(api_client: TestClient) -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("paper-a.pdf", MINIMAL_PDF)
    zip_bytes = buffer.getvalue()

    headers = {"X-Access-Code": "test-access-code"}

    async def _fake_bulk(job_id: UUID, storage_key: str) -> None:
        from app.bulk_store import bulk_job_store
        from app.services.events import event_bus

        job = bulk_job_store.get(job_id)
        if not job:
            return
        job.status = "complete"
        bulk_job_store.save(job)
        event_bus.emit(job_id, "bulk", "Bulk job complete (test stub)")

    async def _enqueue(job_id, storage_key, background):
        background.add_task(_fake_bulk, job_id, storage_key)
        return "background"

    with patch("app.api.routes.enqueue_bulk_zip", side_effect=_enqueue):
        created = api_client.post(
            "/api/audits/bulk",
            headers=headers,
            files={"file": ("bulk.zip", zip_bytes, "application/zip")},
        )
    assert created.status_code == 202
    job_id = created.json()["id"]

    import time

    deadline = time.time() + 5
    while time.time() < deadline:
        job = api_client.get(f"/api/bulk/{job_id}").json()
        if job.get("status") in ("complete", "failed"):
            break
        time.sleep(0.2)

    assert api_client.get(f"/api/bulk/{job_id}").status_code == 200
    assert api_client.get(f"/api/bulk/{job_id}/audits").status_code == 200
    assert api_client.get(f"/api/bulk/{job_id}/events/history").status_code == 200
    assert api_client.get(f"/api/bulk/{job_id}/dashboard").status_code == 200
    assert api_client.get(f"/api/bulk/{job_id}/dashboard.json").status_code == 200
    assert api_client.get(f"/api/bulk/{job_id}/events/log.txt").status_code == 200

    # SSE endpoints are covered in remote smoke; TestClient blocks on open streams.
