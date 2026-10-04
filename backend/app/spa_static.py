from __future__ import annotations

from pathlib import Path

from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles


class SPAStaticFiles(StaticFiles):
    """Serve static assets and fall back to index.html for client-side routes."""

    async def get_response(self, path: str, scope):  # type: ignore[override]
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code != 404:
                raise
            if path.startswith("api/") or path.startswith("assets/"):
                raise
            return await super().get_response("index.html", scope)


def mount_spa(app, static_dir: Path) -> None:
    if not static_dir.is_dir():
        return
    app.mount("/", SPAStaticFiles(directory=str(static_dir), html=True), name="spa")
