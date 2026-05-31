from __future__ import annotations

import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.config import get_settings


class FileStore:
    """Blob storage for uploads and optional JSON artifacts (local disk or GCS)."""

    def write_bytes(self, key: str, data: bytes) -> None:
        raise NotImplementedError

    def read_bytes(self, key: str) -> bytes:
        raise NotImplementedError

    def exists(self, key: str) -> bool:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError

    @contextmanager
    def local_path(self, key: str) -> Iterator[Path]:
        """Yield a filesystem path suitable for libraries that need open()/Path."""
        raise NotImplementedError


class LocalFileStore(FileStore):
    def __init__(self, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        normalized = key.replace("\\", "/").lstrip("/")
        path = (self._root / normalized).resolve()
        root = self._root.resolve()
        if not str(path).startswith(str(root)):
            raise ValueError("Invalid storage key")
        return path

    def write_bytes(self, key: str, data: bytes) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def read_bytes(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.is_file():
            path.unlink()

    @contextmanager
    def local_path(self, key: str) -> Iterator[Path]:
        path = self._path(key)
        if not path.is_file():
            raise FileNotFoundError(key)
        yield path


class GcsFileStore(FileStore):
    def __init__(self, bucket: str, prefix: str = "papyrus") -> None:
        from google.cloud import storage

        self._client = storage.Client()
        self._bucket = self._client.bucket(bucket)
        self._prefix = prefix.strip("/")

    def _object_name(self, key: str) -> str:
        normalized = key.replace("\\", "/").lstrip("/")
        return f"{self._prefix}/{normalized}" if self._prefix else normalized

    def _blob(self, key: str):
        return self._bucket.blob(self._object_name(key))

    def write_bytes(self, key: str, data: bytes) -> None:
        self._blob(key).upload_from_string(data)

    def read_bytes(self, key: str) -> bytes:
        blob = self._blob(key)
        if not blob.exists():
            raise FileNotFoundError(key)
        return blob.download_as_bytes()

    def exists(self, key: str) -> bool:
        return self._blob(key).exists()

    def delete(self, key: str) -> None:
        blob = self._blob(key)
        if blob.exists():
            blob.delete()

    @contextmanager
    def local_path(self, key: str) -> Iterator[Path]:
        suffix = Path(key).suffix or ".bin"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
            handle.write(self.read_bytes(key))
            temp_path = Path(handle.name)
        try:
            yield temp_path
        finally:
            temp_path.unlink(missing_ok=True)


def upload_key(audit_id: str) -> str:
    return f"uploads/{audit_id}.pdf"


def bulk_zip_key(job_id: str) -> str:
    return f"uploads/bulk/{job_id}.zip"


def audit_json_key(audit_id: str) -> str:
    return f"audits/{audit_id}.json"


def _build_file_store() -> FileStore:
    settings = get_settings()
    if settings.file_storage_backend == "gcs":
        if not settings.gcs_bucket:
            raise ValueError("GCS_BUCKET is required when FILE_STORAGE_BACKEND=gcs")
        return GcsFileStore(settings.gcs_bucket, settings.gcs_prefix)
    root = Path(settings.file_storage_root)
    return LocalFileStore(root)


class _FileStoreProxy:
    def _store(self) -> FileStore:
        return _build_file_store()

    def write_bytes(self, key: str, data: bytes) -> None:
        self._store().write_bytes(key, data)

    def read_bytes(self, key: str) -> bytes:
        return self._store().read_bytes(key)

    def exists(self, key: str) -> bool:
        return self._store().exists(key)

    def delete(self, key: str) -> None:
        self._store().delete(key)

    @contextmanager
    def local_path(self, key: str) -> Iterator[Path]:
        with self._store().local_path(key) as path:
            yield path


file_store = _FileStoreProxy()
