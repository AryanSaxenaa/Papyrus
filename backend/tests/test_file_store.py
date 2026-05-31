from pathlib import Path

from app.storage.files import LocalFileStore, upload_key


def test_local_file_store_roundtrip(tmp_path: Path) -> None:
    store = LocalFileStore(tmp_path)
    key = upload_key("abc-123")
    store.write_bytes(key, b"%PDF-1.4")
    assert store.exists(key)
    assert store.read_bytes(key) == b"%PDF-1.4"
    with store.local_path(key) as path:
        assert path.read_bytes() == b"%PDF-1.4"
    store.delete(key)
    assert not store.exists(key)
