#!/usr/bin/env python3
"""Sanitise recorded transport cassettes into a replay fixture set."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _truncate_snippets(obj: object, max_len: int = 300) -> object:
    if isinstance(obj, dict):
        return {k: _truncate_snippets(v, max_len) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_truncate_snippets(v, max_len) for v in obj]
    if isinstance(obj, str) and len(obj) > max_len:
        return obj[:max_len] + "…"
    return obj


def _redact_secrets(text: str) -> str:
    text = re.sub(r"([?&]api_key=)[^&\s\"']+", r"\1[REDACTED]", text, flags=re.I)
    return text


def sanitise_cassette(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    raw = _redact_secrets(raw)
    payload = json.loads(raw)
    if "url" in payload:
        payload["url"] = _redact_secrets(str(payload["url"]))
    return _truncate_snippets(payload)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--set", required=True, help="Fixture set name, e.g. demo-a")
    parser.add_argument("--audit-data", default=str(ROOT / "data" / "audits"))
    args = parser.parse_args()

    base = Path(args.audit_data)
    raw_dir = base / "fixtures" / "_raw" / args.set
    out_dir = base / "fixtures" / args.set
    out_dir.mkdir(parents=True, exist_ok=True)

    if raw_dir.exists():
        for src in raw_dir.glob("*.json"):
            data = sanitise_cassette(src)
            (out_dir / src.name).write_text(json.dumps(data, indent=2), encoding="utf-8")

    manifest = {
        "replay_set": args.set,
        "credits_spent": 0,
        "recorded_with": {"papyrus": "2.0"},
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote fixtures to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
