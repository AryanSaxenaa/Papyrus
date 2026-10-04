from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import get_settings
from app.services.serpapi.budget import serpapi_budget
from app.services.serpapi.ledger import serpapi_ledger
from app.store import audit_store

router = APIRouter(tags=["evidence"])


class EstimateBody(BaseModel):
    num_citations: int = 1


@router.get("/serpapi/budget")
async def serpapi_budget_status() -> dict:
    settings = get_settings()
    spent = serpapi_ledger.total_credits()
    return {
        "enabled": settings.serpapi_active(),
        "mode": settings.papyrus_mode,
        "monthly_spent": spent,
        "monthly_cap": settings.serpapi_monthly_hard_cap,
        "per_audit_cap": settings.serpapi_max_credits_per_audit,
        "remaining": max(0, settings.serpapi_monthly_hard_cap - spent),
    }


@router.post("/serpapi/estimate")
async def serpapi_estimate(body: EstimateBody) -> dict:
    calls = max(1, body.num_citations) * 2
    return serpapi_budget.preview(calls)


@router.get("/audits/{audit_id}/serpapi")
async def audit_serpapi_calls(audit_id: str) -> dict:
    try:
        uid = UUID(audit_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid audit id") from exc
    audit = audit_store.get(uid)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    return {"audit_id": audit_id, "calls": serpapi_ledger.list_for_audit(audit_id)}


@router.get("/audits/{audit_id}/bundle")
async def audit_evidence_bundle(audit_id: str) -> dict:
    try:
        uid = UUID(audit_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid audit id") from exc
    audit = audit_store.get(uid)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    return {
        "schema": "papyrus.evidence/1",
        "audit_id": audit_id,
        "paper_title": audit.paper_title,
        "pipeline_version": audit.pipeline_version,
        "mode": get_settings().papyrus_mode,
        "serpapi_calls": serpapi_ledger.list_for_audit(audit_id),
        "citations": [c.model_dump(mode="json") for c in audit.citations],
    }
