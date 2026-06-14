"""Minimal client for the Pinterest API v5 (boards + pin creation)."""

from __future__ import annotations

import base64

import requests

_API = "https://api.pinterest.com/v5"
_TIMEOUT = 60


class PinterestError(RuntimeError):
    pass


class PinterestClient:
    def __init__(self, access_token: str):
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
        )

    def _request(self, method: str, path: str, **kwargs) -> dict:
        resp = self._session.request(method, f"{_API}{path}", timeout=_TIMEOUT, **kwargs)
        if resp.status_code >= 400:
            raise PinterestError(
                f"Pinterest {method} {path} -> {resp.status_code}: {resp.text}"
            )
        return resp.json() if resp.content else {}

    def list_boards(self) -> list[dict]:
        boards: list[dict] = []
        bookmark = None
        while True:
            params = {"page_size": 100}
            if bookmark:
                params["bookmark"] = bookmark
            data = self._request("GET", "/boards", params=params)
            boards.extend(data.get("items", []))
            bookmark = data.get("bookmark")
            if not bookmark:
                break
        return boards

    def get_or_create_board(self, name: str, description: str = "") -> str:
        for board in self.list_boards():
            if board.get("name", "").strip().lower() == name.strip().lower():
                return board["id"]
        created = self._request(
            "POST",
            "/boards",
            json={"name": name, "description": description, "privacy": "PUBLIC"},
        )
        return created["id"]

    def create_pin(
        self,
        *,
        board_id: str,
        title: str,
        description: str,
        link: str,
        alt_text: str,
        image_bytes: bytes,
        content_type: str,
    ) -> str:
        body = {
            "board_id": board_id,
            "title": title,
            "description": description,
            "link": link,
            "alt_text": alt_text,
            "media_source": {
                "source_type": "image_base64",
                "content_type": content_type,
                "data": base64.standard_b64encode(image_bytes).decode("utf-8"),
            },
        }
        created = self._request("POST", "/pins", json=body)
        return created["id"]
