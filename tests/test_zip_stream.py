import zipfile
from pathlib import Path

import pytest

from worker.ingestion.zip_stream import iter_takeout_zip_images


def _make_zip(dir_path: Path, name: str, files: dict[str, bytes]) -> Path:
    zpath = dir_path / name
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for arcname, data in files.items():
            zf.writestr(arcname, data)
    return zpath


@pytest.mark.asyncio
async def test_iter_takeout_zip_images_filters_and_collects(tmp_path: Path):
    # Prepare one zip with images and non-images
    _make_zip(
        tmp_path,
        "takeout-001.zip",
        {
            "Google Photos/IMG_0001.jpg": b"jpg-bytes",
            "Google Photos/IMG_0002.jpeg": b"jpeg-bytes",
            "Google Photos/IMG_0003.HEIC": b"heic-bytes",
            "Google Photos/IMG_0004.txt": b"not-an-image",
            "notes/readme.md": b"docs",
        },
    )

    # And a second zip
    _make_zip(
        tmp_path,
        "takeout-002.zip",
        {
            "folder/NESTED/shot.webp": b"webp",
            "folder/NESTED/shot2.tiff": b"tiff",
            "folder/NESTED/ignore.json": b"{}",
        },
    )

    results = [name async for name in iter_takeout_zip_images(tmp_path)]
    # Base names only should be returned
    assert set(results) == {
        "IMG_0001.jpg",
        "IMG_0002.jpeg",
        "IMG_0003.HEIC",
        "shot.webp",
        "shot2.tiff",
    }


@pytest.mark.asyncio
async def test_iter_takeout_zip_images_respects_limit(tmp_path: Path):
    _make_zip(
        tmp_path,
        "takeout-001.zip",
        {f"Google Photos/img_{i}.jpg": b"x" for i in range(10)},
    )

    results = [name async for name in iter_takeout_zip_images(tmp_path, limit=3)]
    assert len(results) == 3


@pytest.mark.asyncio
async def test_iter_takeout_zip_images_empty_zip(tmp_path: Path):
    _make_zip(tmp_path, "empty.zip", {})
    results = [name async for name in iter_takeout_zip_images(tmp_path)]
    assert results == []


@pytest.mark.asyncio
async def test_iter_takeout_zip_images_discovers_nested_zip_files(tmp_path: Path):
    nested = tmp_path / "nested" / "deeper"
    nested.mkdir(parents=True)

    # Create a zip only in a nested directory
    _make_zip(
        nested,
        "deep.zip",
        {"Google Photos/NEST/a.jpg": b"x", "Google Photos/NEST/b.png": b"y"},
    )

    # With recursive=True (default), nested zips should be found
    results = [name async for name in iter_takeout_zip_images(tmp_path)]
    assert set(results) == {"a.jpg", "b.png"}

    # With recursive=False, nothing should be found at top-level
    results_nonrec = [name async for name in iter_takeout_zip_images(tmp_path, recursive=False)]
    assert results_nonrec == []
