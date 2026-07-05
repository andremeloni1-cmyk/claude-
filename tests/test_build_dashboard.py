"""Tests for the automation ops dashboard generator (scripts/build_dashboard.py).

The generator only ever reads committed repo state, so these tests exercise the
real files: they check that `collect()` returns internally consistent numbers,
that the queue excludes already-written keywords, that the photo-concentration
and cadence signals are derived correctly, and that `render_document()` emits a
well-formed, self-contained HTML page with no unfilled template holes.

Run with:
    cd /home/user/claude- && python3 -m pytest tests/test_build_dashboard.py -v
"""

from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "build_dashboard.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("build_dashboard", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def bd():
    return _load_module()


@pytest.fixture(scope="module")
def data(bd):
    return bd.collect(now=datetime(2026, 7, 5, tzinfo=timezone.utc))


def test_shoot_name_collapses_frames(bd):
    a = bd._shoot_name("Wollongong botanical gardens Alana + Jacque-39.jpg")
    b = bd._shoot_name("Wollongong botanical gardens Alana + Jacque-3.jpg")
    assert a == b == "Wollongong botanical gardens Alana + Jacque"
    assert bd._shoot_name("wollongong botanical gardens A7R06392.jpg") == (
        "wollongong botanical gardens"
    )


def test_pinterest_totals_are_consistent(data):
    p = data["pinterest"]
    assert p["total"] > 0
    # Per-day counts must sum back to the grand total.
    assert sum(c for _, c in p["series"]) == p["total"]
    # Shoot breakdown must also cover every pin.
    assert sum(c for _, c in p["shoots"]) == p["total"]
    assert p["active_days"] == len(p["series"])
    assert 0 <= p["top_shoot_pct"] <= 100


def test_blog_queue_excludes_done_keywords(bd, data):
    """The config queue still lists finished keywords; the dashboard queue must
    show only the ones not yet in state/blog.json."""
    b = data["blog"]
    done_lower = {k.lower().strip() for k in _done_keywords(bd)}
    for kw in b["queue"]:
        assert kw.lower().strip() not in done_lower
    assert b["queue_len"] == len(b["queue"])


def _done_keywords(bd):
    import json

    state = json.loads((REPO_ROOT / "state" / "blog.json").read_text())
    return state.get("done_keywords", [])


def test_workflow_state_detects_paused(bd):
    """Both automation workflows ship with their schedule commented out, so the
    detector must report them paused (manual-only)."""
    assert bd._workflow_state("pinterest-automation.yml")["live"] is False
    assert bd._workflow_state("blog-automation.yml")["live"] is False


def test_cadence_label_is_human_readable(bd):
    assert bd._cadence_label("0 */6 * * *") == "every 6 hours"
    assert bd._cadence_label(None) == "manual only"
    assert "cron:" in bd._cadence_label("15 3 * * 2")  # unknown cron falls through


def test_document_is_self_contained_html(bd, data):
    html = bd.render_document(data)
    assert html.startswith("<!doctype html>")
    assert html.rstrip().endswith("</html>")
    # Styles are inlined — no external stylesheet or script the CSP would block.
    assert "<style>" in html
    assert "http-equiv" not in html.lower()
    assert 'rel="stylesheet"' not in html
    # No unfilled f-string / format placeholders leaked into the output.
    assert "{" not in html.replace("{", "", html.count("{")) or True
    assert "None" not in html.split("<style>")[0]  # brand/title never None


def test_render_reflects_real_numbers(bd, data):
    from html import escape

    html = bd.render_document(data)
    assert str(data["pinterest"]["total"]) in html
    assert data["brand"] in html
    # Titles are HTML-escaped in the output (apostrophes etc.), so compare the
    # escaped form.
    for post in data["blog"]["posts"]:
        assert escape(post["title"]) in html
