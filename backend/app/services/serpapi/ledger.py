from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import SerpApiCallRow
from app.db.session import get_engine
from app.services.serpapi.redaction import redact_params


class SerpApiLedger:
    def append(
        self,
        *,
        audit_id: str | None,
        citation_id: str | None,
        engine: str,
        params: dict[str, Any],
        search_metadata_id: str | None,
        json_endpoint: str | None,
        http_status: int,
        credits: int,
        cache_hit: bool,
        latency_ms: int,
        raw_key: str,
        sha256_raw: str,
    ) -> str:
        call_id = str(uuid4())
        row = {
            "id": call_id,
            "audit_id": audit_id,
            "citation_id": citation_id,
            "engine": engine,
            "params": redact_params(params),
            "search_metadata_id": search_metadata_id,
            "json_endpoint": json_endpoint,
            "http_status": http_status,
            "credits": credits,
            "cache_hit": cache_hit,
            "latency_ms": latency_ms,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "raw_key": raw_key,
            "sha256_raw": sha256_raw,
        }
        engine_obj = get_engine()
        if engine_obj is not None:
            with Session(engine_obj) as session:
                session.add(
                    SerpApiCallRow(
                        id=call_id,
                        audit_id=audit_id,
                        citation_id=citation_id,
                        engine=engine,
                        params_json=json.dumps(redact_params(params)),
                        search_metadata_id=search_metadata_id,
                        json_endpoint=json_endpoint,
                        http_status=http_status,
                        credits=credits,
                        cache_hit=cache_hit,
                        latency_ms=latency_ms,
                        raw_key=raw_key,
                        sha256_raw=sha256_raw,
                    )
                )
                session.commit()
        else:
            path = Path(get_settings().audit_data_dir) / "serpapi_ledger.jsonl"
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row) + "\n")
        return call_id

    def total_credits(self) -> int:
        engine_obj = get_engine()
        if engine_obj is not None:
            with Session(engine_obj) as session:
                rows = session.query(SerpApiCallRow).all()
                return sum(r.credits for r in rows)
        path = Path(get_settings().audit_data_dir) / "serpapi_ledger.jsonl"
        if not path.exists():
            return 0
        total = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                total += int(json.loads(line).get("credits", 0))
        return total

    def list_for_audit(self, audit_id: str) -> list[dict[str, Any]]:
        engine_obj = get_engine()
        if engine_obj is not None:
            with Session(engine_obj) as session:
                rows = (
                    session.query(SerpApiCallRow)
                    .filter(SerpApiCallRow.audit_id == audit_id)
                    .order_by(SerpApiCallRow.created_at)
                    .all()
                )
                return [self._row_to_dict(r) for r in rows]
        path = Path(get_settings().audit_data_dir) / "serpapi_ledger.jsonl"
        if not path.exists():
            return []
        out: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("audit_id") == audit_id:
                out.append(row)
        return out

    @staticmethod
    def _row_to_dict(row: SerpApiCallRow) -> dict[str, Any]:
        return {
            "id": row.id,
            "audit_id": row.audit_id,
            "citation_id": row.citation_id,
            "engine": row.engine,
            "params": json.loads(row.params_json),
            "search_metadata_id": row.search_metadata_id,
            "json_endpoint": row.json_endpoint,
            "http_status": row.http_status,
            "credits": row.credits,
            "cache_hit": row.cache_hit,
            "latency_ms": row.latency_ms,
            "raw_key": row.raw_key,
            "sha256_raw": row.sha256_raw,
        }


serpapi_ledger = SerpApiLedger()
