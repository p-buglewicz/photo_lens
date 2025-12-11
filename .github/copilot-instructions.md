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
├── alembic/
│   ├── versions/         # Migration files
│   ├── env.py            # Alembic async environment
│   └── script.py.mako    # Migration template
├── docker-compose.yml
├── pyproject.toml        # uv dependency management
├── alembic.ini           # Alembic configuration
├── Makefile              # Development commands
├── .env.example          # TAKEOUT_PATH, THUMBNAIL_CACHE, MODEL_PATH
├── ALEMBIC.md            # Migration documentation
└── README.md
```

## Build & Development Setup

### Tool Chain

- **uv:** Ultra-fast Python package manager (replaces pip/poetry for this project)
- **Alembic:** Database schema versioning and migrations
- **Make:** Command shortcuts for common tasks
- **Docker Compose:** Multi-container orchestration

### Using uv

```bash
# Install dependencies
uv sync

# Run a script
uv run python script.py
uv run uvicorn backend.app.main:app --reload

# Run Alembic migrations
uv run alembic upgrade head

# Run tests
uv run pytest
```

### Using Make

```bash
make help              # Show all commands
make setup             # Install dependencies
make dev               # Start FastAPI with hot reload
make dev-all           # Start postgres + api with docker-compose
make migrate           # Run Alembic migrations
make migrate-new MESSAGE="Add column"  # Create migration
make test              # Run pytest
make lint              # Check code quality
make docker-up         # Start containers
```

### Docker Build Strategy

The Dockerfile uses multi-stage builds for efficiency:

1. **Builder stage:** Install uv, run `uv sync --no-dev`, creates `.venv`
2. **Runtime stage:** Copy only `.venv` and source code, minimal runtime image

This keeps production images lean while maintaining dependency consistency.

## Conventions & Patterns

### Database & ORM

- Use **SQLAlchemy 2.0** ORM for models in `backend/app/models/`
- **pgvector** extension (via SQL migrations) for similarity search
- Connection pooling via async SQLAlchemy (use `create_async_engine`)
- Store metadata as JSONB for flexible EXIF/Google JSON sidecar fields
- **All schema changes must be versioned as Alembic migrations** in `alembic/versions/`
- Migrations run automatically in Docker via `alembic upgrade head` on startup

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
# Edit .env with local paths (optional for defaults)

# Install dependencies with uv
uv sync

# Option 1: Start all services with Docker Compose
make dev-all

# Option 2: Run FastAPI locally with local postgres
docker compose up postgres  # in one terminal
make dev                   # in another terminal

# Verify backend health
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs

# Run tests
make test

# View test coverage
make test-cov
```

### Creating a New Migration

After modifying models in `backend/app/models/photos.py`:

```bash
# Create autogenerated migration
make migrate-new MESSAGE="Add new column to photos"

# Review the generated file in alembic/versions/
# Edit if necessary

# Apply migration
make migrate

# Or apply automatically via Docker
docker compose up --build
```

### Adding a New Endpoint

1. Create model in `backend/app/models/` if needed
2. Create Alembic migration if schema changed
3. Create/update route in `backend/app/api/{resource}.py`
4. Implement service logic in `backend/app/services/`
5. Test with curl or FastAPI docs (`http://localhost:8000/docs`)
6. Run linting: `make lint`

### Code Quality Checks

```bash
make lint              # Ruff checks
make format           # Black + ruff formatting
make typecheck        # Mypy static analysis
make pre-commit       # Run the full hook suite on all files
make test             # Run full test suite
```

### Debugging Database Issues

- View migration history: `make migrate-history`
- Rollback last migration: `make migrate-down`
- Check logs: `make docker-logs`
- Query database directly via psql (connect to postgres:5432)
- Inspect `ingest_status` table for ingestion batch records

## Key Dependencies

- **FastAPI:** Web framework
- **SQLAlchemy 2.0:** ORM
- **pgvector:** Similarity search
- **psycopg:** PostgreSQL async driver
- **transformers:** Local ML models (CLIP/SigLIP)
- **Pillow:** Image thumbnail generation
- **pydantic:** Request/response validation

## Communication Guidelines

- Keep responses concise and action-oriented
- Avoid excessive emoticons (use sparingly, if at all)
- Use clear, technical language
- Provide code examples and specific file paths
- Focus on implementation details over narrative

## When in Doubt

- Refer to **Phase X deliverables** in README to scope work
- Streaming & memory efficiency are non-negotiable
- External HDD mounts require proper error handling for missing paths
- Keep ML model loading atomic and reusable across batches
