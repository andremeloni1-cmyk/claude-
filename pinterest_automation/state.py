"""Track which Drive photos have already been posted, in a committed JSON file."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def load(path: Path) -> dict:
    if not path.exists():
        return {"posted": {}}
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    data.setdefault("posted", {})
    return data


def is_posted(state: dict, file_id: str) -> bool:
    return file_id in state["posted"]


def mark_posted(state: dict, file_id: str, file_name: str, pin_id: str) -> None:
    state["posted"][file_id] = {
        "file_name": file_name,
        "pin_id": pin_id,
        "posted_at": datetime.now(timezone.utc).isoformat(),
    }


def save(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
        fh.write("\n")
