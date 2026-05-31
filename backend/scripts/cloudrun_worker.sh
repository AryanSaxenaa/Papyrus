#!/bin/sh
# Cloud Run requires a listener on $PORT; Celery has no HTTP server.
PORT="${PORT:-8080}"
python -m http.server "$PORT" &
exec celery -A app.worker.celery_app worker -l info -Q audits --concurrency=1
