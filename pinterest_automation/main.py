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


def _resolve_board_id(cfg: config.Config) -> str:
    """Find the Pinterest board id Postiz needs for every pin.

    Prefer the explicit `pinterest_board_id` from config.yaml. Otherwise look it
    up with the read-only Pinterest token (boards:read works even on the trial
    tier — only write is gated), matching the configured board name, else the
    first board on the account.
    """
    if cfg.pinterest_board_id:
        return cfg.pinterest_board_id

    if not (cfg.pinterest_access_token or cfg.pinterest_refresh_token):
        raise config.ConfigError(
            "Postiz requires a Pinterest board id. Set 'pinterest_board_id' in "
            "config.yaml, or provide a read-only PINTEREST_ACCESS_TOKEN so the "
            "board can be looked up automatically by name."
        )

    boards = pinterest.PinterestClient(cfg.resolve_pinterest_token()).list_boards()
    if not boards:
        raise config.ConfigError(
            "No Pinterest boards found on this account. Create a board first, or "
            "set 'pinterest_board_id' in config.yaml."
        )
    target = cfg.board_name.strip().lower()
    for board in boards:
        if board.get("name", "").strip().lower() == target:
            return board["id"]
    log.warning(
        "No board named %r found; using first board %r instead.",
        cfg.board_name,
        boards[0].get("name"),
    )
    return boards[0]["id"]


def _build_poster(cfg: config.Config):
    """Return (post_fn, label). post_fn(copy, image_bytes, name) -> pin/post id."""
    link = _link_with_utm(cfg.website_url, cfg.utm)

    if cfg.use_postiz:
        client = postiz.PostizClient(cfg.postiz_api_key, base_url=cfg.postiz_base_url)
        integration_id = cfg.postiz_integration_id or client.find_pinterest_integration_id()
        board_id = _resolve_board_id(cfg)
        log.info("Posting to Pinterest board id %s.", board_id)

        def post(copy: dict, image_bytes: bytes, name: str) -> str:
            return client.post_pin(
                integration_id=integration_id,
                title=copy["title"],
                description=copy["description"],
                link=link,
                image_bytes=image_bytes,
                filename=_jpeg_name(name),
                board=board_id,
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
