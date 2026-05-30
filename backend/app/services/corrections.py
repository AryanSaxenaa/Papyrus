from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import CitationCorrectionRecord
from app.db.session import get_engine


class CorrectionStore:
    def _jsonl_path(self) -> Path:
        path = Path(get_settings().audit_data_dir) / "corrections.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def record(
        self,
        audit_id: str,
        citation_id: str,
        citation_index: int,
        field: str,
        original_value: str | None,
        corrected_value: str,
    ) -> None:
        entry = {
            "id": str(uuid4()),
            "audit_id": audit_id,
            "citation_id": citation_id,
            "citation_index": citation_index,
            "field": field,
            "original_value": original_value,
            "corrected_value": corrected_value,
        }
        engine = get_engine()
        if engine is None:
            with self._jsonl_path().open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry) + "\n")
            return
        row = CitationCorrectionRecord(
            id=str(uuid4()),
            audit_id=audit_id,
            citation_id=citation_id,
            citation_index=citation_index,
            field=field,
            original_value=original_value,
            corrected_value=corrected_value,
        )
        with Session(engine) as session:
            session.add(row)
            session.commit()

    def list_recent(self, limit: int = 50) -> list[dict]:
        engine = get_engine()
        if engine is None:
            path = self._jsonl_path()
            if not path.exists():
                return []
            lines = path.read_text(encoding="utf-8").strip().splitlines()
            rows = [json.loads(line) for line in lines[-limit:]]
            return list(reversed(rows))
        with Session(engine) as session:
            rows = session.scalars(
                select(CitationCorrectionRecord).order_by(CitationCorrectionRecord.created_at.desc()).limit(limit)
            ).all()
            return [
                {
                    "id": row.id,
                    "audit_id": row.audit_id,
                    "citation_id": row.citation_id,
                    "citation_index": row.citation_index,
                    "field": row.field,
                    "original_value": row.original_value,
                    "corrected_value": row.corrected_value,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in rows
            ]


correction_store = CorrectionStore()
