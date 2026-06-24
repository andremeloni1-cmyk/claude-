"""Tests for blog_automation/bundle.py::write().

The on-disk bundle (post.json + images/) is the contract the Node publisher
(framer/publish.mjs) reads, so this pins the filename scheme, the cover flag,
and the field mapping.

Run with:
    cd /home/user/claude- && python3 -m pytest tests/test_bundle.py -v
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import blog_automation.bundle as bundle  # noqa: E402


def _post(**overrides):
    post = {
        "slug": "best-wedding-photos",
        "title": "Best Wedding Photos",
        "intro_1": "i1",
        "intro_2": "i2",
        "meta_title": "mt",
        "meta_description": "md",
        "excerpt": "ex",
        "category": "Tips",
        "keywords": ["a", "b", "c"],
        "body_markdown": "## Section\n{{image_3}}",
    }
    post.update(overrides)
    return post


def _images(n: int) -> list[dict]:
    return [{"data": bytes([i]), "alt_text": f"alt {i}"} for i in range(n)]


def test_write_creates_bundle_dir_and_returns_it(tmp_path):
    out = bundle.write(tmp_path, _post(), _images(2), author="Andre")
    assert out == tmp_path / "best-wedding-photos"
    assert (out / "post.json").exists()
    assert (out / "images").is_dir()


def test_write_names_images_zero_padded_and_writes_bytes(tmp_path):
    out = bundle.write(tmp_path, _post(), _images(3), author="Andre")
    files = sorted(p.name for p in (out / "images").iterdir())
    assert files == ["image-01.jpg", "image-02.jpg", "image-03.jpg"]
    assert (out / "images" / "image-01.jpg").read_bytes() == bytes([0])


def test_write_marks_only_first_image_as_cover(tmp_path):
    out = bundle.write(tmp_path, _post(), _images(3), author="Andre")
    manifest = json.loads((out / "post.json").read_text(encoding="utf-8"))
    covers = [img["is_cover"] for img in manifest["images"]]
    assert covers == [True, False, False]
    assert manifest["images"][0]["path"] == "images/image-01.jpg"
    assert manifest["images"][0]["alt"] == "alt 0"


def test_write_maps_fields_and_joins_keywords(tmp_path):
    out = bundle.write(tmp_path, _post(), _images(1), author="Andre Meloni")
    manifest = json.loads((out / "post.json").read_text(encoding="utf-8"))
    fields = manifest["fields"]
    assert fields["title"] == "Best Wedding Photos"
    assert fields["author"] == "Andre Meloni"
    assert fields["keywords"] == "a, b, c"          # list -> comma-joined string
    assert fields["date"] == date.today().isoformat()
    # body keeps its placeholders for the publisher to swap.
    assert manifest["body_markdown"] == "## Section\n{{image_3}}"


def test_write_handles_zero_images(tmp_path):
    out = bundle.write(tmp_path, _post(), [], author="Andre")
    manifest = json.loads((out / "post.json").read_text(encoding="utf-8"))
    assert manifest["images"] == []
    assert (out / "images").is_dir()


def test_post_json_ends_with_trailing_newline(tmp_path):
    out = bundle.write(tmp_path, _post(), _images(1), author="Andre")
    assert (out / "post.json").read_text(encoding="utf-8").endswith("}\n")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
