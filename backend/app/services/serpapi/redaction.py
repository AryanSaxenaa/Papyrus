from __future__ import annotations

import hashlib
import json
import re
from typing import Any
from urllib.parse import urlencode

_REDACT_KEYS = frozenset({"api_key", "apikey", "authorization"})


def redact_params(params: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in params.items():
        if key.lower() in _REDACT_KEYS:
            out[key] = "[REDACTED]"
        elif isinstance(value, dict):
            out[key] = redact_params(value)
        else:
            out[key] = value
    return out


def redact_url(url: str) -> str:
    return re.sub(r"([?&]api_key=)[^&]+", r"\1[REDACTED]", url, flags=re.I)


def cache_key(engine: str, params: dict[str, Any]) -> str:
    canonical = json.dumps({"engine": engine, "params": redact_params(params)}, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_serpapi_url(engine: str, params: dict[str, Any], api_key: str) -> str:
    query = {"engine": engine, **params, "api_key": api_key}
    return f"https://serpapi.com/search.json?{urlencode(query)}"
