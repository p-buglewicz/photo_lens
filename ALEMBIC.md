# Database Migrations with Alembic

LensAnalytics uses Alembic for database schema versioning and migrations.

## Key Concepts

- **Migrations** are stored in `alembic/versions/`
- **Models** are defined in `backend/app/models/`
- Changes are applied using `alembic upgrade` or automatically on container startup

## Common Tasks

### Running migrations locally

```bash
# Apply all pending migrations
alembic upgrade head

# Rollback to previous version
alembic downgrade -1

# View migration history
alembic history
```

### Creating a new migration

After modifying models in `backend/app/models/`, create a migration:

```bash
alembic revision --autogenerate -m "Add column to photos"
```

Review the generated migration file in `alembic/versions/` before applying.

### Applying migrations in Docker

Migrations run automatically on container startup:

```bash
docker compose up --build
```

## Structure

- `alembic.ini` - Alembic configuration
- `alembic/env.py` - Migration execution environment
- `alembic/script.py.mako` - Migration file template
- `alembic/versions/` - Individual migration files
- `backend/app/models/base.py` - SQLAlchemy declarative base
- `backend/app/models/photos.py` - Photo and IngestStatus models
