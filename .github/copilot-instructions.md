# LensAnalytics - AI Agent Instructions

## Project Overview

**LensAnalytics** is a self-hosted, privacy-focused photo analytics engine that processes Google Takeout archives locally without uploading photos anywhere. It combines streaming ingestion, EXIF parsing, ML embeddings (CLIP/SigLIP), and PostgreSQL storage into a searchable analytics platform.

**Core Value:** Local-first privacy with minimal disk usage through streaming ingestion and storage of only metadata + embeddings, not images.

## Architecture - Critical Understanding

The system follows a **producer-consumer pipeline** with clear boundaries:

```
Google Takeout ZIPs → Ingestion Worker → PostgreSQL + pgvector → FastAPI Backend → Web Dashboard
```

**Key Design Decisions:**

- **Streaming Ingestion:** Photos extracted directly from ZIP without full extraction to disk
- **External HDD:** All Takeout ZIPs and optional thumbnails stored on separate storage (`/mnt/photos/Takeout`)
- **pgvector:** PostgreSQL extension for similarity search on 512-768D embeddings
- **No Cloud:** All ML computation is local (CLIP/SigLIP/MobileCLIP models run on-device)
- **Minimal Storage:** Store only metadata, embeddings, and optional 256px thumbnails — not original images

## Project Phases & Deliverables

Development is intentionally modular for portfolio demonstration:

- **Phase 1:** Docker Compose setup, FastAPI skeleton, `/health` endpoint
- **Phase 2:** ZIP streaming, EXIF parsing, JSON metadata normalization
- **Phase 3:** Local vision embeddings (CLIP-based), similarity search endpoints
- **Phase 4:** Analytics endpoints (camera/lens histograms, temporal clustering, color analysis)
- **Phase 5:** Thumbnail service with HDD caching
- **Phase 6:** Web Dashboard (React + Tailwind or Vue)
- **Phase 7:** Advanced features (face clustering, gym progress mode, moodboard generation)

## Directory Structure

```
lensanalytics/
├── backend/
│   ├── app/
│   │   ├── api/          # Route handlers organized by resource
│   │   ├── core/         # Config, logging, database connection
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── services/     # Business logic (analytics, search, metadata normalization)
│   │   └── main.py       # FastAPI app initialization
│   └── Dockerfile
├── worker/
│   ├── run_worker.py     # Entry point
│   ├── ingestion/        # ZIP streaming, EXIF extraction, embedding generation
│   └── Dockerfile
├── docker-compose.yml
├── .env.example          # TAKEOUT_PATH, THUMBNAIL_CACHE, MODEL_PATH
└── README.md
```

## Conventions & Patterns

### Database & ORM

- Use **SQLAlchemy 2.0** ORM for models in `backend/app/models/`
- **pgvector** column type for embeddings: `Vector(dim=768)` (512-768D range)
- Connection pooling via async SQLAlchemy (use `create_async_engine`)
- Store metadata as JSONB for flexible EXIF/Google JSON sidecar fields

### FastAPI Routes

- Organize routes by resource in `api/` subdirectory (e.g., `api/photos.py`, `api/search.py`, `api/analytics.py`)
- Use dependency injection for database sessions
- Return pagination for list endpoints with optional `?limit=&offset=` params
- Ingestion status endpoints: `GET /ingest/status`, `POST /ingest/start`

### Worker Pipeline

- Implement **generator pattern** for streaming ZIP iteration (avoid loading entire files into memory)
- Normalize metadata from both EXIF tags and Google JSON sidecars into unified schema
- Fail gracefully on corrupt images — log skipped files, continue processing
- Use **task queues** (Celery/RQ) for async ingestion with progress reporting

### Configuration

- Environment variables for paths: `TAKEOUT_PATH`, `THUMBNAIL_CACHE`, `DATABASE_URL`
- Optional `MODEL_PATH` for local CLIP model cache
- `.env.example` must document all required variables

### Privacy Constraints

- Never save original image bytes to database
- ML models must run locally — no OpenAI/Hugging Face API calls
- Thumbnails (optional) are 256px max, cached on external HDD

## Integration Points

### PostgreSQL

- `psycopg` (async) for Python
- **pgvector** extension for cosine similarity: `SELECT * FROM photos ORDER BY embedding <-> query_vector LIMIT 10`
- Composite indexes on frequently filtered columns (camera model, lens, date)

### ML Models

- **CLIP/SigLIP/MobileCLIP** via Hugging Face `transformers` library
- Generate embeddings in worker, store in database
- Load model once on worker startup, reuse across batches

### Google Takeout Format

- Nested directories with photos and `*.json` sidecars (one JSON per photo)
- JSON contains Google's processed metadata (type, storage bytes, photos taken dates)
- Photos may be in subdirs like `Google Photos/`, `Takeout/`, or year/month folders

## Common Development Workflows

### Local Development

```bash
# Set up environment
cp .env.example .env
# Edit .env with local paths

# Install dependencies with UV
uv sync

# Start services
docker compose up --build

# Verify backend health
curl http://localhost:8000/health

# Run tests (once implemented)
uv run pytest
```

### Adding a New Endpoint

1. Create model in `backend/app/models/` if needed
2. Create/update route in `backend/app/api/{resource}.py`
3. Implement service logic in `backend/app/services/`
4. Add database schema migration if needed
5. Test with curl or FastAPI docs (`/docs`)

### Debugging Ingestion

- Worker logs show progress and skipped files
- Check `ingest_status` table for batch records
- Query database directly to inspect ingested photos and metadata

## Key Dependencies

- **FastAPI:** Web framework
- **SQLAlchemy 2.0:** ORM
- **pgvector:** Similarity search
- **psycopg:** PostgreSQL async driver
- **transformers:** Local ML models (CLIP/SigLIP)
- **Pillow:** Image thumbnail generation
- **pydantic:** Request/response validation

## When in Doubt

- Refer to **Phase X deliverables** in README to scope work
- Streaming & memory efficiency are non-negotiable
- External HDD mounts require proper error handling for missing paths
- Keep ML model loading atomic and reusable across batches
