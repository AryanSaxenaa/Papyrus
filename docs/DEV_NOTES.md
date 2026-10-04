# Developer notes (VERIFY register)

Answers recorded while implementing the SerpApi hackathon pack.

| ID | Answer |
|---|---|
| V1 | Head at implementation start: `f4909d4` — tagged `pre-hackathon-baseline`. |
| V2 | No `LICENSE` file at repo root (VERIFY before submission; add only with owner decision). |
| V3 | Private `Papyrus-1` not inspected; do not copy without licence/secrets review. |
| V10 | `get_engine()` returns `None` when `PERSISTENCE_BACKEND=json`; relational sync skipped — covered by `test_lite_mode.py`. |
| V17 | Redis failure at startup logs and continues; cache/rate limits use in-memory fallback; events still emit in-process + DB when postgres available. |
| V18 | ASGI: `app.main:app`. Celery: `app.worker.celery_app`, queue `audits-{APP_ENV}` via `settings.audit_queue_name()`. |

Open items: V4–V9, V11–V16 (see spec pack §6).
