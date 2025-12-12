# LensAnalytics

**A local-first, privacy-focused photo analytics and search engine.**

LensAnalytics is a self-hosted photo intelligence platform that ingests your Google Photos Takeout archive, extracts metadata, generates semantic embeddings, and builds a searchable analytics dashboard — without uploading your photos anywhere.

## Quick Overview

| Component | Technology |
|-----------|-----------|
| **Backend** | FastAPI (Python) |
| **Frontend** | Vue 3 + Nginx (static) |
| **Workers** | Python (ingestion & ML) |
| **Database** | PostgreSQL + pgvector |
| **Deployment** | Docker Compose |
| **Storage** | External HDD support |
| **ML** | Local AI models (privacy-first) |

## Ingestion Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- `uv` package manager

### Development Setup

```bash
# 1. Clone and enter directory
git clone https://github.com/p-buglewicz/photo_lens.git
cd photo_lens

# 2. Configure environment
cp .env.example .env
# Edit .env and set HOST_PHOTO_PATH to your Takeout directory:
# HOST_PHOTO_PATH=/path/to/your/photos

# 3. Docker Desktop: Share the photo path
# Open Docker Desktop → Settings → Resources → File Sharing
# Add the directory containing your photos (e.g., /media, /mnt, or parent of HOST_PHOTO_PATH)
# This is required for Docker to access external drives/paths
# On Linux with Docker Engine, paths are usually accessible by default

# 4. Install dependencies (for local dev)
make setup

# 5. Install git hooks (recommended)
uv run pre-commit install

# 6. Start services (postgres + backend + frontend)
docker compose up --build

# 7. Open the web UI
open http://localhost:8080

# 8. Check API health
curl http://localhost:8001/health

# 9. API documentation
open http://localhost:8001/docs
```

### Common Commands

```bash
# Database
make migrate              # Run pending migrations
make migrate-new MESSAGE="description"

# Code quality
make lint                 # Ruff checks
make format               # Black + ruff format
make typecheck            # Mypy static analysis
make pre-commit           # Run pre-commit on all files
make test                # Run tests

# Docker
make docker-up           # Start containers
make docker-down         # Stop containers
make docker-logs         # View logs
make docker-frontend-logs # Frontend container logs (nginx + Vue static)
make docker-backend-logs  # Backend container logs
make docker-ps            # Running containers summary
make docker-restart       # Restart backend + frontend containers

# Worker (Phase 1)
make worker              # Print first N image names from Takeout ZIPs

# Direct (module execution from project root)
uv run python -m worker.run_worker --takeout /path/to/Takeout --limit 20

Note: This Phase 1 CLI is temporary. In Phase 2 the ingestion will run as a background worker with API triggers (usage will change).
```

See [Makefile](./Makefile) for all available commands.

## Why Google Takeout?

Google Photos API limitations:

- No full library downloads
- No bulk media access
- No large-scale backups

Google Takeout provides everything:

- Original photos
- Complete EXIF metadata
- JSON metadata sidecars
- Albums & folders structure
- Full editing history

This project processes all Takeout files **locally** with **minimal disk space** using streaming ingestion.

## Architecture

> **Note:** Architecture is not final and subject to change.

```text
           ┌──────────────────────┐
           │ Google Takeout ZIPs  │  (stored on external HDD)
           └──────────┬───────────┘
                      │ streamed, 1 file at a time
                      ▼
           ┌──────────────────────┐
           │ Ingestion Worker     │
           │  - unzip streaming   │
           │  - EXIF parsing      │
           │  - ML embeddings     │
           │  - thumbnails        │
           └──────────┬───────────┘
                      ▼
           ┌──────────────────────┐
           │ PostgreSQL + pgvector│
           └──────────┬───────────┘
                      ▼
           ┌──────────────────────┐
           │ FastAPI Backend      │
           │  analytics API       │
           └──────────┬───────────┘
                      ▼
           ┌──────────────────────┐
           │ Web Dashboard (TBD)  │
           └──────────────────────┘
```

## Development Roadmap

The project is intentionally split into **phases**, each delivering incremental value.

### Phase 1 — Core Infrastructure (MVP)

**Goals:**

- Set up docker-compose environment
- Create backend (FastAPI) skeleton
- Add external HDD mount point for Takeout zips
- Implement basic database schema
- Build ingestion worker structure

**Deliverables:**

- `docker-compose.yml`
- External HDD mount instructions
- `backend/` + `worker/` directory scaffolding
- Minimal `/health` endpoint

### Phase 2 — Takeout Ingestion Pipeline

**Goals:**

- Stream photos directly from ZIP (no full extraction)
- Parse EXIF metadata
- Parse Google JSON sidecars
- Normalize metadata

**Deliverables:**

- Background worker that:
  - Opens each Takeout ZIP
  - Iterates files
  - Extracts metadata
  - Writes rows to PostgreSQL
- Logging & progress reporting

**Usage (Phase 2 worker):**

```bash
# Install deps
uv sync

# Run Alembic migrations
uv run alembic upgrade head

# Process Takeout ZIPs (update TAKEOUT_PATH as needed)
uv run python worker/run_worker.py --takeout /mnt/photos/Takeout --batch-id $(date -u +"batch-%Y%m%d-%H%M%S")

# Reprocess existing entries (overwrite metadata for same source URIs)
uv run python worker/run_worker.py --takeout /mnt/photos/Takeout --reprocess --batch-id reprocess-$(date -u +"%Y%m%d-%H%M%S")
```

**Storage Strategy:**

- No original images saved
- Optional 256px thumbnails
- Only metadata + embeddings stored long-term

### Phase 3 — Machine Learning Embeddings

**Goals:**

- Integrate local vision model (CLIP, SigLIP, or MobileCLIP)
- Generate 512–768D embeddings
- Store vectors in pgvector column
- Build similarity search

**Deliverables:**

- `GET /search?query=…` endpoint
- `GET /find_similar/:photo_id` endpoint

**Privacy:**

- All ML computation is local
- No cloud API calls

### Phase 4 — Photo Analytics Engine

**Goals:**

- Compute structured analytics:
  - Camera usage
  - Lens usage histogram
  - Focal length distribution
  - Timestamp clusters
  - Location clustering (if GPS available)
  - Dominant colors & moods
  - Duplicate detection

**Deliverables:**

- `GET /analytics/camera`
- `GET /analytics/time/day`
- `GET /analytics/mood`
- `GET /analytics/duplicates`

### Phase 5 — Thumbnail Caching & Preview Service

**Goals:**

- On-the-fly thumbnail generation
- Local cache on HDD or SSD
- Serve thumbnails via FastAPI

**Deliverables:**

- `GET /photo/:id/thumb`
- Small image cache (~10–30 KB per image)

### Phase 6 — Web Dashboard

**Goals:**

- Modern UI with:
  - Timeline view
  - Search interface
  - Analytics charts
  - Similarity results
  - Map view (if GPS available)

**Tech Stack Options:**

- React + Tailwind + shadcn/ui
- Or simple Vue frontend

**Deliverables:**

- `/ui` served via Nginx or FastAPI static frontend

### Phase 7 — Advanced Features (Optional)

**Ideas:**

- Face clustering (local-only)
- Scene detection
- Auto-tag suggestions
- Gym Progress Mode (body outline comparison)
- Screenshot analyzer (game clustering)
- Moodboard generation
- Album reconstruction (Takeout has album JSON!)

> These features are excellent portfolio boosters.

## Project Structure

```bash
lensanalytics/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   └── main.py
│   └── Dockerfile
├── frontend/
│   ├── Dockerfile
│   └── static/
├── worker/
│   ├── run_worker.py
│   ├── ingestion/
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## External HDD Support

This project supports using an external drive for:

- Takeout ZIP storage
- Thumbnails
- Full-text metadata cache

**Example mount point:**

```text
/mnt/photos/Takeout/
```

**Update `.env`:**

```env
TAKEOUT_PATH=/mnt/photos/Takeout
THUMBNAIL_CACHE=/mnt/photos/Thumbnails
```

This ensures large media never fills your internal disk.

## Privacy & Local-First Philosophy

- No cloud storage
- No cloud ML APIs
- No photo uploads
- Everything stays on your machine
- You control the HDD with all data

Ideal for privacy-sensitive users and for demonstration in senior interviews.

## Quick Start

### 1. Place Google Takeout ZIPs on external HDD

```text
/mnt/photos/Takeout/takeout-001.zip
/mnt/photos/Takeout/takeout-002.zip
```

### 2. Start services

```bash
docker compose up --build
```

### 3. Trigger ingestion

```bash
POST /ingest/start
```

### 4. View progress

```bash
GET /ingest/status
```

### 5. Open the frontend (Vue)

```text
http://localhost:8080
```

## Local Development (outside Docker)

```bash
# Set up environment
cp .env.example .env
# Edit .env for local DB (outside Docker):
# DATABASE_URL=postgresql+psycopg://lensanalytics:lensanalytics_dev@localhost:5432/lensanalytics

# Install deps
uv sync

# Run Alembic migrations
uv run alembic upgrade head

# Start backend
uv run uvicorn backend.app.main:app --reload
```

## Frontend UI

- Served by the `frontend` service in [docker-compose.yml](docker-compose.yml) using Nginx to host the static Vue app from [frontend/static/index.html](frontend/static/index.html).
- Accessible on the host at [http://localhost:8080](http://localhost:8080) (container port 80).
- The UI calls the backend exposed on [http://localhost:8001](http://localhost:8001) when accessed from the host; inside the compose network it talks to the `backend` service directly.
- Useful helpers: `make docker-frontend-logs`, `make docker-backend-logs`, and `make docker-ps` for quick inspection.
