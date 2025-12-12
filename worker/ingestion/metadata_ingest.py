from __future__ import annotations

import asyncio
import io
import json
import logging
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator, Optional, Tuple
from uuid import uuid4

from PIL import ExifTags, Image
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import AsyncSessionLocal
from backend.app.models.photos import IngestStatus, Photo

logger = logging.getLogger(__name__)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".webp", ".tif", ".tiff"}


def _list_zip_entries(zip_path: Path) -> list[zipfile.ZipInfo]:
    with zipfile.ZipFile(zip_path, mode="r") as zf:
        return [info for info in zf.infolist() if not info.is_dir()]


def _is_image(name: str) -> bool:
    return Path(name).suffix.lower() in IMAGE_EXTS


def _mime_from_name(name: str) -> Optional[str]:
    suffix = Path(name).suffix.lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".heic": "image/heic",
        ".webp": "image/webp",
        ".tif": "image/tiff",
        ".tiff": "image/tiff",
    }.get(suffix)


def _read_zip_member_bytes(zip_path: Path, member: str) -> bytes:
    with zipfile.ZipFile(zip_path, mode="r") as zf:
        return zf.read(member)


def _make_json_serializable(obj: Any) -> Any:
    """Recursively convert non-JSON-serializable types to JSON-compatible types.

    Handles bytes, tuples, lists, dicts recursively. Strips null bytes from strings and keys.
    """
    if obj is None:
        return None
    elif isinstance(obj, bytes):
        # Decode and strip null bytes which PostgreSQL JSON cannot handle
        return obj.decode("utf-8", errors="ignore").replace("\x00", "")
    elif isinstance(obj, str):
        # Also strip null bytes from strings
        return obj.replace("\x00", "")
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, (tuple, list)):
        return [_make_json_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        # Process both keys and values, removing null bytes from keys
        return {
            (
                k.replace("\x00", "") if isinstance(k, str) else str(k).replace("\x00", "")
            ): _make_json_serializable(v)
            for k, v in obj.items()
        }
    elif isinstance(obj, (int, float, bool)):
        return obj
    else:
        # Fallback: convert unknown types to string and strip nulls
        return str(obj).replace("\x00", "")


def _parse_exif(image_bytes: bytes) -> dict:
    if Image is None:
        logger.debug("Pillow not available, skipping EXIF parsing")
        return {}
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            exif = getattr(img, "_getexif", lambda: None)() or {}
            logger.debug(f"Extracted {len(exif)} EXIF tags from image ({len(image_bytes)} bytes)")
            # Convert EXIF tag ids to names
            exif_named = {}
            for tag_id, value in exif.items():
                tag = ExifTags.TAGS.get(tag_id, str(tag_id)) if ExifTags else str(tag_id)
                # Convert non-JSON-serializable types to strings (recursively)
                exif_named[tag] = _make_json_serializable(value)
            # Normalize common fields
            taken_str = exif_named.get("DateTimeOriginal") or exif_named.get("DateTime")
            result = {
                "make": exif_named.get("Make"),
                "model": exif_named.get("Model"),
                "lens": exif_named.get("LensModel"),
                "datetime_original": taken_str,
                "raw": exif_named,
            }
            logger.debug(
                f"Normalized EXIF: make={result['make']}, model={result['model']}, taken={result['datetime_original']}"
            )
            return result
    except Exception as e:
        logger.warning(f"Failed to parse EXIF: {e}")
        return {}


def _parse_google_json(json_bytes: bytes) -> Any:
    try:
        data = json.loads(json_bytes.decode("utf-8"))
        logger.debug(f"Parsed Google JSON sidecar: {len(data)} fields")
        return data
    except Exception as e:
        logger.warning(f"Failed to parse Google JSON sidecar: {e}")
        return {}


def _normalize_taken_at(exif_meta: dict, google_meta: dict) -> Optional[datetime]:
    # Prefer Google JSON photoTakenTime.timestamp
    try:
        ts = google_meta.get("photoTakenTime", {}).get("timestamp")
        if ts:
            return datetime.fromtimestamp(int(ts), tz=timezone.utc)
    except Exception:
        pass
    # Fallback to EXIF DateTimeOriginal formatted like "YYYY:MM:DD HH:MM:SS"
    dt_str = exif_meta.get("datetime_original")
    if isinstance(dt_str, str):
        for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(dt_str, fmt)
            except Exception:
                continue
    return None


async def stream_zip_metadata(
    takeout_dir: Path,
    limit: int | None = None,
    recursive: bool = True,
) -> AsyncIterator[dict]:
    """Yield normalized metadata blobs for each image in Takeout ZIPs.

    Each item includes: filename, source_uri, file_size, mime_type, exif, google_json, taken_at.
    """
    count = 0
    zip_iter = takeout_dir.rglob("*.zip") if recursive else takeout_dir.glob("*.zip")
    zips = sorted(zip_iter)
    logger.info(f"Found {len(zips)} ZIP files in {takeout_dir}")

    for zip_path in zips:
        logger.debug(f"Processing ZIP: {zip_path.name}")
        # Build quick lookup of entries
        entries = await asyncio.to_thread(_list_zip_entries, zip_path)
        logger.debug(f"ZIP {zip_path.name} contains {len(entries)} members")

        names = [entry.filename for entry in entries]
        image_count = 0
        for entry in entries:
            if not _is_image(entry.filename):
                continue
            image_count += 1
            base = entry.filename
            sidecar = f"{base}.json"
            google_json: dict = {}
            exif_meta: dict = {}
            try:
                if sidecar in names:
                    json_bytes = await asyncio.to_thread(_read_zip_member_bytes, zip_path, sidecar)
                    google_json = _parse_google_json(json_bytes)
                    logger.debug(f"Found sidecar for {Path(base).name}")
            except Exception as e:
                logger.warning(f"Error reading sidecar {sidecar}: {e}")
                google_json = {}
            try:
                img_bytes = await asyncio.to_thread(_read_zip_member_bytes, zip_path, base)
                exif_meta = _parse_exif(img_bytes)
            except Exception as e:
                logger.warning(f"Error reading/parsing {base}: {e}")
                exif_meta = {}
            taken_at = _normalize_taken_at(exif_meta, google_meta=google_json)
            yield {
                "filename": Path(base).name,
                "source_uri": f"zip://{zip_path.name}::{base}",
                "file_size": entry.file_size,
                "mime_type": _mime_from_name(base),
                "exif": exif_meta,
                "google_json": google_json,
                "taken_at": taken_at,
            }
            count += 1
            if count % 10 == 0:
                logger.info(f"Streamed {count} images so far...")
            if limit is not None and count >= limit:
                logger.info(f"Reached limit of {limit} images")
                return
        logger.debug(f"ZIP {zip_path.name} yielded {image_count} images")
    logger.info(f"Stream complete: {count} images total")


async def _get_or_create_batch(session: AsyncSession, batch_id: Optional[str]) -> IngestStatus:
    if not batch_id:
        batch_id = f"batch-{uuid4()}"
    result = await session.execute(select(IngestStatus).where(IngestStatus.batch_id == batch_id))
    status = result.scalar_one_or_none()
    if status:
        return status
    status = IngestStatus(batch_id=batch_id, status="running", started_at=datetime.utcnow())
    session.add(status)
    await session.flush()
    return status


async def _process_single_photo(
    item: dict,
    batch_id: str,
    reprocess: bool,
) -> Tuple[bool, bool]:
    """Process a single photo metadata entry.

    Returns (was_processed, was_skipped) tuple.
    Uses its own database session for isolation.
    """
    async with AsyncSessionLocal() as session:
        try:
            # Upsert by source_uri for idempotency
            stmt = select(Photo).where(Photo.source_uri == item["source_uri"])
            existing = (await session.execute(stmt)).scalar_one_or_none()

            # Ensure all nested metadata is JSON-serializable for JSONB storage
            raw_metadata = {
                "exif": _make_json_serializable(item["exif"]),
                "google": _make_json_serializable(item["google_json"]),
            }

            photo_values = {
                "google_id": None,
                "filename": item["filename"],
                "file_size": item["file_size"],
                "mime_type": item["mime_type"],
                "taken_at": item["taken_at"],
                "raw_metadata": raw_metadata,
                "batch_id": batch_id,
                "source_uri": item["source_uri"],
            }

            if existing:
                if reprocess:
                    logger.debug(
                        f"Reprocessing {item['filename']} (source_uri={item['source_uri']})"
                    )
                    await session.execute(
                        update(Photo).where(Photo.id == existing.id).values(**photo_values)
                    )
                    await session.commit()
                    return True, False
                else:
                    logger.debug(f"Skipping {item['filename']} (already ingested)")
                    return False, True
            else:
                logger.info(
                    f"✓ {item['filename']} (size={item['file_size']}, taken={item['taken_at']})"
                )
                photo = Photo(**photo_values)
                session.add(photo)
                await session.commit()
                return True, False
        except Exception as exc:
            logger.error(f"Failed to process {item.get('filename')}: {exc}")
            return False, False


async def _update_batch_progress(batch_id: str, processed: int, skipped: int) -> None:
    """Update batch status progress counter."""
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(IngestStatus)
            .where(IngestStatus.batch_id == batch_id)
            .values(processed_files=processed, skipped_files=skipped)
        )
        await session.commit()


async def ingest_takeout_metadata(
    takeout_dir: Path,
    batch_id: Optional[str] = None,
    limit: int | None = None,
    reprocess: bool = False,
) -> Tuple[str, int]:
    """Process Takeout ZIPs and persist normalized metadata into the database.

    Processes photos asynchronously with controlled concurrency.
    Returns the number of processed images.
    """
    logger.info(
        f"Starting ingestion: takeout_dir={takeout_dir}, limit={limit}, reprocess={reprocess}"
    )

    # Create batch status record
    async with AsyncSessionLocal() as session:
        status = await _get_or_create_batch(session, batch_id)
        actual_batch_id: str = status.batch_id  # type: ignore[assignment]
        await session.commit()
        logger.info(f"Using batch_id={actual_batch_id}, status={status.status}")

    processed = 0
    skipped = 0
    semaphore = asyncio.Semaphore(10)  # Max 10 concurrent photo processors

    try:
        # Collect metadata items in batches for async processing
        batch = []
        batch_size = 20

        async for item in stream_zip_metadata(takeout_dir, limit=limit):
            batch.append(item)

            if len(batch) >= batch_size:
                # Process batch concurrently
                async def process_with_semaphore(photo_item: dict) -> Tuple[bool, bool]:
                    async with semaphore:
                        return await _process_single_photo(photo_item, actual_batch_id, reprocess)

                results = await asyncio.gather(
                    *[process_with_semaphore(photo) for photo in batch], return_exceptions=True
                )

                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Photo processing error: {result}")
                    elif isinstance(result, tuple):
                        was_processed, was_skipped = result
                        if was_processed:
                            processed += 1
                        if was_skipped:
                            skipped += 1

                # Update progress
                await _update_batch_progress(actual_batch_id, processed, skipped)
                logger.info(f"Progress: {processed} processed, {skipped} skipped")
                batch = []

        # Process remaining items
        if batch:

            async def process_with_semaphore(photo_item: dict) -> Tuple[bool, bool]:
                async with semaphore:
                    return await _process_single_photo(photo_item, actual_batch_id, reprocess)

            results = await asyncio.gather(
                *[process_with_semaphore(photo) for photo in batch], return_exceptions=True
            )

            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Photo processing error: {result}")
                elif isinstance(result, tuple):
                    was_processed, was_skipped = result
                    if was_processed:
                        processed += 1
                    if was_skipped:
                        skipped += 1

        # Mark batch as completed
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(IngestStatus)
                .where(IngestStatus.batch_id == actual_batch_id)
                .values(
                    processed_files=processed,
                    skipped_files=skipped,
                    status="completed",
                    completed_at=datetime.utcnow(),
                )
            )
            await session.commit()

        logger.info(
            f"Ingestion completed: batch_id={actual_batch_id}, processed={processed}, skipped={skipped}"
        )
        return actual_batch_id, processed

    except Exception as exc:
        logger.error(f"Ingestion failed: {exc}", exc_info=True)
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(IngestStatus)
                .where(IngestStatus.batch_id == actual_batch_id)
                .values(status="error", error_message=str(exc))
            )
            await session.commit()
        raise
