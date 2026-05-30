from fastapi import APIRouter

from app.config import get_settings
from app.services.citations_index import failure_rate_by_audit, reindex_all_audits
from app.services.corrections import correction_store
from app.services.rate_limits import rate_limit_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/rate-limits")
async def get_rate_limits() -> dict:
    snapshot = await rate_limit_service.snapshot()
    return {"sources": snapshot, "meta": await rate_limit_service.meta()}


@router.get("/citations/stats")
async def citation_stats() -> dict:
    ranked = failure_rate_by_audit(limit=25)
    return {"audits_by_failure_rate": ranked}


@router.post("/citations/reindex")
async def reindex_citations() -> dict:
    return reindex_all_audits()


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
            "nli_backend": settings.nli_backend,
            "ollama_nli": bool(settings.ollama_base_url),
            "local_nli": settings.nli_backend in {"auto", "local"},
            "exa": bool(settings.exa_api_key),
            "firecrawl": bool(settings.firecrawl_api_key),
            "apify": bool(settings.apify_api_token),
            "semantic_scholar": bool(settings.semantic_scholar_api_key),
        },
    }
