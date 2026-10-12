"""Tests for the pure helpers across pinterest_automation/ (no network).

- main._link_with_utm / main._jpeg_name
- drive._parse_service_account (raw JSON / base64 / invalid)
- postiz._extract_post_id (response-shape tolerance)
- captions._clamp

Run with:
    cd /home/user/claude- && python3 -m pytest tests/test_pinterest_pure.py -v
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import pinterest_automation.main as pin_main  # noqa: E402
import pinterest_automation.drive as drive  # noqa: E402
import pinterest_automation.postiz as postiz  # noqa: E402
import pinterest_automation.captions as captions  # noqa: E402


# ---------------------------------------------------------------------------
# main._link_with_utm
# ---------------------------------------------------------------------------


def test_link_with_utm_returns_url_unchanged_when_no_utm():
    assert pin_main._link_with_utm("https://x.com/p", {}) == "https://x.com/p"


def test_link_with_utm_appends_prefixed_params():
    out = pin_main._link_with_utm("https://x.com/p", {"source": "pinterest", "medium": "social"})
    q = parse_qs(urlparse(out).query)
    assert q["utm_source"] == ["pinterest"]
    assert q["utm_medium"] == ["social"]


def test_link_with_utm_preserves_existing_query_params():
    out = pin_main._link_with_utm("https://x.com/p?ref=abc", {"source": "pinterest"})
    q = parse_qs(urlparse(out).query)
    assert q["ref"] == ["abc"]
    assert q["utm_source"] == ["pinterest"]


# ---------------------------------------------------------------------------
# main._jpeg_name
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name,expected",
    [
        ("photo.png", "photo.jpg"),
        ("photo.jpeg", "photo.jpg"),
        ("no-extension", "no-extension.jpg"),
        ("dotted.name.heic", "dotted.name.jpg"),
    ],
)
def test_jpeg_name(name, expected):
    assert pin_main._jpeg_name(name) == expected


# ---------------------------------------------------------------------------
# drive._parse_service_account
# ---------------------------------------------------------------------------


def test_parse_service_account_accepts_raw_json():
    info = {"type": "service_account", "project_id": "p"}
    assert drive._parse_service_account(json.dumps(info)) == info


def test_parse_service_account_accepts_base64_json():
    info = {"type": "service_account", "project_id": "p"}
    blob = base64.b64encode(json.dumps(info).encode()).decode()
    assert drive._parse_service_account(blob) == info


def test_parse_service_account_rejects_garbage():
    with pytest.raises(ValueError):
        drive._parse_service_account("not json and not base64 !!!")


# ---------------------------------------------------------------------------
# postiz._extract_post_id
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "data,expected",
    [
        ({"id": "123"}, "123"),
        ({"postId": "p1"}, "p1"),
        ({"group": "g1"}, "g1"),
        ([{"id": "first"}], "first"),
        ({"posts": [{"id": "nested"}]}, "nested"),
        ({"unknown": "x"}, "posted"),  # fallback
        ([], "posted"),
        ({}, "posted"),
    ],
)
def test_extract_post_id(data, expected):
    assert postiz._extract_post_id(data) == expected


# ---------------------------------------------------------------------------
# captions._clamp
# ---------------------------------------------------------------------------


def test_captions_clamp_passthrough_under_limit():
    assert captions._clamp("hello  world", 100) == "hello world"


def test_captions_clamp_truncates_with_ellipsis():
    out = captions._clamp("x" * 50, 10)
    assert len(out) == 10 and out.endswith("…")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
