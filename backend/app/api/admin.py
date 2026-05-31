import csv
import io

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.services.bulk_dispatch import celery_worker_available
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
    celery_ready = await celery_worker_available()
    return {
        "pipeline_version": settings.pipeline_version,
        "persistence_backend": settings.persistence_backend,
        "grobid_enabled": settings.grobid_enabled,
        "enable_llm_pdf_ingestion": settings.enable_llm_pdf_ingestion,
        "use_celery_background": settings.celery_background_enabled(),
        "file_storage_backend": settings.file_storage_backend,
        "background_queue_mode": "celery" if celery_ready else "background_tasks",
        "celery_worker_available": celery_ready,
        "integrations": {
            "deepseek": bool(settings.deepseek_api_key),
            "llm_backend": settings.llm_backend,
            "openrouter": bool(settings.openrouter_api_key),
            "openai_embeddings": bool(settings.openai_api_key),
            "huggingface_nli": bool(settings.huggingface_api_key),
            "nli_backend": settings.nli_backend,
            "ollama_nli": bool(settings.ollama_base_url),
            "local_nli": settings.nli_backend in {"auto", "local"},
            "exa": bool(settings.exa_api_key),
            "firecrawl": bool(settings.firecrawl_api_key),
            "apify": bool(settings.apify_api_token),
            "apify_arxiv_secondary": settings.apify_actor_arxiv_secondary,
            "openalex_api_key": bool(settings.openalex_api_key),
            "semantic_scholar": bool(settings.semantic_scholar_api_key),
            "embeddings_backend": settings.embeddings_backend,
            "nli_requires_claim_approval": settings.nli_requires_claim_approval,
        },
    }
