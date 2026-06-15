"""Write one uploaded photo + its CMS fields to ``published_profile/<slug>/``.

Each bundle is self-contained: a ``post.json`` describing the Portfolio item's
fields plus the processed JPEG. The Node publisher (``framer/publish-profile.mjs``)
reads every bundle, turns the relative image path into a hosted URL, and pushes
the item into the Framer Portfolio collection.
"""

from __future__ import annotations

import json
from pathlib import Path


def write(
    published_dir: Path,
    slug: str,
    title: str,
    alt_text: str,
    category: str,
    date_iso: str,
    image_data: bytes,
    source_file_id: str,
) -> Path:
    """Write one bundle. Returns the bundle directory."""
    bundle_dir = published_dir / slug
    images_dir = bundle_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    filename = "image-01.jpg"
    (images_dir / filename).write_bytes(image_data)

    manifest = {
        "slug": slug,
        "fields": {
            "title": title,
            "alt_text": alt_text,
            "category": category,
            "date": date_iso,
        },
        "image": {
            "path": f"images/{filename}",  # relative to the bundle dir
            "alt": alt_text,
        },
        # Kept for traceability back to the source Drive file.
        "source_file_id": source_file_id,
    }

    with (bundle_dir / "post.json").open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    return bundle_dir
