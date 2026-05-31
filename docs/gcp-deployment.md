# Papyrus — Google Cloud deployment

## Recommended: Cloud Run (serverless)

For API + worker + static UI without managing VMs or GROBID, use:

**[cloudrun-deployment.md](./cloudrun-deployment.md)**

That path uses:

- **Supabase** or **Neon** for Postgres (`DATABASE_URL` with `postgresql+psycopg2` and `sslmode=require`)
- **Redis Cloud** or **Upstash** for Celery and cache
- **GCS** for uploaded PDFs (`FILE_STORAGE_BACKEND=gcs`)
- **PyMuPDF** for PDF ingestion (`GROBID_ENABLED=false`)
- **DeepSeek API** or **OpenRouter** for intent/claims only (`LLM_BACKEND`)

Deploy script: `deploy/cloudrun/deploy.ps1` (see `deploy/cloudrun/env.template`).

---

## Legacy: VMs and managed GCP services

The sections below describe VM-based or partial-GCP setups. They remain valid if you self-host GROBID or want everything on one machine.

### What you need today

| Service | Required? | Notes |
|---------|-----------|--------|
| PostgreSQL | Yes (for production) | Cloud SQL, Supabase, or local Docker |
| Redis | Recommended | Celery audits/bulk; in-process fallback if missing |
| GROBID | **No** (default off) | PyMuPDF handles PDF parsing; enable later for bibliography quality |

Default `.env` for cost-conscious deploys:

```env
GROBID_ENABLED=false
ENABLE_LLM_PDF_INGESTION=false
LLM_BACKEND=deepseek
```

---

## Option A: Cloud SQL + Memorystore

### 1. PostgreSQL — Cloud SQL

```bash
gcloud sql instances create papyrus-db \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --storage-size=10GB

gcloud sql databases create papyrus --instance=papyrus-db
gcloud sql users create papyrus --instance=papyrus-db --password=YOUR_SECURE_PASSWORD
```

```env
DATABASE_URL=postgresql+psycopg2://papyrus:YOUR_SECURE_PASSWORD@PUBLIC_IP:5432/papyrus
PERSISTENCE_BACKEND=postgres
```

Authorize your dev IP:

```bash
gcloud sql instances patch papyrus-db --authorized-networks=YOUR_LOCAL_IP/32
```

### 2. Redis — Memorystore

```bash
gcloud redis instances create papyrus-redis \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_7_0
```

```env
REDIS_URL=redis://REDIS_PRIVATE_IP:6379/0
```

> Memorystore is private; Cloud Run needs VPC connector or use **Redis Cloud** instead (see Cloud Run doc).

### 3. GROBID (optional, public beta)

Only if you set `GROBID_ENABLED=true`. Needs ~2–4 GiB RAM.

```bash
gcloud compute instances create papyrus-grobid \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --tags=grobid \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud
```

On the VM: `docker run -d --restart always -p 8070:8070 grobid/grobid:0.8.0`

```env
GROBID_URL=http://GROBID_EXTERNAL_IP:8070
GROBID_ENABLED=true
```

---

## Option B: Single VM with Docker Compose

```bash
docker compose up -d postgres redis
docker compose up --build api worker web
```

No GROBID container is started by default. To add it:

```bash
docker compose --profile grobid up -d grobid
# GROBID_ENABLED=true in .env
```

`e2-standard-2` is enough without GROBID; add RAM if you run GROBID on the same host.

---

## Option C: Minimal cost (managed DB only)

- **Postgres:** Supabase free tier or Cloud SQL micro
- **Redis:** Redis Cloud free tier (or skip Celery with `USE_CELERY_BULK=false` for testing only)
- **GROBID:** off — PyMuPDF ingestion
- **App:** Cloud Run per [cloudrun-deployment.md](./cloudrun-deployment.md)

---

## Local development ($0 infra)

```bash
cp .env.example .env
# PERSISTENCE_BACKEND=json  # optional: no Postgres
# GROBID_ENABLED=false      # default
# ENABLE_LLM_PDF_INGESTION=false

cd backend && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

Use remote Supabase + Redis by setting `DATABASE_URL` and `REDIS_URL` in `.env` and running API/worker on the host (or Docker with `env_file: .env`).

---

## Related docs

- [configuration.md](./configuration.md) — all feature flags and LLM routing
- [cloudrun-deployment.md](./cloudrun-deployment.md) — production Cloud Run steps
