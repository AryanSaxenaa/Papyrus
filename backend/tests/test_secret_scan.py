import subprocess
import sys
from pathlib import Path


def test_secret_scan_passes_repo():
    script = Path(__file__).resolve().parents[1] / "scripts" / "secret_scan.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def test_secret_scan_fails_on_bad_file(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts" / "secret_scan.py"
    bad = tmp_path / "bad.txt"
    bad.write_text("https://serpapi.com/search?api_key=supersecretvalue123456", encoding="utf-8")
    result = subprocess.run([sys.executable, str(script), str(bad)], capture_output=True, text=True, check=False)
    assert result.returncode == 1
