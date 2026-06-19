"""Minimal client for the Etsy Open API v3 (listing creation + uploads)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import requests

_API = "https://openapi.etsy.com/v3/application"
_TIMEOUT = 60


class EtsyError(RuntimeError):
    pass


class EtsyClient:
    def __init__(self, api_key: str, shared_secret: str, access_token: str = ""):
        self._session = requests.Session()
        self._session.headers.update({"x-api-key": f"{api_key}:{shared_secret}"})
        if access_token:
            self._session.headers.update({"Authorization": f"Bearer {access_token}"})

    def _request(self, method: str, path: str, **kwargs) -> dict:
        resp = self._session.request(method, f"{_API}{path}", timeout=_TIMEOUT, **kwargs)
        if resp.status_code >= 400:
            raise EtsyError(f"Etsy {method} {path} -> {resp.status_code}: {resp.text}")
        return resp.json() if resp.content else {}

    # ---- Listing creation (requires OAuth, scope listings_w) --------------

    def create_draft_listing(self, shop_id: int, **fields: Any) -> dict:
        """POST /shops/{shop_id}/listings. Always creates the listing as a draft."""
        return self._request("POST", f"/shops/{shop_id}/listings", data=fields)

    def upload_listing_image(
        self,
        shop_id: int,
        listing_id: int,
        image_path: Path,
        *,
        rank: int | None = None,
        alt_text: str = "",
    ) -> dict:
        data: dict[str, Any] = {}
        if rank is not None:
            data["rank"] = rank
        if alt_text:
            data["alt_text"] = alt_text[:500]
        with image_path.open("rb") as fh:
            return self._request(
                "POST",
                f"/shops/{shop_id}/listings/{listing_id}/images",
                data=data,
                files={"image": (image_path.name, fh)},
            )

    def upload_listing_file(
        self,
        shop_id: int,
        listing_id: int,
        file_path: Path,
        *,
        rank: int | None = None,
    ) -> dict:
        data: dict[str, Any] = {"name": file_path.name}
        if rank is not None:
            data["rank"] = rank
        with file_path.open("rb") as fh:
            return self._request(
                "POST",
                f"/shops/{shop_id}/listings/{listing_id}/files",
                data=data,
                files={"file": (file_path.name, fh)},
            )

    def update_listing(self, shop_id: int, listing_id: int, **fields: Any) -> dict:
        """PATCH /shops/{shop_id}/listings/{listing_id}. Pass state="active" to publish."""
        return self._request(
            "PATCH", f"/shops/{shop_id}/listings/{listing_id}", data=fields
        )

    def get_listing(self, listing_id: int) -> dict:
        return self._request("GET", f"/listings/{listing_id}")

    # ---- Lookups ------------------------------------------------------------
    # These are read-only catalogue endpoints. Etsy's reference lists no OAuth
    # scope for them, but every request (including these) still needs an
    # *approved* x-api-key — so they won't work until your app is approved
    # either, even though no user authorization is required.

    def get_seller_taxonomy_nodes(self) -> list[dict]:
        data = self._request("GET", "/seller-taxonomy/nodes")
        return data.get("results", [])

    def find_shops(self, shop_name: str) -> list[dict]:
        data = self._request("GET", "/shops", params={"shop_name": shop_name})
        return data.get("results", [])

    def get_shop(self, shop_id: int) -> dict:
        return self._request("GET", f"/shops/{shop_id}")


def search_taxonomy_nodes(nodes: list[dict], query: str) -> list[dict]:
    """Flatten the nested taxonomy tree and return nodes whose name matches query."""
    query = query.lower()
    found = []
    stack = list(nodes)
    while stack:
        node = stack.pop()
        if query in node.get("name", "").lower():
            found.append(node)
        stack.extend(node.get("children") or [])
    return found
