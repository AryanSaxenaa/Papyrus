# Deploy Papyrus to Google Cloud Run (API + worker + static web; no GROBID).
# Prerequisites: gcloud auth login, deploy/cloudrun/.env from env.template, init_db on Postgres.
#
# Usage (from repo root):
#   .\deploy\cloudrun\deploy.ps1
# Optional: set SKIP_WEB=1 to redeploy API/worker only; INIT_DB=1 to run migrations locally first.

$ErrorActionPreference = "Continue"
function Fail([string]$msg) { throw $msg }
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $Root

$EnvFile = Join-Path $PSScriptRoot ".env"
if (-not (Test-Path $EnvFile)) {
    Fail "Create deploy/cloudrun/.env from deploy/cloudrun/env.template"
}

Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        Set-Variable -Name $matches[1].Trim() -Value $matches[2].Trim() -Scope Script
    }
}

function Get-DeployVar([string]$Name) {
    if (Test-Path "variable:$Name") {
        return (Get-Item "variable:$Name").Value
    }
    return $null
}

function Add-EnvLine([System.Collections.Generic.List[string]]$List, [string]$Name, [string]$Value) {
    if ($null -ne $Value -and "$Value".Length -gt 0) {
        $List.Add("${Name}=$Value") | Out-Null
    }
}

if (-not $GCP_PROJECT_ID) { Fail "GCP_PROJECT_ID required" }
if (-not $GCP_REGION) { $GCP_REGION = "us-central1" }
if (-not $GCS_BUCKET) { Fail "GCS_BUCKET required" }
if (-not $DATABASE_URL) { Fail "DATABASE_URL required" }
if (-not $REDIS_URL) { Fail "REDIS_URL required" }

if ($env:INIT_DB -eq "1" -or (Get-DeployVar "INIT_DB") -eq "1") {
    Write-Host "Running init_db against DATABASE_URL..."
    Push-Location (Join-Path $Root "backend")
    $env:DATABASE_URL = $DATABASE_URL
    $env:PERSISTENCE_BACKEND = if ($PERSISTENCE_BACKEND) { $PERSISTENCE_BACKEND } else { "postgres" }
    python scripts/init_db.py
    if ($LASTEXITCODE -ne 0) { Pop-Location; throw "init_db failed" }
    Pop-Location
}

gcloud config set project $GCP_PROJECT_ID | Out-Null

$ApiImage = "gcr.io/$GCP_PROJECT_ID/papyrus-api"
$WebImage = "gcr.io/$GCP_PROJECT_ID/papyrus-web"

Write-Host "Enabling APIs..."
gcloud services enable run.googleapis.com artifactregistry.googleapis.com storage.googleapis.com cloudbuild.googleapis.com --quiet

$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
gsutil ls -b "gs://$GCS_BUCKET" 2>$null | Out-Null
$bucketMissing = $LASTEXITCODE -ne 0
$ErrorActionPreference = $prevEap
if ($bucketMissing) {
    Write-Host "Creating bucket gs://$GCS_BUCKET"
    gsutil mb -l $GCP_REGION "gs://$GCS_BUCKET"
    if ($LASTEXITCODE -ne 0) { throw "Failed to create GCS bucket $GCS_BUCKET" }
}

$ProjectNumber = (gcloud projects describe $GCP_PROJECT_ID --format="value(projectNumber)")
$RunSa = "${ProjectNumber}-compute@developer.gserviceaccount.com"
Write-Host "Granting GCS objectAdmin to Cloud Run service account $RunSa ..."
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
gsutil iam ch "serviceAccount:${RunSa}:roles/storage.objectAdmin" "gs://$GCS_BUCKET" 2>&1 | Out-Null
$ErrorActionPreference = $prevEap

$ApiEnvList = [System.Collections.Generic.List[string]]::new()
$basePairs = @{
    APP_ENV                         = "production"
    PERSISTENCE_BACKEND             = if ($PERSISTENCE_BACKEND) { $PERSISTENCE_BACKEND } else { "postgres" }
    FILE_STORAGE_BACKEND            = "gcs"
    GCS_BUCKET                      = $GCS_BUCKET
    USE_CELERY_BACKGROUND           = if ($null -ne (Get-DeployVar "USE_CELERY_BACKGROUND")) { (Get-DeployVar "USE_CELERY_BACKGROUND") } else { "true" }
    USE_CELERY_BULK                 = if ($null -ne (Get-DeployVar "USE_CELERY_BULK")) { (Get-DeployVar "USE_CELERY_BULK") } else { "true" }
    GROBID_ENABLED                  = "false"
    ENABLE_LLM_PDF_INGESTION        = "false"
    DATABASE_URL                    = $DATABASE_URL
    REDIS_URL                       = $REDIS_URL
    CORS_ORIGINS                    = $CORS_ORIGINS
    CROSSREF_MAILTO                 = $CROSSREF_MAILTO
    OPENALEX_MAILTO                 = $OPENALEX_MAILTO
    UNPAYWALL_EMAIL                 = $UNPAYWALL_EMAIL
    LLM_BACKEND                     = if ($LLM_BACKEND) { $LLM_BACKEND } else { "deepseek" }
    NLI_BACKEND                     = if ($NLI_BACKEND) { $NLI_BACKEND } else { "hf" }
    EMBEDDINGS_BACKEND              = if ($EMBEDDINGS_BACKEND) { $EMBEDDINGS_BACKEND } else { "snowflake" }
    AUDIT_DATA_DIR                  = if ($AUDIT_DATA_DIR) { $AUDIT_DATA_DIR } else { "/tmp/papyrus-data" }
}
foreach ($key in $basePairs.Keys) {
    Add-EnvLine $ApiEnvList $key $basePairs[$key]
}

$optionalKeys = @(
    "GCS_PREFIX", "ENABLE_DEEPSEEK", "DEEPSEEK_API_KEY", "DEEPSEEK_MODEL", "DEEPSEEK_BASE_URL",
    "OPENROUTER_API_KEY", "OPENROUTER_MODEL", "OPENROUTER_FALLBACK_MODEL", "OPENROUTER_BASE_URL",
    "HUGGINGFACE_API_KEY", "OPENAI_API_KEY", "SEMANTIC_SCHOLAR_API_KEY",
    "EXA_API_KEY", "FIRECRAWL_API_KEY", "APIFY_API_TOKEN",
    "SYNC_RELATIONAL_AUDITS", "USE_RELATIONAL_READ", "NLI_REQUIRES_CLAIM_APPROVAL",
    "SNOWFLAKE_EMBEDDING_MODEL", "MAX_UPLOAD_MB"
)
foreach ($key in $optionalKeys) {
    Add-EnvLine $ApiEnvList $key (Get-DeployVar $key)
}

$EnvYaml = New-TemporaryFile
$yamlLines = @("---")
foreach ($line in $ApiEnvList) {
    $parts = $line -split "=", 2
    $key = $parts[0]
    $val = $parts[1] -replace '"', '\"'
    $yamlLines += "${key}: `"${val}`""
}
$yamlLines | Set-Content $EnvYaml

Write-Host "Building API image..."
gcloud builds submit ./backend --tag $ApiImage --quiet

Write-Host "Deploying API..."
gcloud run deploy papyrus-api `
    --image $ApiImage `
    --region $GCP_REGION `
    --platform managed `
    --memory 2Gi `
    --cpu 2 `
    --timeout 3600 `
    --min-instances 0 `
    --max-instances 4 `
    --port 8080 `
    --allow-unauthenticated `
    --env-vars-file $EnvYaml `
    --quiet

Write-Host "Deploying Celery worker..."
gcloud run deploy papyrus-worker `
    --image $ApiImage `
    --region $GCP_REGION `
    --platform managed `
    --memory 2Gi `
    --cpu 2 `
    --timeout 3600 `
    --min-instances 1 `
    --max-instances 2 `
    --port 8080 `
    --no-allow-unauthenticated `
    --command "/bin/sh" `
    --args "scripts/cloudrun_worker.sh" `
    --env-vars-file $EnvYaml `
    --quiet

$ApiUrl = (gcloud run services describe papyrus-api --region $GCP_REGION --format="value(status.url)")
Write-Host "API URL: $ApiUrl"

if (-not $ApiUrl) {
    Write-Host "API deploy did not return a URL - skipping web build."
} elseif ($env:SKIP_WEB -eq "1") {
    Write-Host "SKIP_WEB=1 - skipping web build/deploy."
} else {
    Write-Host "Building web image (VITE_API_BASE_URL=$ApiUrl)..."
    gcloud builds submit . --config=deploy/cloudrun/cloudbuild-web.yaml `
        --substitutions "_IMAGE=$WebImage,_API_URL=$ApiUrl" --quiet

    Write-Host "Deploying web UI..."
    gcloud run deploy papyrus-web `
        --image $WebImage `
        --region $GCP_REGION `
        --platform managed `
        --memory 512Mi `
        --port 8080 `
        --allow-unauthenticated `
        --quiet

    $WebUrl = (gcloud run services describe papyrus-web --region $GCP_REGION --format="value(status.url)")
    Write-Host ""
    Write-Host "Web URL: $WebUrl"
    if ($WebUrl) {
        $origins = @($WebUrl)
        if ($CORS_ORIGINS) {
            foreach ($existing in ($CORS_ORIGINS -split ",")) {
                $trimmed = $existing.Trim()
                if ($trimmed -and $origins -notcontains $trimmed) { $origins += $trimmed }
            }
        }
        $merged = ($origins -join ",")
        if ($merged -ne $CORS_ORIGINS) {
            Write-Host ""
            Write-Host "CORS: set CORS_ORIGINS to include all web hostnames, then redeploy API:"
            Write-Host "  CORS_ORIGINS=$merged"
            Write-Host "  `$env:SKIP_WEB='1'; .\deploy\cloudrun\deploy.ps1"
        }
    }
}

Remove-Item $EnvYaml -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Done."
Write-Host "  API: $ApiUrl"
Write-Host "  Health: ${ApiUrl}/api/health/detailed"
