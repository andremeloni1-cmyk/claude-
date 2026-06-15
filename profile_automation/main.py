"""Entry point: find new Drive photos, caption them, and bundle them for Framer.

Run with: python -m profile_automation.main

This is the content-generation half of the profile/portfolio pipeline. It finds
photos in the Drive folder it hasn't uploaded yet, asks Claude for a title and
alt text, resizes each for the web, and saves a bundle under
``published_profile/<slug>/``. The Framer publish step
(``framer/publish-profile.mjs``) then pushes those bundles into the Portfolio
collection.
"""

from __future__ import annotations

import hashlib
import logging
import re
import sys
from datetime import date

# Drive access and web image processing are utilities shared with the other
# automations.
from blog_automation import images
from pinterest_automation import drive

from . import bundle, captioner, config, state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("profile-automation")


def _slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:60]


def _slug_for(file_name: str, file_id: str) -> str:
    """A stable, unique slug for a Drive photo.

    Built from the filename plus a short hash of the (immutable) Drive file id,
    so the same photo always maps to the same Portfolio slug across runs (an
    existing slug is updated in place rather than duplicated), while photos that
    share a filename still get distinct slugs.
    """
    stem = file_name.rsplit(".", 1)[0] if "." in file_name else file_name
    base = _slugify(stem) or "photo"
    digest = hashlib.sha1(file_id.encode("utf-8")).hexdigest()[:6]
    return f"{base}-{digest}"


def run() -> int:
    cfg = config.load()
    st = state.load(cfg.state_path)

    drive_service = drive.build_service(cfg.google_service_account_json)
    drive_images = drive.list_images(drive_service, cfg.gdrive_folder_id)
    new_images = [img for img in drive_images if not state.is_uploaded(st, img["id"])]

    log.info(
        "Found %d photo(s) in Drive, %d new. Uploading up to %d this run.",
        len(drive_images),
        len(new_images),
        cfg.max_per_run,
    )
    if not new_images:
        log.info("Nothing new to upload. Done.")
        return 0

    uploaded = 0
    failures = 0
    for img in new_images[: cfg.max_per_run]:
        name = img["name"]
        try:
            log.info("Processing %s", name)
            raw_bytes = drive.download_image(drive_service, img["id"])
            copy = captioner.generate(cfg, images.for_analysis(raw_bytes), images.JPEG, name)

            slug = _slug_for(name, img["id"])
            date_iso = img.get("createdTime") or f"{date.today().isoformat()}T00:00:00.000Z"

            bundle.write(
                cfg.published_dir,
                slug=slug,
                title=copy["title"],
                alt_text=copy["alt_text"],
                category=cfg.category,
                date_iso=date_iso,
                image_data=images.for_web(raw_bytes),
                source_file_id=img["id"],
            )
            state.mark_uploaded(st, img["id"], name, slug)
            state.save(cfg.state_path, st)  # save after each so a crash never re-uploads
            uploaded += 1
            log.info("Bundled %r (slug: %s)", copy["title"], slug)
        except Exception as exc:  # noqa: BLE001 - keep going on a single bad photo
            failures += 1
            log.error("Failed to process %s: %s", name, exc)

    log.info("Run complete: %d bundled, %d failed.", uploaded, failures)
    return 1 if failures and uploaded == 0 else 0


if __name__ == "__main__":
    sys.exit(run())
