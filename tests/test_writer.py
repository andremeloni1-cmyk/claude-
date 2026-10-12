"""Tests for blog_automation/writer.py.

Covers the pure text helpers (_clamp, _slugify) plus the two model-driven
functions (select_images, write_post) with the Anthropic client stubbed, so no
network access or real credentials are required.

Run with:
    cd /home/user/claude- && python3 -m pytest tests/test_writer.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import blog_automation.writer as writer  # noqa: E402


# ---------------------------------------------------------------------------
# Stub Anthropic client (mirrors the shape writer.py consumes).
# ---------------------------------------------------------------------------


class _FakeTextBlock:
    def __init__(self, text: str):
        self.type = "text"
        self.text = text


class _FakeResponse:
    def __init__(self, payload: dict, stop_reason: str = "end_turn"):
        self.content = [_FakeTextBlock(json.dumps(payload))]
        self.stop_reason = stop_reason


class _FakeMessages:
    def __init__(self, response: _FakeResponse):
        self._response = response
        self.last_kwargs: dict = {}

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return self._response


class _FakeClient:
    def __init__(self, response: _FakeResponse):
        self.messages = _FakeMessages(response)


def _install_fake(monkeypatch, response: _FakeResponse) -> _FakeClient:
    client = _FakeClient(response)
    monkeypatch.setattr(writer.anthropic, "Anthropic", lambda api_key=None: client)
    return client


def _cfg(**overrides):
    defaults = dict(
        anthropic_api_key="dummy",
        model="claude-opus-4-8",
        images_per_post=4,
        business_name="Andre Meloni Photography",
        website_url="https://example.com",
        niche="wedding photography",
        location="NSW, Australia",
        service_area="Sydney, the South Coast",
        target_audience="Engaged couples",
        author="Andre Meloni",
        internal_links=[],
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# _clamp
# ---------------------------------------------------------------------------


def test_clamp_collapses_internal_whitespace():
    assert writer._clamp("a   b\n c", 100) == "a b c"


def test_clamp_returns_text_unchanged_at_exactly_the_limit():
    text = "x" * 10
    assert writer._clamp(text, 10) == text


def test_clamp_truncates_with_ellipsis_over_the_limit():
    out = writer._clamp("x" * 50, 10)
    assert len(out) == 10
    assert out.endswith("…")


def test_clamp_strips_before_appending_ellipsis():
    # The char before the cut is a space; it should be rstripped, not kept.
    out = writer._clamp("word " * 10, 6)
    assert out == "word…"


# ---------------------------------------------------------------------------
# _slugify
# ---------------------------------------------------------------------------


def test_slugify_lowercases_and_hyphenates():
    assert writer._slugify("Best Wedding Photos!") == "best-wedding-photos"


def test_slugify_collapses_runs_and_trims_edges():
    assert writer._slugify("  --Hello,  World--  ") == "hello-world"


def test_slugify_caps_length_at_80():
    assert len(writer._slugify("a " * 200)) <= 80


def test_slugify_falls_back_to_post_for_empty_input():
    assert writer._slugify("!!! ???") == "post"
    assert writer._slugify("") == "post"


# ---------------------------------------------------------------------------
# select_images
# ---------------------------------------------------------------------------


def _candidates(n: int) -> list[dict]:
    return [
        {"file_id": f"f{i}", "name": f"p{i}.jpg", "analysis_bytes": b"\xff\xd8\xff"}
        for i in range(n)
    ]


def test_select_images_returns_empty_for_no_candidates(monkeypatch):
    # Must short-circuit before constructing a client.
    monkeypatch.setattr(
        writer.anthropic, "Anthropic", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no client expected"))
    )
    assert writer.select_images(_cfg(), SimpleNamespace(keyword="k", notes=""), []) == []


def test_select_images_maps_indices_to_candidates_and_clamps_alt(monkeypatch):
    payload = {"chosen": [{"index": 1, "alt_text": "y" * 200}, {"index": 0, "alt_text": "cover"}]}
    _install_fake(monkeypatch, _FakeResponse(payload))

    out = writer.select_images(_cfg(), SimpleNamespace(keyword="k", notes="n"), _candidates(3))

    assert [c["file_id"] for c in out] == ["f1", "f0"]
    assert len(out[0]["alt_text"]) == 125  # clamped to 125 chars


def test_select_images_skips_duplicate_and_out_of_range_indices(monkeypatch):
    payload = {
        "chosen": [
            {"index": 0, "alt_text": "a"},
            {"index": 0, "alt_text": "dup"},   # duplicate -> skipped
            {"index": 99, "alt_text": "oob"},  # out of range -> skipped
            {"index": 2, "alt_text": "c"},
        ]
    }
    _install_fake(monkeypatch, _FakeResponse(payload))

    out = writer.select_images(_cfg(), SimpleNamespace(keyword="k", notes=""), _candidates(3))
    assert [c["file_id"] for c in out] == ["f0", "f2"]


def test_select_images_respects_images_per_post_cap(monkeypatch):
    payload = {"chosen": [{"index": i, "alt_text": str(i)} for i in range(5)]}
    _install_fake(monkeypatch, _FakeResponse(payload))

    out = writer.select_images(_cfg(images_per_post=2), SimpleNamespace(keyword="k", notes=""), _candidates(5))
    assert len(out) == 2


def test_select_images_raises_on_refusal(monkeypatch):
    _install_fake(monkeypatch, _FakeResponse({"chosen": []}, stop_reason="refusal"))
    with pytest.raises(RuntimeError):
        writer.select_images(_cfg(), SimpleNamespace(keyword="k", notes=""), _candidates(1))


# ---------------------------------------------------------------------------
# write_post
# ---------------------------------------------------------------------------


def _post_payload(**overrides):
    payload = {
        "title": "  Best   Wedding  Photos ",
        "slug": "Best Wedding Photos",
        "intro_1": "Intro one.",
        "intro_2": "Intro two.",
        "meta_title": "m" * 80,        # over the 60-char meta-title cap
        "meta_description": "d",
        "excerpt": "e",
        "category": "Wedding  Planning",
        "keywords": [" a ", "", "b"],   # whitespace + empty entries
        "body_markdown": "  ## Section\nbody  ",
    }
    payload.update(overrides)
    return payload


def test_write_post_postprocesses_fields(monkeypatch):
    _install_fake(monkeypatch, _FakeResponse(_post_payload()))

    out = writer.write_post(_cfg(), SimpleNamespace(keyword="wedding photos", notes=""), image_alts=[])

    assert out["title"] == "Best Wedding Photos"            # whitespace collapsed
    assert out["slug"] == "best-wedding-photos"             # slugified
    assert len(out["meta_title"]) == 60                     # clamped
    assert out["category"] == "Wedding Planning"            # whitespace collapsed
    assert out["keywords"] == ["a", "b"]                    # trimmed, empties dropped
    assert out["body_markdown"] == "## Section\nbody"       # stripped


def test_write_post_slug_falls_back_to_title_when_slug_missing(monkeypatch):
    _install_fake(monkeypatch, _FakeResponse(_post_payload(slug="")))
    out = writer.write_post(_cfg(), SimpleNamespace(keyword="k", notes=""), image_alts=[])
    assert out["slug"] == "best-wedding-photos"


def test_write_post_raises_on_refusal(monkeypatch):
    _install_fake(monkeypatch, _FakeResponse(_post_payload(), stop_reason="refusal"))
    with pytest.raises(RuntimeError):
        writer.write_post(_cfg(), SimpleNamespace(keyword="k", notes=""), image_alts=[])


@pytest.mark.parametrize(
    "n_images,expect_phrases,forbidden",
    [
        (0, ["No photos are available"], ["{{image_"]),
        (1, ["1 cover photo"], ["{{image_"]),
        (2, ["2 photos"], ["{{image_"]),
        (4, ["{{image_3}}", "{{image_4}}"], ["{{image_1}}", "{{image_2}}"]),
    ],
)
def test_write_post_image_instructions_branch_on_count(monkeypatch, n_images, expect_phrases, forbidden):
    client = _install_fake(monkeypatch, _FakeResponse(_post_payload()))
    alts = [f"alt {i}" for i in range(n_images)]

    writer.write_post(_cfg(), SimpleNamespace(keyword="k", notes=""), image_alts=alts)

    user_msg = client.messages.last_kwargs["messages"][0]["content"]
    for phrase in expect_phrases:
        assert phrase in user_msg
    for phrase in forbidden:
        assert phrase not in user_msg


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
