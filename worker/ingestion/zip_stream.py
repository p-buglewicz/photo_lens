from __future__ import annotations

import asyncio
import zipfile
from pathlib import Path
from typing import AsyncIterator, Iterable

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".webp", ".tif", ".tiff"}


def _iter_zip_image_names(zip_path: Path) -> Iterable[str]:
    """Yield image file names from a Takeout ZIP without extracting.

    Returns the base filename (not the full path inside the ZIP) for each image-like member.
    """
    # Use the standard library; no extraction to disk, just metadata iteration
    with zipfile.ZipFile(zip_path, mode="r") as zf:
        for info in zf.infolist():
            # Skip directories
            if info.is_dir():
                continue

            name = Path(info.filename)
            if name.suffix.lower() in IMAGE_EXTS:
                yield name.name


async def iter_takeout_zip_images(
    takeout_dir: Path,
    limit: int | None = None,
    recursive: bool = True,
) -> AsyncIterator[str]:
    """Async generator that streams image names from Takeout ZIPs.

    - Iterates ZIP files in the provided directory (non-recursive).
    - Streams entries without extracting; yields base filenames only.
    - Stops after yielding `limit` items when provided.
    """
    count = 0
    # Discover ZIPs (optionally recursively). Sort for deterministic order.
    zip_iter = takeout_dir.rglob("*.zip") if recursive else takeout_dir.glob("*.zip")
    for zip_path in sorted(zip_iter):
        # Move potentially blocking ZIP I/O to a worker thread
        names = await asyncio.to_thread(lambda: list(_iter_zip_image_names(zip_path)))
        for name in names:
            yield name
            count += 1
            if limit is not None and count >= limit:
                return
