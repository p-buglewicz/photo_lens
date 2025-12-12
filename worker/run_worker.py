from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

from worker.ingestion.zip_stream import iter_takeout_zip_images


async def main() -> None:
    parser = argparse.ArgumentParser(description="LensAnalytics minimal ingestion worker")
    parser.add_argument(
        "--takeout",
        type=Path,
        default=Path(os.getenv("TAKEOUT_PATH", "/media/pawel/Dysk/photos_backup")),
        help="Path to directory containing Google Takeout ZIP files",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Maximum number of image names to print (across all ZIPs)",
    )
    args = parser.parse_args()

    takeout_dir: Path = args.takeout
    limit: int | None = args.limit

    if not takeout_dir.exists() or not takeout_dir.is_dir():
        raise SystemExit(f"Takeout path not found or not a directory: {takeout_dir}")

    printed = 0
    async for name in iter_takeout_zip_images(takeout_dir, limit=limit):
        print(name)
        printed += 1

    if printed == 0:
        print("No images found in ZIPs. Ensure Takeout ZIPs exist in the directory.")


if __name__ == "__main__":
    asyncio.run(main())
