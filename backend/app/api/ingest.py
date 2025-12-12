from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app import schemas
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.photos import IngestStatus
from worker.ingestion.metadata_ingest import ingest_takeout_metadata

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingest", tags=["ingest"])

_takeout_override: Optional[str] = None
_ingest_limit_override: Optional[int] = None
_ingest_reprocess_override: Optional[bool] = None


def _resolve_takeout_path(takeout_path: Optional[str]) -> Path:
    """Pick a usable takeout path from request override, runtime override, or env."""
    candidate = takeout_path or _takeout_override or settings.takeout_path
    if not candidate:
        logger.error("TAKEOUT_PATH is not configured")
        raise HTTPException(status_code=400, detail="TAKEOUT_PATH is not configured")

    takeout_dir = Path(candidate).expanduser()
    if not takeout_dir.exists() or not takeout_dir.is_dir():
        logger.error(f"Takeout path invalid: {takeout_dir}")
        raise HTTPException(status_code=400, detail=f"Takeout path invalid: {takeout_dir}")

    return takeout_dir


@router.post("/start", status_code=status.HTTP_202_ACCEPTED)
async def start_ingestion(
    limit: Optional[int] = Query(default=None, ge=0),
    reprocess: Optional[bool] = Query(default=None),
    takeout_path: Optional[str] = Query(
        default=None, description="Override TAKEOUT_PATH for this run"
    ),
) -> dict[str, str]:
    """Trigger ingestion in background. Batch ID is generated server-side."""
    resolved_limit = limit if limit is not None else _ingest_limit_override
    resolved_reprocess = (
        reprocess
        if reprocess is not None
        else _ingest_reprocess_override if _ingest_reprocess_override is not None else False
    )

    logger.info(
        "POST /ingest/start called with limit=%s, reprocess=%s, takeout_path=%s",
        resolved_limit,
        resolved_reprocess,
        takeout_path,
    )

    takeout_dir = _resolve_takeout_path(takeout_path)

    batch_id = f"batch-{uuid4()}"
    logger.info(f"Starting background ingestion with batch_id={batch_id}")

    # Fire-and-forget background task
    asyncio.create_task(
        ingest_takeout_metadata(
            takeout_dir,
            batch_id=batch_id,
            limit=resolved_limit,
            reprocess=resolved_reprocess,
        )
    )
    logger.info(f"Ingestion task created: batch_id={batch_id}")
    return {"batch_id": batch_id, "status": "started"}


@router.get("/config", response_model=schemas.IngestConfigResponse)
async def get_ingest_config() -> schemas.IngestConfigResponse:
    """Expose the currently configured TAKEOUT_PATH and its source."""
    source = "override" if _takeout_override else ("env" if settings.takeout_path else "unset")
    return schemas.IngestConfigResponse(
        takeout_path=_takeout_override or settings.takeout_path,
        source=source,
        limit=_ingest_limit_override,
        reprocess=_ingest_reprocess_override,
    )


@router.put("/config", response_model=schemas.IngestConfigResponse)
async def update_ingest_config(
    payload: schemas.UpdateIngestConfigRequest,
) -> schemas.IngestConfigResponse:
    """Allow FE to set TAKEOUT_PATH, limit, and reprocess defaults at runtime."""

    global _takeout_override, _ingest_limit_override, _ingest_reprocess_override

    if payload.takeout_path is not None:
        takeout_dir = Path(payload.takeout_path).expanduser()
        if not takeout_dir.exists() or not takeout_dir.is_dir():
            logger.error(f"Takeout path invalid: {takeout_dir}")
            raise HTTPException(status_code=400, detail=f"Takeout path invalid: {takeout_dir}")
        _takeout_override = str(takeout_dir)
        logger.info(f"TAKEOUT_PATH override set to {_takeout_override}")

    if payload.limit is not None:
        _ingest_limit_override = payload.limit
        logger.info(f"Ingestion default limit override set to {_ingest_limit_override}")

    if payload.reprocess is not None:
        _ingest_reprocess_override = payload.reprocess
        logger.info(f"Ingestion default reprocess override set to {_ingest_reprocess_override}")

    return schemas.IngestConfigResponse(
        takeout_path=_takeout_override or settings.takeout_path,
        source="override" if _takeout_override else ("env" if settings.takeout_path else "unset"),
        limit=_ingest_limit_override,
        reprocess=_ingest_reprocess_override,
    )


@router.delete("/config", status_code=status.HTTP_204_NO_CONTENT)
async def clear_ingest_config_override() -> None:
    """Remove runtime TAKEOUT_PATH override and fall back to env."""

    global _takeout_override, _ingest_limit_override, _ingest_reprocess_override
    _takeout_override = None
    _ingest_limit_override = None
    _ingest_reprocess_override = None


@router.get("/status")
async def list_ingestion_status(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=200),
) -> dict[str, list[dict]]:
    """List recent ingestion batches and their status."""
    logger.debug(f"GET /ingest/status called with limit={limit}")
    result = await db.execute(
        select(IngestStatus).order_by(IngestStatus.started_at.desc()).limit(limit)
    )
    rows = result.scalars().all()
    logger.debug(f"Found {len(rows)} ingestion batches")

    def to_dict(s: IngestStatus) -> dict:
        return {
            "batch_id": s.batch_id,
            "status": s.status,
            "started_at": s.started_at,
            "completed_at": s.completed_at,
            "total_files": s.total_files,
            "processed_files": s.processed_files,
            "skipped_files": s.skipped_files,
            "error_message": s.error_message,
        }

    items = [to_dict(s) for s in rows]
    logger.debug(f"Returning {len(items)} ingestion status items")
    return {"items": items}
