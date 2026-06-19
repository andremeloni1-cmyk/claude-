"""CLI used by the etsy-automation skill to create and publish Etsy listings.

Listings are always created as drafts. Publishing (state=active) is a
separate, explicit step (`activate`) so nothing goes live without a
deliberate command.

Usage:
    python create_listing.py create <spec.json>
    python create_listing.py activate <listing_id>
    python create_listing.py taxonomy <query>

spec.json holds the fields for create_draft_listing (title, description,
price, quantity, who_made, when_made, taxonomy_id, type, tags, materials,
...) plus two extra arrays consumed by this script and stripped before the
API call:

    "images": ["/abs/path/to/photo1.jpg", ...]
    "files":  ["/abs/path/to/download.pdf", ...]
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from etsy_auth import EtsyAuthError, refresh_access_token  # noqa: E402
from etsy_client import EtsyClient, EtsyError, search_taxonomy_nodes  # noqa: E402


class CliError(RuntimeError):
    pass


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise CliError(f"Missing required environment variable {name!r}.")
    return value


def _client() -> tuple[EtsyClient, int]:
    api_key = _require_env("ETSY_API_KEY")
    shared_secret = _require_env("ETSY_SHARED_SECRET")
    shop_id = int(_require_env("ETSY_SHOP_ID"))

    refresh_token = os.environ.get("ETSY_REFRESH_TOKEN", "").strip()
    access_token = os.environ.get("ETSY_ACCESS_TOKEN", "").strip()

    if refresh_token:
        try:
            access_token, new_refresh_token = refresh_access_token(api_key, refresh_token)
        except EtsyAuthError as exc:
            raise CliError(str(exc)) from exc
        if new_refresh_token != refresh_token:
            print(
                "NOTE: Etsy rotated the refresh token. Update the "
                f"ETSY_REFRESH_TOKEN secret to:\n{new_refresh_token}",
                file=sys.stderr,
            )
    elif not access_token:
        raise CliError(
            "Missing Etsy auth: set ETSY_REFRESH_TOKEN (preferred, auto-renews) "
            "or ETSY_ACCESS_TOKEN."
        )

    return EtsyClient(api_key, shared_secret, access_token), shop_id


def create(spec_path: Path) -> dict:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    images = spec.pop("images", [])
    files = spec.pop("files", [])

    client, shop_id = _client()
    listing = client.create_draft_listing(shop_id, **spec)
    listing_id = listing["listing_id"]

    for rank, image_path in enumerate(images, start=1):
        client.upload_listing_image(shop_id, listing_id, Path(image_path), rank=rank)

    for rank, file_path in enumerate(files, start=1):
        client.upload_listing_file(shop_id, listing_id, Path(file_path), rank=rank)

    result = {
        "listing_id": listing_id,
        "state": listing.get("state", "draft"),
        "url": listing.get("url", ""),
        "images_uploaded": len(images),
        "files_uploaded": len(files),
    }
    print(json.dumps(result, indent=2))
    return result


def activate(listing_id: int) -> dict:
    client, shop_id = _client()
    listing = client.update_listing(shop_id, listing_id, state="active")
    result = {
        "listing_id": listing["listing_id"],
        "state": listing["state"],
        "url": listing.get("url", ""),
    }
    print(json.dumps(result, indent=2))
    return result


def taxonomy(query: str) -> list[dict]:
    client, _shop_id = _client()
    nodes = client.get_seller_taxonomy_nodes()
    matches = search_taxonomy_nodes(nodes, query)
    result = [{"id": node["id"], "name": node["name"]} for node in matches]
    print(json.dumps(result, indent=2))
    return result


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1

    command, *rest = argv[1:]
    try:
        if command == "create":
            if not rest:
                raise CliError("Usage: create_listing.py create <spec.json>")
            create(Path(rest[0]))
        elif command == "activate":
            if not rest:
                raise CliError("Usage: create_listing.py activate <listing_id>")
            activate(int(rest[0]))
        elif command == "taxonomy":
            if not rest:
                raise CliError("Usage: create_listing.py taxonomy <query>")
            taxonomy(" ".join(rest))
        else:
            raise CliError(f"Unknown command {command!r}. Use create, activate, or taxonomy.")
    except (CliError, EtsyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
