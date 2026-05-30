from fastapi import APIRouter

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
            "exa": bool(settings.exa_api_key),
            "firecrawl": bool(settings.firecrawl_api_key),
            "apify": bool(settings.apify_api_token),
            "semantic_scholar": bool(settings.semantic_scholar_api_key),
        },
    }
