#!/usr/bin/env python3
"""Create SQLAlchemy tables (run once per environment before Cloud Run deploy)."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.db.session import init_db  # noqa: E402


def main() -> None:
    init_db()
    print("Database schema initialized.")


if __name__ == "__main__":
    main()
