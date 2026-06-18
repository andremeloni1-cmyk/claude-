"""Entry point: write SEO posts for the next topics and bundle them for Framer.

Run with: python -m blog_automation.main

This is the content-generation half of the pipeline. It picks the next
unwritten topic(s), chooses matching photos from Drive, writes a full SEO post,
and saves a bundle under ``published/<slug>/``. The Framer publish step
(framer/publish.mjs) then pushes those bundles into the CMS.
"""

from __future__ import annotations

import logging
import random
import sys

# Drive access is a pure utility shared with the Pinterest automation.
from pinterest_automation import drive

from . import bundle, config, images, state, writer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("blog-automation")


def _pick_candidates(cfg, drive_service, drive_images, used_ids):
    """Download + shrink a pool of candidate photos for image selection."""
    pool = [img for img in drive_images if img["id"] not in used_ids]
    if cfg.avoid_reusing_images and not pool:
        log.info("All photos already used; allowing reuse for this post.")
    if not cfg.avoid_reusing_images or not pool:
        pool = list(drive_images)

    random.shuffle(pool)
    pool = pool[: cfg.image_candidate_pool]

    candidates = []
    for img in pool:
        try:
            raw = drive.download_image(drive_service, img["id"])
            candidates.append(
                {
                    "file_id": img["id"],
                    "name": img["name"],
                    "analysis_bytes": images.for_analysis(raw),
                }
            )
        except Exception as exc:  # noqa: BLE001 - skip a single unreadable file
            log.warning("Skipping candidate %s: %s", img["name"], exc)
    return candidates


def _build_post(cfg, drive_service, drive_images, used_ids, topic) -> list[str]:
    """Write one post for ``topic`` and save its bundle. Returns image file ids used."""
    candidates = _pick_candidates(cfg, drive_service, drive_images, used_ids)
    chosen = writer.select_images(cfg, topic, candidates) if candidates else []
    log.info("Selected %d photo(s) for %r", len(chosen), topic.keyword)

    alts = [c["alt_text"] for c in chosen]
    post = writer.write_post(cfg, topic, alts)
    log.info("Wrote post %r (slug: %s)", post["title"], post["slug"])

    image_payload = []
    for c in chosen:
        raw = drive.download_image(drive_service, c["file_id"])
        image_payload.append({"data": images.for_web(raw), "alt_text": c["alt_text"]})

    bundle.write(cfg.published_dir, post, image_payload, cfg.author)
    log.info("Saved bundle published/%s", post["slug"])

    return post["slug"], [c["file_id"] for c in chosen]


def run() -> int:
    cfg = config.load()
    st = state.load(cfg.state_path)

    pending = [t for t in cfg.topics if not state.is_done(st, t.keyword)]
    log.info(
        "%d topic(s) configured, %d pending. Writing up to %d this run.",
        len(cfg.topics),
        len(pending),
        cfg.max_posts_per_run,
    )
    if not pending:
        log.info("No pending topics. Add more under blog.topics in config.yaml. Done.")
        return 0

    drive_service = drive.build_service(cfg.google_service_account_json)
    drive_images = drive.list_images(drive_service, cfg.gdrive_folder_id)
    log.info("Found %d photo(s) in Drive.", len(drive_images))

    written = 0
    failures = 0
    for topic in pending[: cfg.max_posts_per_run]:
        try:
            used_ids = state.used_image_ids(st)
            slug, image_ids = _build_post(cfg, drive_service, drive_images, used_ids, topic)
            state.mark_done(st, topic.keyword, slug, image_ids)
            state.save(cfg.state_path, st)  # save after each so a crash never re-writes
            written += 1
        except Exception as exc:  # noqa: BLE001 - keep going on a single bad topic
            failures += 1
            log.error("Failed to write post for %r: %s", topic.keyword, exc)

    log.info("Run complete: %d written, %d failed.", written, failures)
    return 1 if failures and written == 0 else 0


if __name__ == "__main__":
    sys.exit(run())
