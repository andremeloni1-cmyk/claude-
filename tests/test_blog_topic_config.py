"""Tests for the new "top five couple poses for your wedding day" blog topic
entry added to config.yaml's blog.topics list.

This is a config-only change (see .pipeline/specs.md / .pipeline/changes.md):
no Python or Node code was touched, so these tests verify the YAML itself is
valid, well-formed, and safe for both the Python loader
(blog_automation/config.py) and the Node loader (framer/publish.mjs) to
consume, and that it does not collide with already-completed work recorded in
state/blog.json.

Run with:
    cd /home/user/claude- && python3 -m pytest tests/test_blog_topic_config.py -v
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config.yaml"
STATE_PATH = REPO_ROOT / "state" / "blog.json"

NEW_KEYWORD = "top five couple poses for your wedding day"
NEW_NOTES = (
    "Listicle of five flattering, natural couple poses for the wedding day; "
    "reassure camera-shy couples and explain how a photographer guides each "
    "pose. Keep it practical and experience-led."
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def raw_config_text() -> str:
    return CONFIG_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def parsed_config(raw_config_text: str) -> dict:
    return yaml.safe_load(raw_config_text) or {}


@pytest.fixture(scope="module")
def topics(parsed_config: dict) -> list:
    return parsed_config["blog"]["topics"]


# ---------------------------------------------------------------------------
# YAML validity (Python side)
# ---------------------------------------------------------------------------


def test_config_file_exists():
    assert CONFIG_PATH.is_file()


def test_python_yaml_safe_load_succeeds(raw_config_text: str):
    """yaml.safe_load must parse the whole file without raising."""
    data = yaml.safe_load(raw_config_text)
    assert isinstance(data, dict)
    assert "blog" in data


def test_blog_topics_is_a_list(parsed_config: dict):
    assert isinstance(parsed_config["blog"]["topics"], list)
    assert len(parsed_config["blog"]["topics"]) >= 1


# ---------------------------------------------------------------------------
# YAML validity (Node side, the `yaml` package used by framer/publish.mjs)
# ---------------------------------------------------------------------------


def test_node_yaml_package_parses_config():
    """framer/publish.mjs::loadConfig() uses the npm `yaml` package's parse().

    Run a tiny inline Node script (using the same package, installed under
    framer/node_modules) to confirm it parses config.yaml without error and
    sees the same topics list / new entry that Python sees.
    """
    yaml_pkg_dir = REPO_ROOT / "framer" / "node_modules" / "yaml"
    if not yaml_pkg_dir.exists():
        pytest.skip(
            "framer/node_modules/yaml not installed (run `npm install` in "
            "framer/ to exercise the Node-side YAML parser)."
        )

    script = r"""
import { readFileSync } from "node:fs";
import { parse as parseYaml } from "yaml";

const raw = readFileSync(process.argv[2], "utf8");
const data = parseYaml(raw) || {};
const topics = (data.blog && data.blog.topics) || [];
console.log(JSON.stringify(topics));
"""
    script_path = REPO_ROOT / "framer" / "_tmp_test_parse_config.mjs"
    script_path.write_text(script, encoding="utf-8")
    try:
        result = subprocess.run(
            ["node", str(script_path), str(CONFIG_PATH)],
            cwd=str(REPO_ROOT / "framer"),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"Node `yaml` package failed to parse config.yaml.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        node_topics = json.loads(result.stdout)
        assert isinstance(node_topics, list)
        keywords = [t.get("keyword") for t in node_topics]
        assert NEW_KEYWORD in keywords
    finally:
        script_path.unlink(missing_ok=True)


def test_node_publish_mjs_load_config_does_not_throw():
    """Smoke-test the actual loadConfig() logic path used in publish.mjs
    (collection_name / field_map) still works with the new topics list
    present — i.e. the new entry didn't break unrelated parsing.
    """
    yaml_pkg_dir = REPO_ROOT / "framer" / "node_modules" / "yaml"
    if not yaml_pkg_dir.exists():
        pytest.skip("framer/node_modules/yaml not installed.")

    script = r"""
import { readFileSync } from "node:fs";
import { parse as parseYaml } from "yaml";

function loadConfig(repoRoot) {
  const raw = readFileSync(repoRoot + "/config.yaml", "utf8");
  const data = parseYaml(raw) || {};
  const blog = data.blog || {};
  return {
    collectionName: (blog.collection_name || "Blog").trim(),
    fieldMap: blog.field_map || {},
  };
}

const cfg = loadConfig(process.argv[2]);
console.log(JSON.stringify(cfg));
"""
    script_path = REPO_ROOT / "framer" / "_tmp_test_load_config.mjs"
    script_path.write_text(script, encoding="utf-8")
    try:
        result = subprocess.run(
            ["node", str(script_path), str(REPO_ROOT)],
            cwd=str(REPO_ROOT / "framer"),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        cfg = json.loads(result.stdout)
        assert cfg["collectionName"] == "Blog"
        assert "title" in cfg["fieldMap"]
    finally:
        script_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Parsing into blog_automation/config.py's Topic objects
# ---------------------------------------------------------------------------


def _topics_from_raw(raw_topics: list):
    """Replicates blog_automation/config.py::load()'s topic-parsing logic
    exactly, so we test the real parsing rule without needing the
    ANTHROPIC_API_KEY / GOOGLE_SERVICE_ACCOUNT_JSON / GDRIVE_FOLDER_ID env
    vars that the full load() requires.
    """
    sys.path.insert(0, str(REPO_ROOT))
    from blog_automation.config import Topic  # noqa: WPS433 (import inside fn ok for test)

    return [
        Topic(keyword=str(t.get("keyword", "")).strip(), notes=str(t.get("notes", "")).strip())
        for t in raw_topics
        if str(t.get("keyword", "")).strip()
    ]


def test_topic_dataclass_parses_new_entry(topics: list):
    parsed = _topics_from_raw(topics)
    matching = [t for t in parsed if t.keyword == NEW_KEYWORD]
    assert len(matching) == 1, f"expected exactly one Topic for {NEW_KEYWORD!r}, got {len(matching)}"
    topic = matching[0]
    assert topic.notes == NEW_NOTES
    assert topic.keyword == NEW_KEYWORD  # no leading/trailing whitespace, exact match


def test_full_config_load_with_env_vars(monkeypatch):
    """Exercise the real blog_automation.config.load() end-to-end (with dummy
    secrets so it doesn't hit ConfigError on missing env vars), confirming
    the new topic survives the full loader unmodified and last in the list.
    """
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy-test-key")
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", "{}")
    monkeypatch.setenv("GDRIVE_FOLDER_ID", "dummy-folder-id")

    sys.path.insert(0, str(REPO_ROOT))
    import importlib

    import blog_automation.config as config_mod

    importlib.reload(config_mod)  # ensure a clean import in case of prior partial import
    cfg = config_mod.load()

    assert cfg.topics[-1].keyword == NEW_KEYWORD
    assert cfg.topics[-1].notes == NEW_NOTES
    # Existing topics still present and in original order (no reordering).
    assert cfg.topics[0].keyword == "best intimate wedding venues in the Southern Highlands"
    assert cfg.topics[5].keyword == "Southern Highlands elopement photography guide"
    assert len(cfg.topics) == 7


def test_no_topic_silently_dropped_for_empty_keyword_rule(topics: list):
    """Sanity-check on the config.py rule itself: every raw topic in the file
    (including the new one) has a non-empty keyword, so none are silently
    dropped by the `if str(t.get("keyword", "")).strip()` filter.
    """
    parsed = _topics_from_raw(topics)
    assert len(parsed) == len(topics), (
        "Some topic(s) were dropped by the keyword-required filter — check "
        "for an empty/whitespace-only keyword."
    )


# ---------------------------------------------------------------------------
# Keyword uniqueness within config.yaml
# ---------------------------------------------------------------------------


def test_new_keyword_present_exactly_once(topics: list):
    keywords = [t.get("keyword") for t in topics]
    assert keywords.count(NEW_KEYWORD) == 1


def test_all_keywords_unique_in_config(topics: list):
    keywords = [t.get("keyword") for t in topics]
    duplicates = {k for k in keywords if keywords.count(k) > 1}
    assert not duplicates, f"Duplicate keyword(s) found in blog.topics: {duplicates}"


def test_new_keyword_is_last_entry(topics: list):
    assert topics[-1]["keyword"] == NEW_KEYWORD


# ---------------------------------------------------------------------------
# Keyword not already present in state/blog.json's done_keywords
# ---------------------------------------------------------------------------


def test_state_file_exists():
    assert STATE_PATH.is_file()


def test_new_keyword_not_in_done_keywords():
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    done_keywords = state.get("done_keywords", [])
    assert NEW_KEYWORD not in done_keywords, (
        "New keyword already marked done in state/blog.json — it would never "
        "be picked up by a future run (state.is_done() matches on exact "
        "keyword string)."
    )


def test_new_keyword_not_in_any_existing_post_record():
    """Belt-and-suspenders: also check the per-post 'keyword' values under
    state.posts, not just done_keywords, in case of any drift between the two.
    """
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    posts = state.get("posts", {})
    used_keywords = {p.get("keyword") for p in posts.values()}
    assert NEW_KEYWORD not in used_keywords


# ---------------------------------------------------------------------------
# Formatting / quoting consistency with sibling entries
# ---------------------------------------------------------------------------


def test_new_entry_lines_double_quoted(raw_config_text: str):
    lines = raw_config_text.splitlines()
    keyword_line = next(line for line in lines if NEW_KEYWORD in line)
    notes_line = next(line for line in lines if "camera-shy couples" in line)

    assert re.search(r'keyword:\s*"top five couple poses for your wedding day"\s*$', keyword_line), keyword_line
    assert re.search(r'notes:\s*".*"\s*$', notes_line), notes_line


def test_new_entry_indentation_matches_siblings(raw_config_text: str):
    lines = raw_config_text.splitlines()
    keyword_lines = [line for line in lines if re.match(r"^\s*- keyword:", line)]
    notes_lines = [line for line in lines if re.match(r"^\s*notes:", line)]

    assert len(keyword_lines) >= 2
    assert len(notes_lines) >= 2

    keyword_indents = {len(line) - len(line.lstrip(" ")) for line in keyword_lines}
    notes_indents = {len(line) - len(line.lstrip(" ")) for line in notes_lines}

    assert keyword_indents == {4}, f"Inconsistent '- keyword:' indentation: {keyword_indents}"
    assert notes_indents == {6}, f"Inconsistent 'notes:' indentation: {notes_indents}"


def test_new_entry_has_exactly_keyword_and_notes_keys(topics: list):
    new_entry = next(t for t in topics if t.get("keyword") == NEW_KEYWORD)
    assert set(new_entry.keys()) == {"keyword", "notes"}


def test_no_trailing_whitespace_in_file(raw_config_text: str):
    offending = [
        (i + 1, line) for i, line in enumerate(raw_config_text.splitlines()) if line != line.rstrip()
    ]
    assert offending == [], f"Trailing whitespace found on line(s): {offending}"


def test_file_ends_with_single_trailing_newline():
    raw_bytes = CONFIG_PATH.read_bytes()
    assert raw_bytes.endswith(b"\n"), "config.yaml must end with a newline."
    assert not raw_bytes.endswith(b"\n\n"), "config.yaml must not have extra trailing blank lines."


def test_existing_topics_not_reordered_or_renumbered(topics: list):
    expected_prefix = [
        "best intimate wedding venues in the Southern Highlands",
        "South Coast NSW wedding photography locations",
        "how to choose a wedding photographer in Sydney",
        "what to wear for an engagement photoshoot",
        "best time of day for wedding photos",
        "Southern Highlands elopement photography guide",
    ]
    actual_prefix = [t["keyword"] for t in topics[: len(expected_prefix)]]
    assert actual_prefix == expected_prefix


def test_no_numeral_used_in_new_keyword():
    """Spec: avoid a numeral that could be misread; use spelled-out 'top
    five' (the chosen default) rather than 'top 5'."""
    assert "5" not in NEW_KEYWORD
    assert "top five" in NEW_KEYWORD


def test_keyword_and_notes_are_lowercase_prose_consistent_with_siblings(topics: list):
    """Existing keywords are plain lowercase prose (not Title Case, except
    where a proper noun like 'Southern Highlands' or 'Sydney' appears). The
    new keyword should follow the same casing convention: no ALL CAPS, not
    capitalised as a title.
    """
    new_entry = next(t for t in topics if t.get("keyword") == NEW_KEYWORD)
    keyword = new_entry["keyword"]
    # First character should be lowercase to match sibling style
    # ("best intimate...", "how to choose...", "what to wear...", "top five...").
    assert keyword[0].islower(), f"Expected keyword to start lowercase like siblings, got: {keyword!r}"
    assert keyword == keyword.strip(), "Keyword must not have leading/trailing whitespace."


def test_no_secrets_introduced(raw_config_text: str):
    """Spec: no API keys should be added. Heuristic check for common secret
    patterns anywhere in the file (defensive; this file should hold none)."""
    suspicious_patterns = [
        r"sk-[A-Za-z0-9]{20,}",
        r"AIza[0-9A-Za-z\-_]{35}",
        r"-----BEGIN (RSA |EC )?PRIVATE KEY-----",
    ]
    for pattern in suspicious_patterns:
        assert not re.search(pattern, raw_config_text), f"Possible secret matching {pattern!r} found in config.yaml"


# ---------------------------------------------------------------------------
# append_topics() sanitises untrusted (LLM/web-search) keyword/notes strings
# ---------------------------------------------------------------------------


def _fresh_config_module():
    sys.path.insert(0, str(REPO_ROOT))
    import importlib

    import blog_automation.config as config_mod

    return importlib.reload(config_mod)


def test_append_topics_normalises_newlines_and_control_chars(tmp_path, monkeypatch):
    """A keyword/notes value with an embedded newline or control char must be
    collapsed to a single line so it can't break the double-quoted YAML scalar
    and corrupt config.yaml for every subsequent run.
    """
    config_mod = _fresh_config_module()

    tmp_config = tmp_path / "config.yaml"
    tmp_config.write_text(
        "blog:\n"
        "  topics:\n"
        '    - keyword: "existing keyword"\n'
        '      notes: "existing notes"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(config_mod, "_CONFIG_PATH", tmp_config)

    dirty = config_mod.Topic(
        keyword="poses\nfor\tcouples",
        notes="line one\r\nline two\twith   spaces",
    )
    config_mod.append_topics([dirty])

    # File must still be valid YAML after the append.
    data = yaml.safe_load(tmp_config.read_text(encoding="utf-8"))
    topics = data["blog"]["topics"]
    assert topics[-1]["keyword"] == "poses for couples"
    assert topics[-1]["notes"] == "line one line two with spaces"
    # No stray newline/tab survived into the raw file body of the new entry.
    assert "\t" not in tmp_config.read_text(encoding="utf-8")


def test_append_topics_rolls_back_on_invalid_yaml(tmp_path, monkeypatch):
    """If a write somehow yields invalid YAML, the original file is restored
    and a ConfigError is raised — a corrupt config is never left behind.
    """
    config_mod = _fresh_config_module()

    original = (
        "blog:\n"
        "  topics:\n"
        '    - keyword: "existing keyword"\n'
        '      notes: "existing notes"\n'
    )
    tmp_config = tmp_path / "config.yaml"
    tmp_config.write_text(original, encoding="utf-8")
    monkeypatch.setattr(config_mod, "_CONFIG_PATH", tmp_config)

    # Force a corrupt write: make _yaml_dquote a no-op so a stray quote in the
    # keyword produces malformed YAML, proving the rollback path works.
    monkeypatch.setattr(config_mod, "_yaml_dquote", lambda v: v)

    with pytest.raises(config_mod.ConfigError):
        config_mod.append_topics([config_mod.Topic(keyword='bad " quote', notes="x")])

    assert tmp_config.read_text(encoding="utf-8") == original


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
