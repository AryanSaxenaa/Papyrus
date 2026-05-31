#!/usr/bin/env bash
# Deploy Papyrus to Cloud Run (API + worker + web). Requires gcloud, deploy/cloudrun/.env.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

ENV_FILE="deploy/cloudrun/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "Create $ENV_FILE from deploy/cloudrun/env.template" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

export GCP_REGION="${GCP_REGION:-us-central1}"
: "${GCP_PROJECT_ID:?GCP_PROJECT_ID required}"
: "${GCS_BUCKET:?GCS_BUCKET required}"
: "${DATABASE_URL:?DATABASE_URL required}"
: "${REDIS_URL:?REDIS_URL required}"

if [[ "${INIT_DB:-0}" == "1" ]]; then
  echo "Running init_db..."
  (cd backend && DATABASE_URL="$DATABASE_URL" PERSISTENCE_BACKEND="${PERSISTENCE_BACKEND:-postgres}" python scripts/init_db.py)
fi

gcloud config set project "$GCP_PROJECT_ID" >/dev/null

API_IMAGE="gcr.io/${GCP_PROJECT_ID}/papyrus-api"
WEB_IMAGE="gcr.io/${GCP_PROJECT_ID}/papyrus-web"

gcloud services enable run.googleapis.com artifactregistry.googleapis.com storage.googleapis.com cloudbuild.googleapis.com --quiet

if ! gsutil ls -b "gs://${GCS_BUCKET}" >/dev/null 2>&1; then
  gsutil mb -l "$GCP_REGION" "gs://${GCS_BUCKET}"
fi

PROJECT_NUMBER="$(gcloud projects describe "$GCP_PROJECT_ID" --format='value(projectNumber)')"
RUN_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
gsutil iam ch "serviceAccount:${RUN_SA}:roles/storage.objectAdmin" "gs://${GCS_BUCKET}" 2>/dev/null || true

ENV_YAML="$(mktemp)"
trap 'rm -f "$ENV_YAML"' EXIT

{
  echo "---"
  printf 'APP_ENV: "%s"\n' "production"
  printf 'PERSISTENCE_BACKEND: "%s"\n' "${PERSISTENCE_BACKEND:-postgres}"
  printf 'FILE_STORAGE_BACKEND: "%s"\n' "gcs"
  printf 'GCS_BUCKET: "%s"\n' "$GCS_BUCKET"
  printf 'USE_CELERY_BACKGROUND: "%s"\n' "${USE_CELERY_BACKGROUND:-true}"
  printf 'USE_CELERY_BULK: "%s"\n' "${USE_CELERY_BULK:-true}"
  printf 'GROBID_ENABLED: "%s"\n' "false"
  printf 'ENABLE_LLM_PDF_INGESTION: "%s"\n' "false"
  printf 'DATABASE_URL: "%s"\n' "$DATABASE_URL"
  printf 'REDIS_URL: "%s"\n' "$REDIS_URL"
  printf 'CORS_ORIGINS: "%s"\n' "${CORS_ORIGINS:-}"
  printf 'CROSSREF_MAILTO: "%s"\n' "${CROSSREF_MAILTO:-}"
  printf 'OPENALEX_MAILTO: "%s"\n' "${OPENALEX_MAILTO:-}"
  printf 'UNPAYWALL_EMAIL: "%s"\n' "${UNPAYWALL_EMAIL:-}"
  printf 'LLM_BACKEND: "%s"\n' "${LLM_BACKEND:-deepseek}"
  printf 'NLI_BACKEND: "%s"\n' "${NLI_BACKEND:-hf}"
  printf 'EMBEDDINGS_BACKEND: "%s"\n' "${EMBEDDINGS_BACKEND:-snowflake}"
  printf 'AUDIT_DATA_DIR: "%s"\n' "${AUDIT_DATA_DIR:-/tmp/papyrus-data}"
} >"$ENV_YAML"

append_if_set() {
  local key="$1"
  local val="${!key:-}"
  if [[ -n "$val" ]]; then
    printf '%s: "%s"\n' "$key" "$val" >>"$ENV_YAML"
  fi
}

for key in GCS_PREFIX ENABLE_DEEPSEEK DEEPSEEK_API_KEY DEEPSEEK_MODEL DEEPSEEK_BASE_URL \
  OPENROUTER_API_KEY OPENROUTER_MODEL OPENROUTER_FALLBACK_MODEL OPENROUTER_BASE_URL \
  HUGGINGFACE_API_KEY OPENAI_API_KEY SEMANTIC_SCHOLAR_API_KEY EXA_API_KEY FIRECRAWL_API_KEY \
  APIFY_API_TOKEN SYNC_RELATIONAL_AUDITS USE_RELATIONAL_READ NLI_REQUIRES_CLAIM_APPROVAL \
  SNOWFLAKE_EMBEDDING_MODEL MAX_UPLOAD_MB; do
  append_if_set "$key"
done

echo "Building API image..."
gcloud builds submit ./backend --tag "$API_IMAGE" --quiet

echo "Deploying API..."
gcloud run deploy papyrus-api \
  --image "$API_IMAGE" \
  --region "$GCP_REGION" \
  --platform managed \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --min-instances 0 \
  --max-instances 4 \
  --port 8080 \
  --allow-unauthenticated \
  --env-vars-file "$ENV_YAML" \
  --quiet

echo "Deploying worker..."
gcloud run deploy papyrus-worker \
  --image "$API_IMAGE" \
  --region "$GCP_REGION" \
  --platform managed \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --min-instances 1 \
  --max-instances 2 \
  --port 8080 \
  --no-allow-unauthenticated \
  --command "/bin/sh" \
  --args "scripts/cloudrun_worker.sh" \
  --env-vars-file "$ENV_YAML" \
  --quiet

API_URL="$(gcloud run services describe papyrus-api --region "$GCP_REGION" --format='value(status.url)')"
echo "API URL: $API_URL"

if [[ "${SKIP_WEB:-0}" != "1" ]]; then
  gcloud builds submit . --config=deploy/cloudrun/cloudbuild-web.yaml \
    --substitutions="_IMAGE=${WEB_IMAGE},_API_URL=${API_URL}" --quiet

  gcloud run deploy papyrus-web \
    --image "$WEB_IMAGE" \
    --region "$GCP_REGION" \
    --platform managed \
    --memory 512Mi \
    --port 8080 \
    --allow-unauthenticated \
    --quiet

  WEB_URL="$(gcloud run services describe papyrus-web --region "$GCP_REGION" --format='value(status.url)')"
  echo "Web URL: $WEB_URL"
fi

echo "Health: ${API_URL}/api/health/detailed"
