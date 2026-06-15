"""Post pins to Pinterest via the Postiz public API.

Pinterest's own API gates the write scopes we need (``boards:write`` /
``pins:write``) behind a manual "Standard access" review. Postiz already holds
approved Pinterest write access, so we route posting through it instead: upload
the image, then create a Pinterest post on the connected Postiz channel.

Docs: https://docs.postiz.com/public-api
"""

from __future__ import annotations

import io
from datetime import datetime, timezone

import requests

DEFAULT_BASE_URL = "https://api.postiz.com/public/v1"
_TIMEOUT = 60
_TITLE_MAX = 100  # Pinterest pin title limit


class PostizError(RuntimeError):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


class PostizClient:
    """Thin client for the handful of Postiz endpoints we use."""

    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL):
        if not api_key:
            raise PostizError("Postiz API key is required.")
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self._session = requests.Session()
        # Postiz expects the key in Authorization with no "Bearer " prefix.
        self._session.headers.update({"Authorization": api_key})

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def list_integrations(self) -> list[dict]:
        resp = self._session.get(self._url("integrations"), timeout=_TIMEOUT)
        if resp.status_code >= 400:
            raise PostizError(
                f"Listing Postiz integrations failed ({resp.status_code}): {resp.text}"
            )
        data = resp.json()
        if isinstance(data, dict):  # some deployments wrap the list
            data = data.get("integrations") or data.get("data") or []
        return data if isinstance(data, list) else []

    def find_pinterest_integration_id(self) -> str:
        """Return the id of the connected Pinterest channel."""
        integrations = self.list_integrations()
        for item in integrations:
            identifier = (
                item.get("identifier")
                or item.get("provider")
                or item.get("providerIdentifier")
                or ""
            )
            if str(identifier).lower() == "pinterest":
                channel_id = item.get("id") or item.get("integrationId")
                if channel_id:
                    return str(channel_id)
        names = ", ".join(
            str(i.get("name") or i.get("identifier") or "?") for i in integrations
        ) or "(none)"
        raise PostizError(
            "No Pinterest channel is connected in Postiz. Connect your Pinterest "
            "account in the Postiz dashboard first. Channels found: " + names
        )

    def upload_image(
        self, image_bytes: bytes, filename: str, content_type: str = "image/jpeg"
    ) -> dict:
        files = {"file": (filename, io.BytesIO(image_bytes), content_type)}
        resp = self._session.post(self._url("upload"), files=files, timeout=_TIMEOUT)
        if resp.status_code >= 400:
            raise PostizError(f"Postiz upload failed ({resp.status_code}): {resp.text}")
        data = resp.json()
        if isinstance(data, list):
            data = data[0] if data else {}
        media_id = data.get("id")
        if not media_id:
            raise PostizError(f"Postiz upload response missing 'id': {data}")
        return {"id": str(media_id), "path": data.get("path")}

    def post_pin(
        self,
        *,
        integration_id: str,
        title: str,
        description: str,
        link: str,
        image_bytes: bytes,
        filename: str,
        board: str = "",
        content_type: str = "image/jpeg",
    ) -> str:
        """Upload the image and create a Pinterest pin. Returns a post id."""
        media = self.upload_image(image_bytes, filename, content_type)

        image_entry: dict = {"id": media["id"]}
        if media.get("path"):
            image_entry["path"] = media["path"]

        settings: dict = {"__type": "pinterest", "title": title[:_TITLE_MAX], "link": link}
        if board:
            settings["board"] = board

        body = {
            "type": "now",
            "date": _now_iso(),
            "shortLink": False,
            "tags": [],
            "posts": [
                {
                    "integration": {"id": integration_id},
                    "value": [{"content": description, "image": [image_entry]}],
                    "settings": settings,
                }
            ],
        }
        resp = self._session.post(self._url("posts"), json=body, timeout=_TIMEOUT)
        if resp.status_code >= 400:
            raise PostizError(f"Postiz create post failed ({resp.status_code}): {resp.text}")
        return _extract_post_id(resp.json() if resp.content else {})


def _extract_post_id(data) -> str:
    """Best-effort pull of an id out of Postiz's create-post response."""
    if isinstance(data, list):
        data = data[0] if data else {}
    if isinstance(data, dict):
        for key in ("id", "postId", "group", "groupId"):
            if data.get(key):
                return str(data[key])
        posts = data.get("posts")
        if isinstance(posts, list) and posts and isinstance(posts[0], dict):
            for key in ("id", "postId"):
                if posts[0].get(key):
                    return str(posts[0][key])
    return "posted"
