# Papyrus — Google Cloud Deployment Guide

You need three services: PostgreSQL, Redis, and GROBID (the first two are essential; GROBID is for PDF parsing quality but PyMuPDF fallback works without it).

## Option A: Cloud SQL + Memorystore (Managed, simplest)

### 1. PostgreSQL — Cloud SQL
```bash
gcloud sql instances create papyrus-db \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --storage-size=10GB \
  --password-policy-min-length=8

gcloud sql databases create papyrus --instance=papyrus-db
gcloud sql users create papyrus --instance=papyrus-db --password=YOUR_SECURE_PASSWORD
```
After creation, copy the **Public IP address** from `gcloud sql instances describe papyrus-db`.

Set this in your `.env`:
```
DATABASE_URL=postgresql+psycopg2://papyrus:YOUR_SECURE_PASSWORD@PUBLIC_IP:5432/papyrus
PERSISTENCE_BACKEND=both
```

Then authorize your local machine's IP (required to connect from dev):
```bash
gcloud sql instances patch papyrus-db --authorized-networks=YOUR_LOCAL_IP/32
```

> **Cost**: db-f1-micro is ~$7/month. 10GB storage is ~$1.70/month. Fits well within free trial credits ($300).

### 2. Redis — Memorystore
```bash
gcloud redis instances create papyrus-redis \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_7_0
```
This gives you a private IP. For local dev access, you'll need to set up a VM jump box or use **Option B** for Redis instead (run it yourself).

> **Cost**: 1GB Memorystore is ~$30/month. Consumes credits faster. For a cheap alternative, see Option B.

Set in `.env`:
```
REDIS_URL=redis://REDIS_PRIVATE_IP:6379/0
```

### 3. GROBID

GROBID needs significant RAM (2-4GB). Your options:

**Compute Engine VM (cheapest fit for credits)**:
```bash
gcloud compute instances create papyrus-grobid \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --boot-disk-size=20GB \
  --tags=http-server,grobid \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud
```

SSH in and run:
```bash
gcloud compute ssh papyrus-grobid --zone=us-central1-a

# On the VM:
sudo apt update && sudo apt install -y docker.io
sudo systemctl start docker
sudo docker run -d --restart always -p 8070:8070 grobid/grobid:0.8.0
```

Note the external IP:
```bash
gcloud compute instances describe papyrus-grobid --zone=us-central1-a --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

Create a firewall rule:
```bash
gcloud compute firewall-rules create allow-grobid \
  --allow tcp:8070 \
  --target-tags=grobid
```

Set in `.env`:
```
GROBID_URL=http://GROBID_EXTERNAL_IP:8070
GROBID_ENABLED=true
```

> **Cost**: e2-medium is ~$25/month. Or shut it down when not in use with `gcloud compute instances stop papyrus-grobid`.

---

## Option B: Single Compute Engine VM with Docker (Cheapest)

Run everything on one VM if you want to keep costs near zero:

```bash
gcloud compute instances create papyrus-all \
  --zone=us-central1-a \
  --machine-type=e2-standard-2 \
  --boot-disk-size=30GB \
  --tags=http-server,https-server \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud
```

SSH in and set up Docker Compose:
```bash
gcloud compute ssh papyrus-all --zone=us-central1-a

# Install Docker
sudo apt update
sudo apt install -y docker.io docker-compose-v2

# Clone your repo, then start everything
docker compose up -d postgres redis grobid api web
```

This gives you all 6 services on one machine. 

> **Cost**: e2-standard-2 (8GB RAM, for GROBID) is ~$50/month. Use `gcloud compute instances stop papyrus-all` when not in use.

---

## Option C: Mix and Match (Recommended)

- **PostgreSQL**: Cloud SQL (cheap, managed backups). ~$9/month.
- **Redis**: Run it yourself on a small VM or skip it entirely — the app works without Redis (uses in-memory fallback for rate limits, skips caching). Just set `USE_CELERY_BULK=false`.
- **GROBID**: Skip it. The app will use PyMuPDF fallback PDF parsing. It's less accurate for bibliography extraction but functional. Set `GROBID_ENABLED=false`.

This costs ~$9/month (just Cloud SQL) and gives you a functional pipeline.

---

## Quick Start: Minimal Deployment (No DB, Local Only)

Don't deploy anything yet. Run locally:

```bash
cd Papyrus
# The app already works with JSON file persistence (no Postgres needed)
# In .env, set:
# PERSISTENCE_BACKEND=json
# USE_CELERY_BULK=false
# GROBID_ENABLED=false

cd backend && uvicorn app.main:app --reload
cd frontend && npm install && npm run dev
```

This costs $0. Perfect for testing. Once you're ready, spin up Cloud SQL.

---

## Next Steps

1. Start with **PostgreSQL only** (Cloud SQL) — this is the most impactful, costs $9/month
2. Add Redis later if you need caching and Celery bulk jobs
3. Add GROBID later if PDF parsing accuracy matters

Recommended first command:
```bash
gcloud sql instances create papyrus-db --database-version=POSTGRES_16 --tier=db-f1-micro --region=us-central1 --storage-size=10GB
```
