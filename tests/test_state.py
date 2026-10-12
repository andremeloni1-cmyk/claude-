"""Tests for the JSON state stores that guarantee idempotency:
- blog_automation/state.py   (never rewrite a topic / reuse a photo)
- pinterest_automation/state.py (never repost a Drive photo)

A regression in either silently double-publishes to live accounts, so these
cover the missing-file defaults, partial-file migration, dedup on mark, and the
save -> load round-trip.

Run with:
    cd /home/user/claude- && python3 -m pytest tests/test_state.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import blog_automation.state as blog_state  # noqa: E402
import pinterest_automation.state as pin_state  # noqa: E402


# ---------------------------------------------------------------------------
# blog_automation/state.py
# ---------------------------------------------------------------------------


def test_blog_load_missing_file_returns_empty_defaults(tmp_path):
    st = blog_state.load(tmp_path / "nope.json")
    assert st == {"done_keywords": [], "used_image_ids": [], "posts": {}}


def test_blog_load_backfills_missing_keys(tmp_path):
    path = tmp_path / "blog.json"
    path.write_text(json.dumps({"done_keywords": ["k"]}), encoding="utf-8")
    st = blog_state.load(path)
    assert st["done_keywords"] == ["k"]
    assert st["used_image_ids"] == []   # backfilled
    assert st["posts"] == {}            # backfilled


def test_blog_is_done_and_used_image_ids():
    st = {"done_keywords": ["a"], "used_image_ids": ["f1", "f2"], "posts": {}}
    assert blog_state.is_done(st, "a") is True
    assert blog_state.is_done(st, "b") is False
    assert blog_state.used_image_ids(st) == {"f1", "f2"}


def test_blog_mark_done_records_post_and_dedupes():
    st = {"done_keywords": ["a"], "used_image_ids": ["f1"], "posts": {}}
    blog_state.mark_done(st, "a", "slug-a", ["f1", "f2"])  # "a"/"f1" already present

    assert st["done_keywords"] == ["a"]            # not duplicated
    assert st["used_image_ids"] == ["f1", "f2"]    # f2 appended once
    assert st["posts"]["slug-a"]["keyword"] == "a"
    assert st["posts"]["slug-a"]["image_file_ids"] == ["f1", "f2"]
    assert "created_at" in st["posts"]["slug-a"]


def test_blog_save_then_load_round_trips(tmp_path):
    path = tmp_path / "sub" / "blog.json"  # parent dir does not exist yet
    st = {"done_keywords": ["a"], "used_image_ids": ["f1"], "posts": {"s": {"keyword": "a"}}}
    blog_state.save(path, st)
    assert path.exists()
    assert blog_state.load(path) == st


# ---------------------------------------------------------------------------
# pinterest_automation/state.py
# ---------------------------------------------------------------------------


def test_pin_load_missing_file_returns_empty_defaults(tmp_path):
    assert pin_state.load(tmp_path / "nope.json") == {"posted": {}}


def test_pin_load_backfills_posted_key(tmp_path):
    path = tmp_path / "posted.json"
    path.write_text(json.dumps({}), encoding="utf-8")
    assert pin_state.load(path) == {"posted": {}}


def test_pin_is_posted_and_mark_posted():
    st = {"posted": {}}
    assert pin_state.is_posted(st, "file-1") is False
    pin_state.mark_posted(st, "file-1", "photo.jpg", "pin-99")
    assert pin_state.is_posted(st, "file-1") is True
    entry = st["posted"]["file-1"]
    assert entry["file_name"] == "photo.jpg"
    assert entry["pin_id"] == "pin-99"
    assert "posted_at" in entry


def test_pin_save_then_load_round_trips(tmp_path):
    path = tmp_path / "nested" / "posted.json"
    st = {"posted": {"file-1": {"file_name": "p.jpg", "pin_id": "x", "posted_at": "t"}}}
    pin_state.save(path, st)
    assert pin_state.load(path) == st


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
