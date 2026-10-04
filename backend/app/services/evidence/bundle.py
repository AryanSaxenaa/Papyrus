from __future__ import annotations

import hashlib
import io
import json
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.domain.models import AuditRun
from app.services.serpapi.ledger import serpapi_ledger

VERIFY_PY = '''#!/usr/bin/env python3
"""Offline verifier for papyrus.evidence/1 bundles (stdlib only)."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    root = Path(__file__).resolve().parent
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        print("FAIL: manifest.json missing")
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != "papyrus.evidence/1":
        print("FAIL: unsupported schema")
        return 1
    for entry in manifest.get("files", []):
        rel = entry["path"]
        expected = entry["sha256"]
        path = root / rel
        if not path.is_file():
            print(f"FAIL: missing {rel}")
            return 1
        actual = sha256_file(path)
        if actual != expected:
            print(f"FAIL: hash mismatch for {rel}")
            return 1
    text = (root / "verdicts.json").read_text(encoding="utf-8")
    if "api_key" in text.lower():
        print("FAIL: api_key found in bundle text")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

README_TXT = """Papyrus evidence bundle (papyrus.evidence/1)

Run offline verification:
  python verify.py

SerpApi search archives are retained for about 31 days from each call's created_at.
After that, use the hashed raw JSON in serpapi/ and ledger.jsonl in this bundle.
"""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_evidence_zip(audit: AuditRun) -> bytes:
    settings = get_settings()
    audit_id = str(audit.id)
    calls = serpapi_ledger.list_for_audit(audit_id)
    credits_spent = sum(int(c.get("credits", 0)) for c in calls)

    verdicts = {
        "audit_id": audit_id,
        "paper_title": audit.paper_title,
        "pipeline_version": audit.pipeline_version,
        "citations": [c.model_dump(mode="json") for c in audit.citations],
    }
    verdicts_bytes = json.dumps(verdicts, indent=2).encode("utf-8")

    files_meta: list[dict[str, Any]] = []
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        def add(name: str, data: bytes) -> None:
            zf.writestr(name, data)
            files_meta.append({"path": name, "sha256": _sha256_bytes(data)})

        add("verdicts.json", verdicts_bytes)
        ledger_lines = "\n".join(json.dumps(c) for c in calls)
        if ledger_lines:
            add("serpapi/ledger.jsonl", (ledger_lines + "\n").encode("utf-8"))
        for idx, call in enumerate(calls):
            call_id = call.get("id") or f"call-{idx}"
            add(f"serpapi/{call_id}.json", json.dumps(call, indent=2).encode("utf-8"))
        add("verify.py", VERIFY_PY.encode("utf-8"))
        add("README.txt", README_TXT.encode("utf-8"))

        manifest = {
            "schema": "papyrus.evidence/1",
            "audit_id": audit_id,
            "paper_title": audit.paper_title,
            "pipeline_version": audit.pipeline_version,
            "mode": settings.papyrus_mode,
            "credits_spent": credits_spent,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "files": files_meta,
        }
        add("manifest.json", json.dumps(manifest, indent=2).encode("utf-8"))

    return buffer.getvalue()


def verify_zip_bytes(data: bytes) -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "bundle.zip"
        path.write_bytes(data)
        with zipfile.ZipFile(path) as archive:
            archive.extractall(tmp)
        verify_script = Path(tmp) / "verify.py"
        result = subprocess.run(
            [sys.executable, str(verify_script)],
            cwd=tmp,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
