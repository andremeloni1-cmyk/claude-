#!/usr/bin/env python3
"""Build the marketing-automation ops dashboard.

Reads the committed state the two pipelines leave behind — `state/posted.json`
(Pinterest), `state/blog.json` (blog), `config.yaml` (limits + topic queue) and
the two workflow files (schedule / paused state) — and renders a single,
self-contained `dashboard.html` at the repo root. No API keys, no network: it
only ever reads files already in the repo, so it is safe to run anywhere.

Usage:
    python scripts/build_dashboard.py                 # writes dashboard.html
    python scripts/build_dashboard.py --fragment f.html  # also write a body-only
                                                          # fragment (for embedding)

The heavy lifting is in `collect()`, which returns a plain dict of everything
the template needs; `render_body()` turns that into markup. Keeping the two
apart means the numbers can be unit-tested without going near the HTML.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
WORKFLOWS = ROOT / ".github" / "workflows"


# --------------------------------------------------------------------------- #
# Data collection
# --------------------------------------------------------------------------- #
def _load_json(path: Path, default):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _shoot_name(file_name: str) -> str:
    """Collapse a photo file name down to the shoot it came from.

    Files look like ``Wollongong botanical gardens Alana + Jacque-39.jpg`` or
    ``wollongong botanical gardens A7R06392.jpg`` — strip the trailing frame
    number / camera code and the extension so sibling frames group together.
    """
    stem = re.sub(r"\.jpe?g$", "", file_name, flags=re.IGNORECASE)
    stem = re.split(r"\s+(?:A7R|DSC|IMG|_)\w*$", stem)[0]
    stem = re.sub(r"[-_]\s*\d+$", "", stem)
    return stem.strip(" -_") or "Untitled shoot"


def _workflow_state(filename: str) -> dict:
    """Detect whether a workflow's cron schedule is live or paused.

    A paused workflow keeps its ``schedule:`` block commented out (see the two
    automation workflows), so an *uncommented* ``schedule:`` line means live.
    The cron string is pulled out for display either way.
    """
    text = (WORKFLOWS / filename).read_text() if (WORKFLOWS / filename).exists() else ""
    live = bool(re.search(r"^\s*schedule:", text, flags=re.MULTILINE))
    cron_match = re.search(r'cron:\s*["\']([^"\']+)["\']', text)
    return {"live": live, "cron": cron_match.group(1) if cron_match else None}


# Human-readable cadence for the handful of crons this repo actually uses.
_CADENCE = {
    "0 */6 * * *": "every 6 hours",
    "0 9 * * 1": "weekly · Mon 09:00 UTC",
}


def _cadence_label(cron: str | None) -> str:
    if not cron:
        return "manual only"
    return _CADENCE.get(cron, f"cron: {cron}")


def collect(now: datetime | None = None) -> dict:
    """Gather every number the dashboard shows into a plain dict."""
    now = now or datetime.now(timezone.utc)

    cfg = yaml.safe_load((ROOT / "config.yaml").read_text()) or {}
    blog_cfg = cfg.get("blog", {}) or {}

    # ---- Pinterest ---------------------------------------------------------
    posted = _load_json(STATE / "posted.json", {}).get("posted", {})
    pin_days = Counter(v["posted_at"][:10] for v in posted.values() if v.get("posted_at"))
    shoots = Counter(_shoot_name(v.get("file_name", "")) for v in posted.values())
    day_series = sorted(pin_days.items())
    top_shoot = shoots.most_common(1)[0] if shoots else ("—", 0)
    pin_total = len(posted)

    pin_wf = _workflow_state("pinterest-automation.yml")
    last_pin_day = day_series[-1][0] if day_series else None
    pinterest = {
        "total": pin_total,
        "first_day": day_series[0][0] if day_series else None,
        "last_day": last_pin_day,
        "days_since": (now.date() - datetime.fromisoformat(last_pin_day).date()).days
        if last_pin_day
        else None,
        "active_days": len(day_series),
        "series": day_series,
        "peak_day": max((c for _, c in day_series), default=0),
        "shoots": shoots.most_common(),
        "shoot_count": len(shoots),
        "top_shoot": {"name": top_shoot[0], "count": top_shoot[1]},
        "top_shoot_pct": round(100 * top_shoot[1] / pin_total) if pin_total else 0,
        "max_per_run": cfg.get("max_pins_per_run"),
        "live": pin_wf["live"],
        "cadence": _cadence_label(pin_wf["cron"]),
    }

    # ---- Blog --------------------------------------------------------------
    blog_state = _load_json(STATE / "blog.json", {})
    done = blog_state.get("done_keywords", [])
    done_lower = {k.lower().strip() for k in done}
    posts = blog_state.get("posts", {})

    # Prefer the human title from each published bundle; fall back to the slug.
    post_rows = []
    for slug, meta in posts.items():
        title = slug.replace("-", " ").title()
        bundle = ROOT / "published" / slug / "post.json"
        if bundle.exists():
            fields = _load_json(bundle, {}).get("fields", {})
            title = fields.get("title") or title
        post_rows.append(
            {"slug": slug, "title": title, "date": meta.get("created_at", "")[:10]}
        )
    post_rows.sort(key=lambda r: r["date"], reverse=True)

    # The queue in config.yaml still lists finished keywords; the *remaining*
    # work is whatever hasn't been marked done yet.
    queue = []
    for t in blog_cfg.get("topics", []) or []:
        kw = t.get("keyword") if isinstance(t, dict) else t
        if kw and kw.lower().strip() not in done_lower:
            queue.append(kw)

    blog_wf = _workflow_state("blog-automation.yml")
    blog = {
        "live": len(post_rows),
        "posts": post_rows,
        "done_count": len(done),
        "queue": queue,
        "queue_len": len(queue),
        "max_per_run": blog_cfg.get("max_posts_per_run"),
        "collection": blog_cfg.get("collection_name", "Blog"),
        "is_live": blog_wf["live"],
        "cadence": _cadence_label(blog_wf["cron"]),
    }

    return {
        "generated": now,
        "brand": cfg.get("business_name", "Photography Automations"),
        "website": cfg.get("website_url", ""),
        "service_area": (cfg.get("service_area") or "").strip(),
        "pinterest": pinterest,
        "blog": blog,
    }


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def _status(live: bool) -> tuple[str, str]:
    return ("live", "Live") if live else ("paused", "Paused")


def _bar_chart(series: list[tuple[str, int]], peak: int) -> str:
    """A compact inline-SVG column chart of pins posted per day."""
    if not series:
        return '<p class="empty">No pins posted yet.</p>'
    w, h = 640, 150
    pad_b, pad_t = 26, 12
    gap = 6
    n = len(series)
    bw = (w - (n - 1) * gap) / n
    plot_h = h - pad_b - pad_t
    bars, labels = [], []
    for i, (day, count) in enumerate(series):
        bh = (count / peak) * plot_h if peak else 0
        x = i * (bw + gap)
        y = pad_t + (plot_h - bh)
        emph = i == n - 1
        cls = "bar bar--last" if emph else "bar"
        bars.append(
            f'<rect class="{cls}" x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" '
            f'height="{bh:.1f}" rx="2"><title>{escape(day)}: {count} pins</title></rect>'
        )
        bars.append(
            f'<text class="bar-val" x="{x + bw / 2:.1f}" y="{y - 4:.1f}" '
            f'text-anchor="middle">{count}</text>'
        )
        labels.append(
            f'<text class="bar-lbl" x="{x + bw / 2:.1f}" y="{h - 8:.1f}" '
            f'text-anchor="middle">{escape(day[5:])}</text>'
        )
    grid = (
        f'<line class="grid" x1="0" y1="{pad_t + plot_h:.1f}" '
        f'x2="{w}" y2="{pad_t + plot_h:.1f}" />'
    )
    return (
        f'<svg class="chart" viewBox="0 0 {w} {h}" role="img" '
        f'aria-label="Pins posted per day">{grid}{"".join(bars)}{"".join(labels)}</svg>'
    )


def _stat(value, label, tone="") -> str:
    tone_cls = f" stat--{tone}" if tone else ""
    return (
        f'<div class="stat{tone_cls}"><span class="stat-val">{value}</span>'
        f'<span class="stat-lbl">{escape(label)}</span></div>'
    )


def render_body(d: dict) -> str:
    p, b = d["pinterest"], d["blog"]
    gen = d["generated"].strftime("%d %b %Y, %H:%M UTC")

    # ---- headline health ---------------------------------------------------
    both_paused = not p["live"] and not b["is_live"]
    if both_paused:
        health_tone, health_txt = "paused", "Both pipelines paused"
    elif p["live"] and b["is_live"]:
        health_tone, health_txt = "live", "All pipelines live"
    else:
        health_tone, health_txt = "mixed", "Partially live"

    p_tone, p_txt = _status(p["live"])
    b_tone, b_txt = _status(b["is_live"])

    # ---- top KPI row -------------------------------------------------------
    queue_tone = "crit" if b["queue_len"] <= 1 else "warn" if b["queue_len"] <= 3 else "ok"
    stats = "".join(
        [
            _stat(p["total"], "Pins posted"),
            _stat(b["live"], "Blog posts live"),
            _stat(b["queue_len"], "Topics in queue", queue_tone),
            _stat(p["shoot_count"], "Shoots drawn from"),
        ]
    )

    # ---- Pinterest card ----------------------------------------------------
    since = p["days_since"]
    since_txt = (
        "today" if since == 0 else f"{since} day{'s' if since != 1 else ''} ago"
        if since is not None else "—"
    )
    idle_flag = (
        '<span class="flag flag--warn">Idle — paused</span>'
        if not p["live"] and since is not None and since > 2
        else ""
    )
    shoot_rows = "".join(
        f'<li><span class="shoot-name">{escape(name)}</span>'
        f'<span class="shoot-bar" style="--w:{round(100 * c / p["total"]) if p["total"] else 0}%">'
        f'</span><span class="shoot-n">{c}</span></li>'
        for name, c in p["shoots"][:5]
    )
    concentration = (
        f'<p class="note note--warn">{p["top_shoot_pct"]}% of all pins come from a single '
        f'shoot (<em>{escape(p["top_shoot"]["name"])}</em>). The pin pipeline is running low '
        f'on fresh photos — add more to the Drive folder to widen coverage.</p>'
        if p["top_shoot_pct"] >= 60
        else ""
    )

    pinterest_card = f"""
    <section class="card">
      <header class="card-head">
        <h2>Pinterest</h2>
        <span class="pill pill--{p_tone}">{p_txt}</span>
      </header>
      <p class="card-sub">{escape(p['cadence'])} · up to {p['max_per_run']} pins/run {idle_flag}</p>
      <div class="chart-wrap">{_bar_chart(p['series'], p['peak_day'])}</div>
      <dl class="facts">
        <div><dt>Active days</dt><dd>{p['active_days']}</dd></div>
        <div><dt>Busiest day</dt><dd>{p['peak_day']} pins</dd></div>
        <div><dt>Last pin</dt><dd>{since_txt}</dd></div>
      </dl>
      <h3 class="mini-h">Where the pins came from</h3>
      <ul class="shoots">{shoot_rows}</ul>
      {concentration}
    </section>"""

    # ---- Blog card ---------------------------------------------------------
    if b["queue"]:
        queue_items = "".join(f"<li>{escape(k)}</li>" for k in b["queue"])
        queue_block = f'<ul class="queue">{queue_items}</ul>'
    else:
        queue_block = '<p class="empty">Queue is empty — add topics to config.yaml.</p>'
    queue_note = (
        f'<p class="note note--{queue_tone}">Only {b["queue_len"]} topic'
        f'{"s" if b["queue_len"] != 1 else ""} left to write. Run the '
        f'<code>topic-scout</code> agent to refill the queue before it runs dry.</p>'
        if b["queue_len"] <= 2
        else ""
    )
    post_rows = "".join(
        f'<li><span class="post-date">{escape(r["date"])}</span>'
        f'<span class="post-title">{escape(r["title"])}</span></li>'
        for r in b["posts"]
    )

    blog_card = f"""
    <section class="card">
      <header class="card-head">
        <h2>SEO Blog</h2>
        <span class="pill pill--{b_tone}">{b_txt}</span>
      </header>
      <p class="card-sub">{escape(b['cadence'])} · up to {b['max_per_run']} post/run · Framer “{escape(b['collection'])}” collection</p>
      <dl class="facts">
        <div><dt>Published</dt><dd>{b['live']}</dd></div>
        <div><dt>Keywords done</dt><dd>{b['done_count']}</dd></div>
        <div><dt>Queue</dt><dd class="{'val-crit' if queue_tone=='crit' else ''}">{b['queue_len']} left</dd></div>
      </dl>
      <h3 class="mini-h">Published posts</h3>
      <ul class="posts">{post_rows}</ul>
      <h3 class="mini-h">Next up in the queue</h3>
      {queue_block}
      {queue_note}
    </section>"""

    site = escape(d["website"])
    site_label = re.sub(r"^https?://(www\.)?", "", d["website"]).rstrip("/")

    return f"""<style>{_CSS}</style>
<main class="wrap">
  <header class="masthead">
    <div class="brand">
      <span class="brand-mark">◆</span>
      <div>
        <h1>{escape(d['brand'])}</h1>
        <p class="tagline">Marketing automation control room{' · ' + escape(site_label) if site_label else ''}</p>
      </div>
    </div>
    <div class="health">
      <span class="pill pill--{health_tone} pill--lg">{escape(health_txt)}</span>
      <span class="stamp">Updated {escape(gen)}</span>
    </div>
  </header>

  <section class="kpis">{stats}</section>

  <div class="cards">
    {pinterest_card}
    {blog_card}
  </div>

  <footer class="foot">
    <span>Generated from committed state — <code>state/</code> + <code>config.yaml</code>. No live API calls.</span>
    {f'<a href="{site}">{escape(site_label)}</a>' if site else ''}
  </footer>
</main>"""


# --------------------------------------------------------------------------- #
# Styles
# --------------------------------------------------------------------------- #
_CSS = """
:root {
  --bg: #f4f2ee; --panel: #fbfaf8; --ink: #21201c; --muted: #6f6b62;
  --line: #e3ded4; --line-strong: #d3ccbe;
  --accent: #2f7d84; --accent-soft: #d9ebec;
  --ok: #3f8f5a; --warn: #b7822b; --crit: #b5432f; --paused: #8a8577;
  --shadow: 0 1px 2px rgba(30,28,22,.05), 0 8px 24px rgba(30,28,22,.05);
  --mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  --serif: Georgia, "Iowan Old Style", "Times New Roman", serif;
  --sans: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #16161a; --panel: #1f1f25; --ink: #ece9e2; --muted: #9a958b;
    --line: #2c2c34; --line-strong: #3a3a44;
    --accent: #5bb6bd; --accent-soft: #1c3a3d;
    --ok: #5cc27e; --warn: #d8a24e; --crit: #e0715a; --paused: #8f8a7e;
    --shadow: 0 1px 2px rgba(0,0,0,.3), 0 10px 30px rgba(0,0,0,.35);
  }
}
:root[data-theme="light"] {
  --bg: #f4f2ee; --panel: #fbfaf8; --ink: #21201c; --muted: #6f6b62;
  --line: #e3ded4; --line-strong: #d3ccbe;
  --accent: #2f7d84; --accent-soft: #d9ebec;
  --ok: #3f8f5a; --warn: #b7822b; --crit: #b5432f; --paused: #8a8577;
  --shadow: 0 1px 2px rgba(30,28,22,.05), 0 8px 24px rgba(30,28,22,.05);
}
:root[data-theme="dark"] {
  --bg: #16161a; --panel: #1f1f25; --ink: #ece9e2; --muted: #9a958b;
  --line: #2c2c34; --line-strong: #3a3a44;
  --accent: #5bb6bd; --accent-soft: #1c3a3d;
  --ok: #5cc27e; --warn: #d8a24e; --crit: #e0715a; --paused: #8f8a7e;
  --shadow: 0 1px 2px rgba(0,0,0,.3), 0 10px 30px rgba(0,0,0,.35);
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink);
  font-family: var(--sans); line-height: 1.5;
  -webkit-font-smoothing: antialiased; }
.wrap { max-width: 1040px; margin: 0 auto; padding: clamp(20px, 4vw, 44px); }

.masthead { display: flex; flex-wrap: wrap; gap: 16px 24px;
  justify-content: space-between; align-items: flex-start;
  padding-bottom: 22px; border-bottom: 1px solid var(--line); }
.brand { display: flex; align-items: center; gap: 14px; }
.brand-mark { color: var(--accent); font-size: 26px; line-height: 1; }
.masthead h1 { font-family: var(--serif); font-weight: 600;
  font-size: clamp(22px, 3.4vw, 30px); margin: 0; letter-spacing: -.01em;
  text-wrap: balance; }
.tagline { margin: 2px 0 0; color: var(--muted); font-size: 13.5px; }
.health { display: flex; flex-direction: column; align-items: flex-end; gap: 7px; }
.stamp { color: var(--muted); font-size: 12px; font-variant-numeric: tabular-nums; }

.pill { display: inline-flex; align-items: center; gap: 7px;
  font-size: 12px; font-weight: 600; letter-spacing: .02em;
  padding: 4px 11px; border-radius: 999px; white-space: nowrap;
  border: 1px solid transparent; }
.pill::before { content: ""; width: 7px; height: 7px; border-radius: 50%;
  background: currentColor; }
.pill--lg { font-size: 13px; padding: 6px 14px; }
.pill--live { color: var(--ok); background: color-mix(in srgb, var(--ok) 13%, transparent);
  border-color: color-mix(in srgb, var(--ok) 30%, transparent); }
.pill--paused { color: var(--paused); background: color-mix(in srgb, var(--paused) 15%, transparent);
  border-color: color-mix(in srgb, var(--paused) 32%, transparent); }
.pill--mixed { color: var(--warn); background: color-mix(in srgb, var(--warn) 15%, transparent);
  border-color: color-mix(in srgb, var(--warn) 32%, transparent); }

.kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;
  margin: 24px 0; }
.stat { background: var(--panel); border: 1px solid var(--line);
  border-radius: 12px; padding: 16px 18px; box-shadow: var(--shadow);
  display: flex; flex-direction: column; gap: 4px; }
.stat-val { font-size: clamp(26px, 4vw, 34px); font-weight: 650;
  font-variant-numeric: tabular-nums; letter-spacing: -.02em; line-height: 1; }
.stat-lbl { color: var(--muted); font-size: 12.5px; }
.stat--ok { border-left: 3px solid var(--ok); }
.stat--warn .stat-val { color: var(--warn); }
.stat--warn { border-left: 3px solid var(--warn); }
.stat--crit .stat-val { color: var(--crit); }
.stat--crit { border-left: 3px solid var(--crit); }

.cards { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
.card { background: var(--panel); border: 1px solid var(--line);
  border-radius: 14px; padding: 20px 22px; box-shadow: var(--shadow);
  display: flex; flex-direction: column; }
.card-head { display: flex; align-items: center; justify-content: space-between;
  gap: 12px; }
.card-head h2 { font-family: var(--serif); font-weight: 600; font-size: 19px;
  margin: 0; }
.card-sub { color: var(--muted); font-size: 12.5px; margin: 4px 0 16px; }

.flag { display: inline-block; font-size: 11px; font-weight: 600;
  padding: 1px 7px; border-radius: 6px; margin-left: 4px; }
.flag--warn { color: var(--warn);
  background: color-mix(in srgb, var(--warn) 16%, transparent); }

.chart-wrap { margin: 2px 0 18px; }
.chart { width: 100%; height: auto; overflow: visible; }
.chart .bar { fill: var(--accent); opacity: .42; }
.chart .bar--last { opacity: .9; }
.chart .bar-val { fill: var(--muted); font-size: 10px;
  font-family: var(--mono); font-variant-numeric: tabular-nums; }
.chart .bar-lbl { fill: var(--muted); font-size: 9.5px; font-family: var(--mono); }
.chart .grid { stroke: var(--line-strong); stroke-width: 1; }

.facts { display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 10px; margin: 0 0 18px; }
.facts div { background: var(--bg); border: 1px solid var(--line);
  border-radius: 9px; padding: 9px 11px; }
.facts dt { color: var(--muted); font-size: 11px; margin: 0 0 3px; }
.facts dd { margin: 0; font-size: 15px; font-weight: 600;
  font-variant-numeric: tabular-nums; }
.val-crit { color: var(--crit); }

.mini-h { font-size: 11px; text-transform: uppercase; letter-spacing: .07em;
  color: var(--muted); margin: 6px 0 9px; font-weight: 700; }

.shoots { list-style: none; margin: 0 0 4px; padding: 0;
  display: flex; flex-direction: column; gap: 7px; }
.shoots li { display: grid; grid-template-columns: 1fr 84px auto;
  align-items: center; gap: 10px; font-size: 12.5px; }
.shoot-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.shoot-bar { height: 7px; border-radius: 4px; background: var(--line-strong);
  position: relative; }
.shoot-bar::before { content: ""; position: absolute; inset: 0;
  width: var(--w); background: var(--accent); border-radius: 4px; opacity: .7; }
.shoot-n { font-family: var(--mono); font-variant-numeric: tabular-nums;
  color: var(--muted); font-size: 12px; }

.posts, .queue { list-style: none; margin: 0 0 4px; padding: 0;
  display: flex; flex-direction: column; }
.posts li { display: flex; gap: 12px; padding: 7px 0; font-size: 13px;
  border-bottom: 1px solid var(--line); }
.posts li:last-child { border-bottom: 0; }
.post-date { font-family: var(--mono); color: var(--muted); font-size: 11.5px;
  white-space: nowrap; padding-top: 1px; }
.post-title { font-weight: 500; }
.queue { counter-reset: q; gap: 6px; }
.queue li { counter-increment: q; position: relative; padding: 6px 0 6px 26px;
  font-size: 13px; border-bottom: 1px solid var(--line); }
.queue li:last-child { border-bottom: 0; }
.queue li::before { content: counter(q); position: absolute; left: 0; top: 6px;
  width: 18px; height: 18px; border-radius: 5px; background: var(--accent-soft);
  color: var(--accent); font-size: 10.5px; font-weight: 700; font-family: var(--mono);
  display: grid; place-items: center; }

.note { font-size: 12.5px; line-height: 1.45; margin: 12px 0 0;
  padding: 10px 12px; border-radius: 9px; border: 1px solid; }
.note code { font-family: var(--mono); font-size: 11.5px;
  background: color-mix(in srgb, var(--ink) 8%, transparent);
  padding: 1px 5px; border-radius: 4px; }
.note--warn { color: var(--warn);
  background: color-mix(in srgb, var(--warn) 9%, transparent);
  border-color: color-mix(in srgb, var(--warn) 28%, transparent); }
.note--crit { color: var(--crit);
  background: color-mix(in srgb, var(--crit) 9%, transparent);
  border-color: color-mix(in srgb, var(--crit) 28%, transparent); }
.note--ok { color: var(--ok);
  background: color-mix(in srgb, var(--ok) 9%, transparent);
  border-color: color-mix(in srgb, var(--ok) 26%, transparent); }
.note em { font-style: italic; }

.empty { color: var(--muted); font-size: 12.5px; font-style: italic; margin: 4px 0; }

.foot { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 8px;
  margin-top: 26px; padding-top: 16px; border-top: 1px solid var(--line);
  color: var(--muted); font-size: 12px; }
.foot code { font-family: var(--mono); font-size: 11px; }
.foot a { color: var(--accent); text-decoration: none; }
.foot a:hover { text-decoration: underline; }

@media (max-width: 720px) {
  .kpis { grid-template-columns: repeat(2, 1fr); }
  .cards { grid-template-columns: 1fr; }
  .health { align-items: flex-start; }
}
"""


def render_document(d: dict) -> str:
    return (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{escape(d['brand'])} — Automation Dashboard</title>\n"
        "</head>\n<body>\n" + render_body(d) + "\n</body>\n</html>\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Build the automation ops dashboard.")
    ap.add_argument("-o", "--out", default=str(ROOT / "dashboard.html"),
                    help="output path for the standalone HTML (default: dashboard.html)")
    ap.add_argument("--fragment", help="also write a body-only fragment to this path")
    args = ap.parse_args()

    data = collect()
    Path(args.out).write_text(render_document(data))
    print(f"Wrote {args.out}")
    if args.fragment:
        Path(args.fragment).write_text(render_body(data))
        print(f"Wrote {args.fragment}")


if __name__ == "__main__":
    main()
