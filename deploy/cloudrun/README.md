# Cloud Run production deploy

## Prerequisites

1. GCP project with billing; `gcloud auth login`
2. Supabase (or Neon) Postgres URL — `postgresql+psycopg2://...?sslmode=require`
3. Redis Cloud (or Upstash) — reachable from Cloud Run (`redis://` or `rediss://`)
4. API keys in `deploy/cloudrun/.env` (from `env.template`)

## First-time setup

```powershell
Copy-Item deploy\cloudrun\env.template deploy\cloudrun\.env
# Edit .env — fill GCP_PROJECT_ID, DATABASE_URL, REDIS_URL, keys, mailtos

cd backend
pip install -r requirements.txt
$env:DATABASE_URL = "..."   # same as deploy .env
python scripts/init_db.py
```

Or one-shot with deploy script:

```powershell
$env:INIT_DB = "1"
.\deploy\cloudrun\deploy.ps1
```

## Deploy

```powershell
.\deploy\cloudrun\deploy.ps1
```

Linux/macOS:

```bash
chmod +x deploy/cloudrun/deploy.sh
INIT_DB=1 ./deploy/cloudrun/deploy.sh   # first time only
./deploy/cloudrun/deploy.sh
```

## After first deploy (CORS)

1. Note the **web** URL from the script output.
2. Set `CORS_ORIGINS` in `deploy/cloudrun/.env` to that URL (comma-separated if multiple).
3. Redeploy API + worker only:

```powershell
$env:SKIP_WEB = "1"
.\deploy\cloudrun\deploy.ps1
```

## Verify

- `GET {API_URL}/api/health/detailed` — postgres, redis ok; grobid skipped
- Upload a PDF from the web UI; confirm worker logs in Cloud Run → `papyrus-worker`

## Scripts

| Script | Purpose |
|--------|---------|
| `deploy.ps1` / `deploy.sh` | Build images, GCS IAM, deploy api + worker + web |
| `../cloudrun/cloudbuild-web.yaml` | Web image (repo root context) |
| `../../backend/scripts/init_db.py` | Create Postgres tables |
