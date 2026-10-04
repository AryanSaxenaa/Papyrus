from __future__ import annotations

import hmac

from fastapi import Header, HTTPException

from app.config import get_settings


def require_live_audit_access(
    x_access_code: str | None = Header(default=None, alias="X-Access-Code"),
) -> None:
    """When PUBLIC_DEMO_MODE is on, live audits need X-Access-Code (replay stays open)."""
    settings = get_settings()
    if settings.papyrus_mode == "replay":
        return
    if not settings.public_demo_mode:
        return
    expected = settings.live_access_code
    if not expected:
        raise HTTPException(status_code=503, detail="Live audits are disabled on this instance")
    provided = x_access_code or ""
    if not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=403, detail="Invalid or missing access code")
