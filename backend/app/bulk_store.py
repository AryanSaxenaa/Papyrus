from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import BulkJobRecord
from app.db.session import get_engine
from app.domain.models import BulkAuditJob


class BulkJobStore:
    def __init__(self) -> None:
        self._jobs: dict[UUID, BulkAuditJob] = {}

    def _path(self, job_id: UUID) -> Path:
        settings = get_settings()
        directory = Path(settings.audit_data_dir) / "bulk"
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{job_id}.json"

    def _use_postgres(self) -> bool:
        return get_settings().persistence_backend in {"postgres", "both"}

    def _use_json(self) -> bool:
        return get_settings().persistence_backend in {"json", "both"}

    def create(self, job: BulkAuditJob) -> BulkAuditJob:
        self._jobs[job.id] = job
        self.save(job)
        return job

    def get(self, job_id: UUID) -> BulkAuditJob | None:
        if job_id in self._jobs:
            return self._jobs[job_id]

        if self._use_postgres():
            engine = get_engine()
            if engine is not None:
                with Session(engine) as session:
                    row = session.get(BulkJobRecord, str(job_id))
                    if row:
                        job = BulkAuditJob.model_validate_json(row.payload)
                        self._jobs[job_id] = job
                        return job

        if self._use_json():
            path = self._path(job_id)
            if path.exists():
                job = BulkAuditJob.model_validate_json(path.read_text(encoding="utf-8"))
                self._jobs[job_id] = job
                return job
        return None

    def save(self, job: BulkAuditJob) -> None:
        self._jobs[job.id] = job
        payload = json.dumps(job.model_dump(mode="json"), indent=2)
        if self._use_json():
            self._path(job.id).write_text(payload, encoding="utf-8")
        if self._use_postgres():
            engine = get_engine()
            if engine is None:
                return
            with Session(engine) as session:
                row = session.get(BulkJobRecord, str(job.id))
                if row is None:
                    row = BulkJobRecord(id=str(job.id), payload=payload)
                    session.add(row)
                else:
                    row.payload = payload
                session.commit()


bulk_job_store = BulkJobStore()
