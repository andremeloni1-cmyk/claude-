"""Entry point: find new Drive photos, write SEO copy, post pins to Pinterest.

Run with: python -m pinterest_automation.main
"""

from __future__ import annotations

import logging
import sys
from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl

from . import captions, config, drive, images, pinterest, postiz, state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("pinterest-automation")


def _link_with_utm(url: str, utm: dict) -> str:
    if not utm:
        return url
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query))
    query.update({f"utm_{k}": v for k, v in utm.items()})
    return urlunparse(parsed._replace(query=urlencode(query)))


def _jpeg_name(name: str) -> str:
    """Filenames sent to the uploader should match the JPEG bytes we encode."""
    stem = name.rsplit(".", 1)[0] if "." in name else name
    return f"{stem}.jpg"


def _build_poster(cfg: config.Config):
    """Return (post_fn, label). post_fn(copy, image_bytes, name) -> pin/post id."""
    link = _link_with_utm(cfg.website_url, cfg.utm)

    if cfg.use_postiz:
        client = postiz.PostizClient(cfg.postiz_api_key, base_url=cfg.postiz_base_url)
        integration_id = cfg.postiz_integration_id or client.find_pinterest_integration_id()

        def post(copy: dict, image_bytes: bytes, name: str) -> str:
            return client.post_pin(
                integration_id=integration_id,
                title=copy["title"],
                description=copy["description"],
                link=link,
                image_bytes=image_bytes,
                filename=_jpeg_name(name),
                board=cfg.pinterest_board_id,
                content_type=images.JPEG,
            )

        return post, "Postiz"

    pin_client = pinterest.PinterestClient(cfg.resolve_pinterest_token())
    board_id = pin_client.get_or_create_board(cfg.board_name, cfg.board_description)

    def post(copy: dict, image_bytes: bytes, name: str) -> str:
        return pin_client.create_pin(
            board_id=board_id,
            title=copy["title"],
            description=copy["description"],
            link=link,
            alt_text=copy["alt_text"],
            image_bytes=image_bytes,
            content_type=images.JPEG,
        )

    return post, "Pinterest API"


def run() -> int:
    cfg = config.load()
    st = state.load(cfg.state_path)

    drive_service = drive.build_service(cfg.google_service_account_json)
    drive_images = drive.list_images(drive_service, cfg.gdrive_folder_id)
    new_images = [img for img in drive_images if not state.is_posted(st, img["id"])]

    log.info(
        "Found %d photo(s) in Drive, %d new. Posting up to %d this run.",
        len(drive_images),
        len(new_images),
        cfg.max_pins_per_run,
    )
    if not new_images:
        log.info("Nothing new to post. Done.")
        return 0

    post, backend = _build_poster(cfg)
    log.info("Posting via %s.", backend)

    posted = 0
    failures = 0
    for img in new_images[: cfg.max_pins_per_run]:
        name = img["name"]
        try:
            log.info("Processing %s", name)
            raw_bytes = drive.download_image(drive_service, img["id"])
            copy = captions.generate(cfg, images.for_analysis(raw_bytes), images.JPEG, name)
            pin_id = post(copy, images.for_pin(raw_bytes), name)
            state.mark_posted(st, img["id"], name, pin_id)
            state.save(cfg.state_path, st)  # save after each so a crash never re-posts
            posted += 1
            log.info("Posted pin %s for %s", pin_id, name)
        except Exception as exc:  # noqa: BLE001 - keep going on a single bad photo
            failures += 1
            log.error("Failed to post %s: %s", name, exc)

    log.info("Run complete: %d posted, %d failed.", posted, failures)
    return 1 if failures and posted == 0 else 0


if __name__ == "__main__":
    sys.exit(run())
