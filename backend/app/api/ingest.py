from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.photos import IngestStatus
from worker.ingestion.metadata_ingest import ingest_takeout_metadata

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/start", status_code=status.HTTP_202_ACCEPTED)
async def start_ingestion(
    limit: Optional[int] = Query(default=None, ge=0),
    reprocess: bool = Query(default=False),
) -> dict[str, str]:
    """Trigger ingestion in background. Batch ID is generated server-side."""
    logger.info(f"POST /ingest/start called with limit={limit}, reprocess={reprocess}")

    if not settings.takeout_path:
        logger.error("TAKEOUT_PATH is not configured")
        raise HTTPException(status_code=400, detail="TAKEOUT_PATH is not configured")

    takeout_dir = Path(settings.takeout_path)
    if not takeout_dir.exists() or not takeout_dir.is_dir():
        logger.error(f"Takeout path invalid: {takeout_dir}")
        raise HTTPException(status_code=400, detail=f"Takeout path invalid: {takeout_dir}")

    batch_id = f"batch-{uuid4()}"
    logger.info(f"Starting background ingestion with batch_id={batch_id}")

    # Fire-and-forget background task
    asyncio.create_task(
        ingest_takeout_metadata(takeout_dir, batch_id=batch_id, limit=limit, reprocess=reprocess)
    )
    logger.info(f"Ingestion task created: batch_id={batch_id}")
    return {"batch_id": batch_id, "status": "started"}


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
