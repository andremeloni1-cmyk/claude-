"""Tests for the automatic topic-research feature:
- blog_automation/research.py::research_topics() (web-search-driven discovery)
- blog_automation/config.py::append_topics() (persists results into config.yaml)
- blog_automation/main.py::run()'s auto-topping-up of the pending queue

These tests stub the Anthropic client and Drive/writer/bundle calls so no
network access or real credentials are required.

Run with:
    cd /home/user/claude- && python3 -m pytest tests/test_research.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from blog_automation.config import Topic  # noqa: E402


# ---------------------------------------------------------------------------
# Fakes for the Anthropic client used by research.research_topics()
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


class _FakeAnthropicClient:
    def __init__(self, response: _FakeResponse):
        self.messages = _FakeMessages(response)

    def __call__(self, api_key: str):  # mimics anthropic.Anthropic(api_key=...)
        return self


def _make_cfg(**overrides):
    defaults = dict(
        business_name="Andre Meloni Photography",
        service_area="Sydney, the South Coast and the Southern Highlands",
        location="New South Wales, Australia",
        target_audience="Engaged couples planning a wedding",
        model="claude-opus-4-8",
        anthropic_api_key="dummy-test-key",
        auto_research=True,
        research_batch_size=3,
        max_posts_per_run=1,
        topics=[],
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# research_topics()
# ---------------------------------------------------------------------------


def test_research_topics_returns_parsed_topics(monkeypatch):
    import blog_automation.research as research_mod

    payload = {
        "topics": [
            {"keyword": "best wedding photo locations in Sydney", "notes": "Showcase scenic spots."},
            {"keyword": "how long should a wedding photographer shoot", "notes": "Buyer's guide."},
        ]
    }
    fake_client = _FakeAnthropicClient(_FakeResponse(payload))
    monkeypatch.setattr(research_mod.anthropic, "Anthropic", fake_client)

    cfg = _make_cfg()
    result = research_mod.research_topics(cfg, avoid_keywords=set(), count=2)

    assert len(result) == 2
    assert result[0].keyword == "best wedding photo locations in Sydney"
    assert result[0].notes == "Showcase scenic spots."
    assert result[1].keyword == "how long should a wedding photographer shoot"


def test_research_topics_filters_duplicates_case_insensitively(monkeypatch):
    import blog_automation.research as research_mod

    payload = {
        "topics": [
            {"keyword": "Best Time Of Day For Wedding Photos", "notes": "dup of existing"},
            {"keyword": "new unique topic idea", "notes": "fresh"},
        ]
    }
    fake_client = _FakeAnthropicClient(_FakeResponse(payload))
    monkeypatch.setattr(research_mod.anthropic, "Anthropic", fake_client)

    cfg = _make_cfg()
    avoid = {"best time of day for wedding photos"}
    result = research_mod.research_topics(cfg, avoid_keywords=avoid, count=2)

    assert len(result) == 1
    assert result[0].keyword == "new unique topic idea"


def test_research_topics_raises_on_refusal(monkeypatch):
    import blog_automation.research as research_mod

    fake_client = _FakeAnthropicClient(_FakeResponse({"topics": []}, stop_reason="refusal"))
    monkeypatch.setattr(research_mod.anthropic, "Anthropic", fake_client)

    cfg = _make_cfg()
    with pytest.raises(RuntimeError):
        research_mod.research_topics(cfg, avoid_keywords=set(), count=2)


def test_research_topics_zero_count_short_circuits(monkeypatch):
    import blog_automation.research as research_mod

    def _boom(**kwargs):
        raise AssertionError("should not call the API for count<=0")

    monkeypatch.setattr(
        research_mod.anthropic,
        "Anthropic",
        lambda api_key: SimpleNamespace(messages=SimpleNamespace(create=_boom)),
    )

    cfg = _make_cfg()
    assert research_mod.research_topics(cfg, avoid_keywords=set(), count=0) == []


def test_research_topics_passes_web_search_tool_and_schema(monkeypatch):
    import blog_automation.research as research_mod

    fake_client = _FakeAnthropicClient(_FakeResponse({"topics": []}))
    monkeypatch.setattr(research_mod.anthropic, "Anthropic", fake_client)

    cfg = _make_cfg()
    research_mod.research_topics(cfg, avoid_keywords=set(), count=1)

    kwargs = fake_client.messages.last_kwargs
    tool_types = [t.get("type") for t in kwargs["tools"]]
    assert "web_search_20250305" in tool_types
    assert kwargs["output_config"]["format"]["type"] == "json_schema"


# ---------------------------------------------------------------------------
# config.append_topics()
# ---------------------------------------------------------------------------


def test_append_topics_preserves_existing_content_and_adds_new_block(tmp_path, monkeypatch):
    import blog_automation.config as config_mod

    fake_config = tmp_path / "config.yaml"
    fake_config.write_text(
        "blog:\n"
        "  topics:\n"
        '    - keyword: "existing topic"\n'
        '      notes: "existing notes"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(config_mod, "_CONFIG_PATH", fake_config)

    config_mod.append_topics([Topic(keyword="new topic", notes="new notes")])

    text = fake_config.read_text(encoding="utf-8")
    assert '- keyword: "existing topic"' in text
    assert '- keyword: "new topic"' in text
    assert '      notes: "new notes"' in text
    assert text.endswith("\n") and not text.endswith("\n\n")


def test_append_topics_escapes_double_quotes(tmp_path, monkeypatch):
    import blog_automation.config as config_mod
    import yaml

    fake_config = tmp_path / "config.yaml"
    fake_config.write_text("blog:\n  topics:\n", encoding="utf-8")
    monkeypatch.setattr(config_mod, "_CONFIG_PATH", fake_config)

    config_mod.append_topics([Topic(keyword='topic with "quotes" inside', notes="plain")])

    data = yaml.safe_load(fake_config.read_text(encoding="utf-8"))
    assert data["blog"]["topics"][0]["keyword"] == 'topic with "quotes" inside'


def test_append_topics_noop_for_empty_list(tmp_path, monkeypatch):
    import blog_automation.config as config_mod

    fake_config = tmp_path / "config.yaml"
    original = "blog:\n  topics: []\n"
    fake_config.write_text(original, encoding="utf-8")
    monkeypatch.setattr(config_mod, "_CONFIG_PATH", fake_config)

    config_mod.append_topics([])

    assert fake_config.read_text(encoding="utf-8") == original


# ---------------------------------------------------------------------------
# main.run()'s auto-topping-up behaviour
# ---------------------------------------------------------------------------


def _run_with_stubs(monkeypatch, *, pending_count: int, max_posts_per_run: int, auto_research: bool):
    """Drive blog_automation.main.run() with everything except the
    pending-queue/auto-research decision stubbed out, and report whether
    research_topics() and config.append_topics() were called.
    """
    import blog_automation.main as main_mod

    done_keywords = []
    topics = []
    for i in range(pending_count):
        topics.append(Topic(keyword=f"pending topic {i}", notes=""))
    # One already-done topic so cfg.topics != pending in the general case.
    topics.append(Topic(keyword="already done topic", notes=""))
    done_keywords.append("already done topic")

    cfg = _make_cfg(
        topics=topics,
        max_posts_per_run=max_posts_per_run,
        auto_research=auto_research,
        research_batch_size=2,
        state_path=Path("/tmp/unused-state.json"),
        published_dir=Path("/tmp/unused-published"),
        author="Andre Meloni",
        avoid_reusing_images=True,
        image_candidate_pool=24,
        images_per_post=4,
        gdrive_folder_id="dummy",
        google_service_account_json="{}",
    )

    monkeypatch.setattr(main_mod.config, "load", lambda: cfg)
    monkeypatch.setattr(main_mod.state, "load", lambda path: {"done_keywords": done_keywords, "used_image_ids": [], "posts": {}})
    monkeypatch.setattr(main_mod.state, "is_done", lambda st, keyword: keyword in st["done_keywords"])
    monkeypatch.setattr(main_mod.state, "used_image_ids", lambda st: set())
    monkeypatch.setattr(main_mod.state, "mark_done", lambda *a, **k: None)
    monkeypatch.setattr(main_mod.state, "save", lambda *a, **k: None)

    # No Drive photos needed: stub _build_post entirely so we never touch
    # the real Drive/Anthropic/bundle code paths.
    monkeypatch.setattr(main_mod.drive, "build_service", lambda *_: object())
    monkeypatch.setattr(main_mod.drive, "list_images", lambda *_: [])
    monkeypatch.setattr(main_mod, "_build_post", lambda *a, **k: ("some-slug", []))

    research_calls = []
    monkeypatch.setattr(
        main_mod.research,
        "research_topics",
        lambda cfg_, avoid, count: research_calls.append((avoid, count)) or [],
    )
    append_calls = []
    monkeypatch.setattr(main_mod.config, "append_topics", lambda new_topics: append_calls.append(new_topics))

    main_mod.run()
    return research_calls, append_calls


def test_auto_research_triggers_when_pending_below_max_posts_per_run(monkeypatch):
    research_calls, _ = _run_with_stubs(
        monkeypatch, pending_count=0, max_posts_per_run=1, auto_research=True
    )
    assert len(research_calls) == 1
    assert research_calls[0][1] == 2  # research_batch_size


def test_auto_research_skipped_when_queue_has_enough_pending(monkeypatch):
    research_calls, _ = _run_with_stubs(
        monkeypatch, pending_count=2, max_posts_per_run=1, auto_research=True
    )
    assert research_calls == []


def test_auto_research_skipped_when_disabled(monkeypatch):
    research_calls, _ = _run_with_stubs(
        monkeypatch, pending_count=0, max_posts_per_run=1, auto_research=False
    )
    assert research_calls == []


def test_new_topics_are_persisted_and_added_to_pending(monkeypatch):
    import blog_automation.main as main_mod

    cfg = _make_cfg(
        topics=[],
        max_posts_per_run=1,
        auto_research=True,
        research_batch_size=1,
        state_path=Path("/tmp/unused-state.json"),
        published_dir=Path("/tmp/unused-published"),
        author="Andre Meloni",
        avoid_reusing_images=True,
        image_candidate_pool=24,
        images_per_post=4,
        gdrive_folder_id="dummy",
        google_service_account_json="{}",
    )
    monkeypatch.setattr(main_mod.config, "load", lambda: cfg)
    monkeypatch.setattr(main_mod.state, "load", lambda path: {"done_keywords": [], "used_image_ids": [], "posts": {}})
    monkeypatch.setattr(main_mod.state, "is_done", lambda st, keyword: keyword in st["done_keywords"])
    monkeypatch.setattr(main_mod.state, "used_image_ids", lambda st: set())
    monkeypatch.setattr(main_mod.state, "mark_done", lambda *a, **k: None)
    monkeypatch.setattr(main_mod.state, "save", lambda *a, **k: None)
    monkeypatch.setattr(main_mod.drive, "build_service", lambda *_: object())
    monkeypatch.setattr(main_mod.drive, "list_images", lambda *_: [])

    built_with = []
    monkeypatch.setattr(
        main_mod,
        "_build_post",
        lambda cfg_, *a, **k: (built_with.append(a[-1].keyword), ("slug", []))[1],
    )

    new_topic = Topic(keyword="freshly researched topic", notes="auto")
    monkeypatch.setattr(main_mod.research, "research_topics", lambda cfg_, avoid, count: [new_topic])
    appended = []
    monkeypatch.setattr(main_mod.config, "append_topics", lambda topics: appended.append(topics))

    exit_code = main_mod.run()

    assert exit_code == 0
    assert appended == [[new_topic]]
    assert built_with == ["freshly researched topic"]
    assert new_topic in cfg.topics


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
