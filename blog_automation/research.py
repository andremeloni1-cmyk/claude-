"""Use Claude's web search tool to discover new SEO blog topics automatically.

This closes the last manual gap in the pipeline: instead of a human curating
``blog.topics`` in config.yaml forever, ``main.py`` calls here to top the
queue back up once it runs low, so the pipeline never goes idle.
"""

from __future__ import annotations

import json

import anthropic

from .config import Topic

_RESEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "topics": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": ["keyword", "notes"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["topics"],
    "additionalProperties": False,
}


def research_topics(cfg, avoid_keywords: set, count: int) -> list[Topic]:
    """Web-search for ``count`` new, non-duplicate blog topic ideas.

    ``avoid_keywords`` is every keyword already queued or written (so we never
    propose a duplicate). Returns up to ``count`` new Topic objects; returns
    fewer if Claude can't find that many genuinely distinct ideas.
    """
    if count <= 0:
        return []

    client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)

    avoid_list = "\n".join(f"- {k}" for k in sorted(avoid_keywords)) or "(none yet)"
    user = (
        f"Research {count} new, SEO-optimised blog post topic ideas for a wedding and "
        "portrait photography business.\n\n"
        f"Business: {cfg.business_name}\n"
        f"Service area: {cfg.service_area}\n"
        f"Location: {cfg.location}\n"
        f"Target audience: {cfg.target_audience}\n\n"
        "Use web search to find search terms with real, current search demand on "
        "Google related to wedding photography, engagement photography, portrait "
        "photography, or wedding planning in this service area. Prefer topics with "
        "clear local or buyer intent over generic national keywords.\n\n"
        "Do not propose any of these already-queued or already-published topics "
        f"(exact or near-duplicate keyword):\n{avoid_list}\n\n"
        f"Return exactly {count} topics as JSON only, matching the schema. For each: "
        "`keyword` is the primary SEO search phrase (lowercase, plain prose, spelled-"
        "out numbers rather than numerals), and `notes` is a 1-2 sentence brief "
        "steering the angle/intent for the writer."
    )

    response = client.messages.create(
        model=cfg.model,
        max_tokens=4096,
        system=(
            "You are an SEO strategist for a professional photography business. You "
            "research real, current search trends via web search and propose blog "
            "topics genuinely worth writing — never generic filler."
        ),
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
        messages=[{"role": "user", "content": user}],
        output_config={"format": {"type": "json_schema", "schema": _RESEARCH_SCHEMA}},
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("Model refused to research new blog topics.")

    text = next((b.text for b in response.content if b.type == "text"), "")
    data = json.loads(text) if text else {}

    seen_lower = {k.lower() for k in avoid_keywords}
    results: list[Topic] = []
    for item in data.get("topics", []):
        keyword = str(item.get("keyword", "")).strip()
        notes = str(item.get("notes", "")).strip()
        if not keyword or keyword.lower() in seen_lower:
            continue
        seen_lower.add(keyword.lower())
        results.append(Topic(keyword=keyword, notes=notes))
        if len(results) >= count:
            break
    return results
