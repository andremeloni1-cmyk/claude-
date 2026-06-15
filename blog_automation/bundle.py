"""Write a finished post + its images to ``published/<slug>/`` for the Framer step.

Each bundle is self-contained: a ``post.json`` describing the CMS fields plus
the processed JPEGs. The Node publisher (``framer/publish.mjs``) reads every
bundle, turns the relative image paths into hosted URLs, and pushes the post
into the Framer CMS.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path


def write(published_dir: Path, post: dict, images: list[dict], author: str) -> Path:
    """Write one bundle. ``images`` is a list of {data: bytes, alt_text: str},
    cover first. Returns the bundle directory.
    """
    slug = post["slug"]
    bundle_dir = published_dir / slug
    images_dir = bundle_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    image_entries = []
    for i, img in enumerate(images, start=1):
        filename = f"image-{i:02d}.jpg"
        (images_dir / filename).write_bytes(img["data"])
        image_entries.append(
            {
                "path": f"images/{filename}",  # relative to the bundle dir
                "alt": img["alt_text"],
                "is_cover": i == 1,
            }
        )

    manifest = {
        "slug": slug,
        "fields": {
            "title": post["title"],
            "intro_1": post["intro_1"],
            "intro_2": post["intro_2"],
            "meta_title": post["meta_title"],
            "meta_description": post["meta_description"],
            "excerpt": post["excerpt"],
            "category": post["category"],
            "author": author,
            "keywords": ", ".join(post["keywords"]),
            "date": date.today().isoformat(),
        },
        # body_markdown keeps {{image_N}} placeholders; the publisher swaps them
        # for hosted images so the photos appear inline in the article.
        "body_markdown": post["body_markdown"],
        "images": image_entries,
    }

    with (bundle_dir / "post.json").open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    return bundle_dir
