"""Tests for pinterest_automation/captions.py::generate() with a stubbed client.

Covers field clamping to Pinterest limits, the unsupported-media-type fallback,
keyword cleanup, and refusal handling. No network access required.

Run with:
    cd /home/user/claude- && python3 -m pytest tests/test_captions.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import pinterest_automation.captions as captions  # noqa: E402


class _FakeTextBlock:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class _FakeResponse:
    def __init__(self, payload, stop_reason="end_turn"):
        self.content = [_FakeTextBlock(json.dumps(payload))]
        self.stop_reason = stop_reason


class _FakeMessages:
    def __init__(self, response):
        self._response = response
        self.last_kwargs = {}

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return self._response


class _FakeClient:
    def __init__(self, response):
        self.messages = _FakeMessages(response)


def _install(monkeypatch, response):
    client = _FakeClient(response)
    monkeypatch.setattr(captions.anthropic, "Anthropic", lambda api_key=None: client)
    return client


def _cfg(**overrides):
    base = dict(
        anthropic_api_key="ak", model="m", business_name="b", niche="n",
        location="l", service_area="Sydney, South Coast", website_url="https://x.com",
        target_audience="t",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _payload(**overrides):
    p = {
        "title": "t " * 100,         # over 100-char cap
        "description": "d " * 400,   # over 500-char cap
        "alt_text": "a " * 400,      # over 500-char cap
        "keywords": [" k1 ", "", "k2"],
    }
    p.update(overrides)
    return p


def test_generate_clamps_fields_and_cleans_keywords(monkeypatch):
    _install(monkeypatch, _FakeResponse(_payload()))
    out = captions.generate(_cfg(), b"img", "image/jpeg", "photo.jpg")
    assert len(out["title"]) == 100
    assert len(out["description"]) == 500
    assert len(out["alt_text"]) == 500
    assert out["keywords"] == ["k1", "k2"]


def test_generate_falls_back_to_jpeg_for_unsupported_media(monkeypatch):
    client = _install(monkeypatch, _FakeResponse(_payload()))
    captions.generate(_cfg(), b"img", "image/tiff", "photo.tiff")
    content = client.messages.last_kwargs["messages"][0]["content"]
    image_block = next(b for b in content if b["type"] == "image")
    assert image_block["source"]["media_type"] == "image/jpeg"


def test_generate_preserves_supported_media(monkeypatch):
    client = _install(monkeypatch, _FakeResponse(_payload()))
    captions.generate(_cfg(), b"img", "image/png", "photo.png")
    content = client.messages.last_kwargs["messages"][0]["content"]
    image_block = next(b for b in content if b["type"] == "image")
    assert image_block["source"]["media_type"] == "image/png"


def test_generate_raises_on_refusal(monkeypatch):
    _install(monkeypatch, _FakeResponse(_payload(), stop_reason="refusal"))
    with pytest.raises(RuntimeError):
        captions.generate(_cfg(), b"img", "image/jpeg", "photo.jpg")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
