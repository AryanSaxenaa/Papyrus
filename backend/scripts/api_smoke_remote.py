"""Smoke-test public API routes against a running deployment (replay + optional live)."""
from __future__ import annotations

import argparse
import io
import os
import sys
import time
import zipfile
from uuid import UUID

import httpx

BASE_DEFAULT = "https://papyrus-production-70fb.up.railway.app"
MINIMAL_PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=os.environ.get("PAPYRUS_BASE_URL", BASE_DEFAULT))
    parser.add_argument("--replay-set", default="demo-a")
    parser.add_argument(
        "--access-code",
        default=os.environ.get("LIVE_ACCESS_CODE", ""),
        help="Required for live ingest when PUBLIC_DEMO_MODE is on",
    )
    parser.add_argument(
        "--live-doi",
        action="store_true",
        help="Wait for a real DOI audit to finish (slow; uses SerpApi if enabled)",
    )
    parser.add_argument("--doi", default="10.1038/nature12373")
    parser.add_argument("--live-wait-seconds", type=int, default=300)
    args = parser.parse_args()
    base = args.base.rstrip("/")
    headers_live = {"X-Access-Code": args.access_code} if args.access_code else {}
    results: list[tuple[str, str, int, str]] = []

    def record(method: str, path: str, resp: httpx.Response, note: str = "") -> None:
        ok = "OK" if resp.status_code < 400 else "FAIL"
        snippet = (resp.text or "")[:160].replace("\n", " ")
        results.append((ok, f"{method} {path}", resp.status_code, note or snippet))

    def check_sse(client: httpx.Client, path: str) -> None:
        try:
            with client.stream("GET", path, timeout=3.0) as stream:
                stream.raise_for_status()
                results.append(("OK", f"GET {path} (SSE)", stream.status_code, "connected"))
        except httpx.ReadTimeout:
            results.append(("OK", f"GET {path} (SSE)", 200, "stream open (timeout ok)"))
        except httpx.HTTPError as exc:
            results.append(("FAIL", f"GET {path} (SSE)", 0, str(exc)))

    with httpx.Client(base_url=base, timeout=120.0) as client:
        config = client.get("/api/config").json()
        mode = config.get("mode", "unknown")

        for path in (
            "/api/health",
            "/api/config",
            "/api/health/detailed",
            "/api/audits",
            "/api/audits/summaries",
            "/api/serpapi/budget",
            "/api/admin/rate-limits",
            "/api/admin/corrections",
            "/api/admin/config",
        ):
            record("GET", path, client.get(path))

        record("POST", "/api/serpapi/estimate", client.post("/api/serpapi/estimate", json={"num_citations": 3}))

        r = client.post(f"/api/audits/replay/{args.replay_set}")
        if r.status_code not in (200, 202):
            record("POST", f"/api/audits/replay/{args.replay_set}", r)
            print_report(results)
            return 1
        record("POST", f"/api/audits/replay/{args.replay_set}", r)
        audit_id = r.json()["id"]
        UUID(audit_id)

        audit = wait_audit(client, audit_id, 90)
        record("GET", f"/api/audits/{audit_id}", client.get(f"/api/audits/{audit_id}"), f"status={audit.get('status')}")

        cid = audit.get("citations", [{}])[0].get("id") if audit.get("citations") else None

        for path in (
            f"/api/audits/{audit_id}/events/history",
            f"/api/audits/{audit_id}/events/log.txt",
            f"/api/audits/{audit_id}/report.json",
            f"/api/audits/{audit_id}/report.txt",
            f"/api/audits/{audit_id}/report.pdf",
            f"/api/audits/{audit_id}/serpapi",
            f"/api/audits/{audit_id}/bundle",
            f"/api/audits/{audit_id}/bundle.zip",
        ):
            record("GET", path, client.get(path))

        check_sse(client, f"/api/audits/{audit_id}/events")

        if cid:
            record("GET", "citation/attempts", client.get(f"/api/audits/{audit_id}/citations/{cid}/attempts"))
            record(
                "PATCH",
                "citation/intent",
                client.patch(
                    f"/api/audits/{audit_id}/citations/{cid}/intent",
                    json={"intent": "background"},
                ),
            )
            record(
                "PATCH",
                "citation/claim",
                client.patch(
                    f"/api/audits/{audit_id}/citations/{cid}/claim",
                    json={"claim": "Remote smoke claim."},
                ),
            )
            record("POST", "citation/approve-claim", client.post(f"/api/audits/{audit_id}/citations/{cid}/approve-claim"))
            record("POST", "citation/rerun-nli", client.post(f"/api/audits/{audit_id}/citations/{cid}/rerun-nli"))
            record("POST", "citation/rerun", client.post(f"/api/audits/{audit_id}/citations/{cid}/rerun"))

        record("GET", "/api/admin/corrections/export.csv", client.get("/api/admin/corrections/export.csv"))

        if mode == "live":
            record(
                "POST",
                "/api/audits/doi (no code)",
                client.post("/api/audits/doi", json={"doi": args.doi}),
            )
            if args.access_code:
                doi_live = client.post("/api/audits/doi", json={"doi": args.doi}, headers=headers_live)
                record("POST", "/api/audits/doi (live)", doi_live)
                if args.live_doi and doi_live.status_code == 202:
                    live_id = doi_live.json()["id"]
                    live_audit = wait_audit(client, live_id, args.live_wait_seconds)
                    record(
                        "GET",
                        f"/api/audits/{live_id} (live doi)",
                        client.get(f"/api/audits/{live_id}"),
                        f"status={live_audit.get('status')}",
                    )
                    serp = client.get(f"/api/audits/{live_id}/serpapi").json()
                    calls = len(serp.get("calls") or [])
                    results.append(
                        (
                            "OK" if live_audit.get("status") == "complete" else "FAIL",
                            "live SerpApi ledger",
                            calls,
                            f"calls={calls} mode={mode}",
                        )
                    )

                record(
                    "POST",
                    "/api/audits/url (live)",
                    client.post(
                        "/api/audits/url",
                        json={"url": "https://arxiv.org/abs/2301.00001"},
                        headers=headers_live,
                    ),
                )
                record(
                    "POST",
                    "/api/audits/pdf (live)",
                    client.post(
                        "/api/audits",
                        headers=headers_live,
                        files={"file": ("smoke.pdf", MINIMAL_PDF, "application/pdf")},
                    ),
                )

                buffer = io.BytesIO()
                with zipfile.ZipFile(buffer, "w") as archive:
                    archive.writestr("smoke.pdf", MINIMAL_PDF)
                bulk = client.post(
                    "/api/audits/bulk",
                    headers=headers_live,
                    files={"file": ("bulk.zip", buffer.getvalue(), "application/zip")},
                )
                record("POST", "/api/audits/bulk", bulk)
                if bulk.status_code == 202:
                    job_id = bulk.json()["id"]
                    for path in (
                        f"/api/bulk/{job_id}",
                        f"/api/bulk/{job_id}/audits",
                        f"/api/bulk/{job_id}/events/history",
                        f"/api/bulk/{job_id}/dashboard",
                        f"/api/bulk/{job_id}/dashboard.json",
                        f"/api/bulk/{job_id}/events/log.txt",
                    ):
                        record("GET", path, client.get(path))
                    check_sse(client, f"/api/bulk/{job_id}/events")
        else:
            record("POST", "/api/audits/doi", client.post("/api/audits/doi", json={"doi": args.doi}))

        delete_id = audit_id
        record("DELETE", f"/api/audits/{delete_id}", client.delete(f"/api/audits/{delete_id}"))
        gone = client.get(f"/api/audits/{delete_id}")
        results.append(
            ("OK" if gone.status_code == 404 else "FAIL", f"GET /api/audits/{delete_id} after delete", gone.status_code, "")
        )

    print_report(results)
    fails = [x for x in results if x[0] == "FAIL"]
    return 1 if fails else 0


def wait_audit(client: httpx.Client, audit_id: str, timeout_s: int) -> dict:
    deadline = time.time() + timeout_s
    last: dict = {}
    while time.time() < deadline:
        response = client.get(f"/api/audits/{audit_id}")
        if response.status_code == 200:
            last = response.json()
            if last.get("status") in ("complete", "failed"):
                return last
        time.sleep(1.5)
    return last


def print_report(results: list[tuple[str, str, int, str]]) -> None:
    print(f"\n{'='*72}")
    print(f"API smoke: {len(results)} checks")
    print(f"{'='*72}")
    for ok, label, code, note in results:
        print(f"  [{ok:4}] {code:3} {label}")
        if note and ok == "FAIL":
            print(f"         {note}")
    fails = sum(1 for r in results if r[0] == "FAIL")
    print(f"\nFailed: {fails}")


if __name__ == "__main__":
    sys.exit(main())
