#!/usr/bin/env python3
"""One live SerpApi Scholar call (reads SERPAPI_API_KEY from env). Never log the key."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


async def main() -> int:
    if not os.environ.get("SERPAPI_API_KEY"):
        print("Set SERPAPI_API_KEY in the environment", file=sys.stderr)
        return 1
    from app.services.serpapi.client import SerpApiClient

    client = SerpApiClient()
    body, receipt = await client.search(
        "google_scholar",
        {"q": "Attention is all you need"},
        audit_id="smoke",
    )
    print(json.dumps({"results": len(body.get("organic_results") or []), "receipt": receipt.model_dump(mode="json")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
