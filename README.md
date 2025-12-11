# LensAnalytics

**A local-first, privacy-focused photo analytics and search engine.**

LensAnalytics is a self-hosted photo intelligence platform that ingests your Google Photos Takeout archive, extracts metadata, generates semantic embeddings, and builds a searchable analytics dashboard — without uploading your photos anywhere.

## Quick Overview

| Component | Technology |
|-----------|-----------|
| **Backend** | FastAPI (Python) |
| **Workers** | Python (ingestion & ML) |
| **Database** | PostgreSQL + pgvector |
| **Deployment** | Docker Compose |
| **Storage** | External HDD support |
| **ML** | Local AI models (privacy-first) |

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

The project is intentionally split into **phases**, each deliverable on its own — ideal for interviews or iterative development.

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
