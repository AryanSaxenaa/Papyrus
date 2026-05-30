import csv
import io

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.services.corrections import correction_store
from app.services.rate_limits import rate_limit_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/rate-limits")
async def get_rate_limits() -> dict:
    snapshot = await rate_limit_service.snapshot()
    return {"sources": snapshot, "meta": await rate_limit_service.meta()}


@router.get("/corrections")
async def list_corrections(limit: int = 50) -> dict:
    rows = correction_store.list_recent(limit=min(limit, 200))
    return {"corrections": rows, "count": len(rows)}


@router.get("/corrections/export.csv")
async def export_corrections_csv(limit: int = 500) -> StreamingResponse:
    rows = correction_store.list_recent(limit=min(limit, 2000))
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "id",
            "audit_id",
            "citation_id",
            "citation_index",
            "field",
            "original_value",
            "corrected_value",
            "created_at",
        ],
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=papyrus-corrections.csv"},
    )


@router.get("/config")
async def get_public_config() -> dict:
    settings = get_settings()
    return {
        "pipeline_version": settings.pipeline_version,
        "persistence_backend": settings.persistence_backend,
        "grobid_enabled": settings.grobid_enabled,
        "integrations": {
            "deepseek": bool(settings.deepseek_api_key),
            "openai_embeddings": bool(settings.openai_api_key),
            "huggingface_nli": bool(settings.huggingface_api_key),
            "nli_backend": settings.nli_backend,
            "ollama_nli": bool(settings.ollama_base_url),
            "local_nli": settings.nli_backend in {"auto", "local"},
            "exa": bool(settings.exa_api_key),
            "firecrawl": bool(settings.firecrawl_api_key),
            "apify": bool(settings.apify_api_token),
            "semantic_scholar": bool(settings.semantic_scholar_api_key),
            "embeddings_backend": settings.embeddings_backend,
            "nli_requires_claim_approval": settings.nli_requires_claim_approval,
        },
    }
