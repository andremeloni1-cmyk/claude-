"""Track which Drive photos have already been uploaded, in a committed JSON file.

Stored so re-runs never upload the same Drive photo twice. Photos are matched by
their Drive file id, so renaming a file in Drive won't cause a re-upload, but
re-uploading it to Drive (which mints a new id) will.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def load(path: Path) -> dict:
    if not path.exists():
        return {"uploaded": {}}
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    data.setdefault("uploaded", {})
    return data


def is_uploaded(state: dict, file_id: str) -> bool:
    return file_id in state["uploaded"]


def mark_uploaded(state: dict, file_id: str, file_name: str, slug: str) -> None:
    state["uploaded"][file_id] = {
        "file_name": file_name,
        "slug": slug,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }


def save(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
        fh.write("\n")
