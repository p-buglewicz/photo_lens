from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

from worker.ingestion.metadata_ingest import ingest_takeout_metadata


async def main() -> None:
    parser = argparse.ArgumentParser(description="LensAnalytics ingestion worker (Phase 2)")
    parser.add_argument(
        "--takeout",
        type=Path,
        default=Path(os.getenv("TAKEOUT_PATH", "/media/pawel/Dysk/photos_backup")),
        help="Path to directory containing Google Takeout ZIP files",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of images to process (across all ZIPs)",
    )
    parser.add_argument(
        "--reprocess",
        action="store_true",
        help="Reprocess and overwrite existing records for matching source URIs",
    )
    args = parser.parse_args()

    takeout_dir: Path = args.takeout
    limit: int | None = args.limit

    if not takeout_dir.exists() or not takeout_dir.is_dir():
        raise SystemExit(f"Takeout path not found or not a directory: {takeout_dir}")

    batch_id, processed = await ingest_takeout_metadata(
        takeout_dir, batch_id=None, limit=limit, reprocess=args.reprocess
    )
    print(f"Processed {processed} images in batch {batch_id}.")


if __name__ == "__main__":
    asyncio.run(main())
