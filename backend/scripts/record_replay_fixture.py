#!/usr/bin/env python3
"""
Run a real PDF audit (live providers) and write replay fixtures for Shepherd / demo-a.

Usage (from backend/, with .env or env vars for APIs including SERPAPI_API_KEY):

  python scripts/record_replay_fixture.py \\
    --pdf tests/fixtures/sample-pdfs/2108.12837v1.pdf \\
    --set demo-a

Writes under tests/fixtures/replay/<set>/:
  audit.json, events.jsonl, manifest.json
Optional: copies SerpApi transport cassettes when PAPYRUS_MODE=record.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _parse_ts(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def events_to_jsonl(events: list[dict]) -> str:
    if not events:
        return '{"t_rel_ms": 0, "type": "system", "message": "Recorded audit replay"}\n'
    base = _parse_ts(str(events[0].get("ts")))
    lines: list[str] = []
    for event in events:
        rel_ms = 0.0
        if base:
            ts = _parse_ts(str(event.get("ts")))
            if ts:
                rel_ms = max(0.0, (ts - base).total_seconds() * 1000.0)
        row = {k: v for k, v in event.items() if k != "ts"}
        row["t_rel_ms"] = int(rel_ms)
        lines.append(json.dumps(row, default=str))
    return "\n".join(lines) + "\n"


def audit_fixture_payload(audit) -> dict:
    """Shape expected by POST /api/audits/replay/{set} (new audit id on load)."""
    data = audit.model_dump(mode="json", exclude_none=True)
    for key in ("id", "created_at", "completed_at", "events", "paper_text", "bulk_job_id", "source_url"):
        data.pop(key, None)
    data["status"] = "complete"
    return data


async def run_record(pdf_path: Path, out_dir: Path, replay_set: str, record_transport: bool) -> dict:
    work = out_dir.parent / "_record_work" / replay_set
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    os.environ.setdefault("APP_ENV", "development")
    os.environ["AUDIT_DATA_DIR"] = str(work)
    os.environ["PERSISTENCE_BACKEND"] = "json"
    os.environ["USE_CELERY_BACKGROUND"] = "false"
    os.environ["SYNC_RELATIONAL_AUDITS"] = "false"
    os.environ["USE_RELATIONAL_READ"] = "false"
    if record_transport:
        os.environ["PAPYRUS_MODE"] = "record"
        os.environ["REPLAY_SET"] = replay_set
    else:
        os.environ["PAPYRUS_MODE"] = "live"

    from app.config import get_settings

    get_settings.cache_clear()

    from app.domain.models import AuditRun
    from app.pipeline.orchestrator import audit_orchestrator
    from app.services.events import event_bus
    from app.services.serpapi.ledger import serpapi_ledger
    from app.store import audit_store

    audit = AuditRun(paper_title=pdf_path.stem)
    audit_store.create(audit)
    audit_id = audit.id

    await audit_orchestrator.run(audit_id, pdf_path)
    audit = audit_store.get(audit_id)
    if not audit or audit.status != "complete":
        raise RuntimeError(f"Audit did not complete: {getattr(audit, 'status', 'missing')}")

    events = event_bus.history(audit_id)
    serp_calls = serpapi_ledger.list_for_audit(str(audit_id))
    credits = sum(int(c.get("credits") or 0) for c in serp_calls)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "audit.json").write_text(
        json.dumps(audit_fixture_payload(audit), indent=2),
        encoding="utf-8",
    )
    (out_dir / "events.jsonl").write_text(events_to_jsonl(events), encoding="utf-8")
    manifest = {
        "replay_set": replay_set,
        "source_pdf": pdf_path.name,
        "credits_spent": credits,
        "citation_count": len(audit.citations),
        "serpapi_calls": len(serp_calls),
        "recorded_at": datetime.utcnow().isoformat() + "Z",
        "recorded_with": {"papyrus": audit.pipeline_version, "mode": os.environ.get("PAPYRUS_MODE")},
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    raw_dir = work / "fixtures" / "_raw" / replay_set
    if raw_dir.exists():
        for src in raw_dir.glob("*.json"):
            shutil.copy2(src, out_dir / src.name)

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Record replay fixtures from a live PDF audit")
    parser.add_argument(
        "--pdf",
        type=Path,
        default=ROOT / "tests" / "fixtures" / "sample-pdfs" / "2108.12837v1.pdf",
    )
    parser.add_argument("--set", default="demo-a", help="Replay set name (default demo-a)")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output dir (default tests/fixtures/replay/<set>)",
    )
    parser.add_argument(
        "--record-transport",
        action="store_true",
        help="PAPYRUS_MODE=record to cassette SerpApi HTTP responses into the fixture set",
    )
    parser.add_argument(
        "--serpapi-scope",
        choices=("residual", "all", "off"),
        default=None,
        help="Override SERPAPI_SCOPE for recording (use all to capture Scholar witness on more citations)",
    )
    args = parser.parse_args()

    if args.serpapi_scope:
        os.environ["SERPAPI_SCOPE"] = args.serpapi_scope

    if not args.pdf.is_file():
        print(f"PDF not found: {args.pdf}", file=sys.stderr)
        print("Download: https://arxiv.org/pdf/2108.12837v1.pdf", file=sys.stderr)
        return 1

    if not os.environ.get("SERPAPI_API_KEY"):
        print(
            "Warning: SERPAPI_API_KEY not set — Scholar witness will be disabled; re-run with a key "
            "and --serpapi-scope all to bake SerpApi receipts into the fixture.",
            file=sys.stderr,
        )

    out_dir = args.out or (ROOT / "tests" / "fixtures" / "replay" / args.set)
    manifest = asyncio.run(run_record(args.pdf, out_dir, args.set, args.record_transport))
    print(json.dumps({"ok": True, "out_dir": str(out_dir), **manifest}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
