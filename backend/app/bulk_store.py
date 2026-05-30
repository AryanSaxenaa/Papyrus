from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from app.config import get_settings
from app.domain.models import BulkAuditJob


class BulkJobStore:
    def __init__(self) -> None:
        self._jobs: dict[UUID, BulkAuditJob] = {}

    def _path(self, job_id: UUID) -> Path:
        settings = get_settings()
        directory = Path(settings.audit_data_dir) / "bulk"
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{job_id}.json"

    def create(self, job: BulkAuditJob) -> BulkAuditJob:
        self._jobs[job.id] = job
        self.save(job)
        return job

    def get(self, job_id: UUID) -> BulkAuditJob | None:
        if job_id in self._jobs:
            return self._jobs[job_id]
        path = self._path(job_id)
        if not path.exists():
            return None
        job = BulkAuditJob.model_validate_json(path.read_text(encoding="utf-8"))
        self._jobs[job_id] = job
        return job

    def save(self, job: BulkAuditJob) -> None:
        self._jobs[job.id] = job
        self._path(job.id).write_text(
            json.dumps(job.model_dump(mode="json"), indent=2),
            encoding="utf-8",
        )


bulk_job_store = BulkJobStore()
