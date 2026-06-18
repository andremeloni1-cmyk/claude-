"""Track which topics have been written and which photos have been used.

Stored in a committed JSON file so re-runs never rewrite the same topic or
(by default) reuse the same photo across posts.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def load(path: Path) -> dict:
    if not path.exists():
        return {"done_keywords": [], "used_image_ids": [], "posts": {}}
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    data.setdefault("done_keywords", [])
    data.setdefault("used_image_ids", [])
    data.setdefault("posts", {})
    return data


def is_done(state: dict, keyword: str) -> bool:
    return keyword in state["done_keywords"]


def used_image_ids(state: dict) -> set[str]:
    return set(state["used_image_ids"])


def mark_done(state: dict, keyword: str, slug: str, image_file_ids: list[str]) -> None:
    if keyword not in state["done_keywords"]:
        state["done_keywords"].append(keyword)
    for fid in image_file_ids:
        if fid not in state["used_image_ids"]:
            state["used_image_ids"].append(fid)
    state["posts"][slug] = {
        "keyword": keyword,
        "image_file_ids": image_file_ids,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def save(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
        fh.write("\n")
