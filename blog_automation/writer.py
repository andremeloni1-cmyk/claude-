"""Use Claude to (1) pick the best photos for a topic and (2) write the SEO post."""

from __future__ import annotations

import base64
import json
import re

import anthropic

_SUPPORTED_MEDIA = {"image/jpeg", "image/png", "image/gif", "image/webp"}

# SEO field limits (search engines truncate around these).
_META_TITLE_MAX = 60
_META_DESC_MAX = 155
_EXCERPT_MAX = 200

# --- Image selection -------------------------------------------------------

_SELECT_SCHEMA = {
    "type": "object",
    "properties": {
        "chosen": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer"},
                    "alt_text": {"type": "string"},
                },
                "required": ["index", "alt_text"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["chosen"],
    "additionalProperties": False,
}


def select_images(cfg, topic, candidates: list[dict]) -> list[dict]:
    """Pick the best photos for a topic from candidate thumbnails.

    ``candidates`` is a list of {file_id, name, analysis_bytes}. Returns a list
    of {file_id, name, alt_text}, ordered best-first (first = cover), at most
    ``cfg.images_per_post`` long. The model may return fewer if few photos fit.
    """
    if not candidates:
        return []

    client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)

    content: list[dict] = []
    for i, cand in enumerate(candidates):
        content.append({"type": "text", "text": f"Photo index {i} (filename: {cand['name']}):"})
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64.standard_b64encode(cand["analysis_bytes"]).decode("utf-8"),
                },
            }
        )
    content.append(
        {
            "type": "text",
            "text": (
                f"Blog post topic: \"{topic.keyword}\".\n"
                f"Angle/notes: {topic.notes or 'n/a'}.\n\n"
                f"Choose up to {cfg.images_per_post} photos from the set above that best "
                "illustrate this post, ordered best-first (the first will be the cover "
                "image). Prefer a varied, editorial selection over near-duplicates. For "
                "each chosen photo write accurate, descriptive alt text (max 125 chars) "
                "for accessibility and SEO — describe only what is genuinely visible. "
                "Return JSON only."
            ),
        }
    )

    response = client.messages.create(
        model=cfg.model,
        max_tokens=1024,
        system=(
            "You are a photo editor for a professional photography blog. You select "
            "the most relevant, highest-quality images for an article and write honest "
            "alt text. Never invent details that are not visible in a photo."
        ),
        messages=[{"role": "user", "content": content}],
        output_config={"format": {"type": "json_schema", "schema": _SELECT_SCHEMA}},
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(f"Model refused to select images for {topic.keyword!r}.")

    text = next((b.text for b in response.content if b.type == "text"), "")
    data = json.loads(text)

    chosen: list[dict] = []
    seen: set[int] = set()
    for item in data.get("chosen", []):
        idx = int(item["index"])
        if idx in seen or not (0 <= idx < len(candidates)):
            continue
        seen.add(idx)
        cand = candidates[idx]
        chosen.append(
            {
                "file_id": cand["file_id"],
                "name": cand["name"],
                "alt_text": _clamp(str(item.get("alt_text", "")), 125),
            }
        )
        if len(chosen) >= cfg.images_per_post:
            break
    return chosen


# --- Post writing ----------------------------------------------------------

_POST_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "slug": {"type": "string"},
        "meta_title": {"type": "string"},
        "meta_description": {"type": "string"},
        "excerpt": {"type": "string"},
        "category": {"type": "string"},
        "keywords": {"type": "array", "items": {"type": "string"}},
        "body_markdown": {"type": "string"},
    },
    "required": [
        "title",
        "slug",
        "meta_title",
        "meta_description",
        "excerpt",
        "category",
        "keywords",
        "body_markdown",
    ],
    "additionalProperties": False,
}


def _system_prompt(cfg) -> str:
    links = "\n".join(
        f"- {l.get('anchor')}: {l.get('url')}" for l in cfg.internal_links if l.get("url")
    ) or "(none provided)"
    return (
        "You are an expert SEO content writer for a professional photography "
        "business. You write genuinely helpful, original long-form blog posts "
        "that rank in Google and convert readers into enquiries — never thin, "
        "spammy, or obviously AI-generated filler.\n\n"
        f"Business: {cfg.business_name}\n"
        f"Website: {cfg.website_url}\n"
        f"Niche: {cfg.niche}\n"
        f"Location: {cfg.location}\n"
        f"Wedding service area: {cfg.service_area}\n"
        f"Target audience: {cfg.target_audience}\n"
        f"Author: {cfg.author}\n\n"
        "Internal links to weave in naturally as markdown links where genuinely "
        f"relevant (do not force them):\n{links}\n\n"
        "Writing rules:\n"
        "- Demonstrate real experience and expertise (E-E-A-T): concrete, specific, "
        "practical advice a photographer would actually give.\n"
        "- Use the primary keyword naturally in the title, the first paragraph, and "
        "a few headings — never keyword-stuff.\n"
        "- Where natural, mention specific towns/regions from the service area "
        "(e.g. \"Southern Highlands\", \"South Coast\") so the post ranks for "
        "local search — but never invent venue names or claim to have shot at a "
        "specific place you have no evidence for.\n"
        "- Structure the body in markdown: an engaging intro, multiple ## H2 sections "
        "(use ### H3 where helpful), short scannable paragraphs and bullet lists, and "
        "a short ## FAQ section of 3-4 question/answer pairs near the end.\n"
        "- End with a warm call to action linking to the website.\n"
        "- Aim for roughly 900-1400 words of substantive content.\n"
        "- Never invent specific venue names, prices, client names, dates, or facts "
        "you cannot stand behind. Keep claims honest and general where unsure.\n\n"
        "Field rules:\n"
        f"- title: compelling, keyword-led H1 (not clickbait).\n"
        f"- slug: lowercase, hyphenated, keyword-based, no stop-word padding.\n"
        f"- meta_title: max {_META_TITLE_MAX} characters.\n"
        f"- meta_description: max {_META_DESC_MAX} characters, includes the keyword and a hook.\n"
        f"- excerpt: 1-2 sentence summary, max {_EXCERPT_MAX} characters.\n"
        "- category: a short, sensible blog category (e.g. 'Wedding Planning', 'Tips').\n"
        "- keywords: 5-8 search terms this post targets.\n"
        "- body_markdown: the full article in markdown (no front matter, no H1 — the "
        "title is rendered separately)."
    )


def write_post(cfg, topic, image_alts: list[str]) -> dict:
    """Write the full SEO post. ``image_alts`` lets the writer place images inline.

    For each available image, the writer inserts a placeholder ``{{image_N}}``
    (1-based) at a natural point in the body. The Framer publish step replaces
    each placeholder with the real, hosted image. The first image is the cover
    and need not be repeated inline.
    """
    client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)

    n = len(image_alts)
    if n > 1:
        placeholders = ", ".join(f"{{{{image_{i}}}}}" for i in range(2, n + 1))
        image_instr = (
            f"You have {n} photos for this post. Photo 1 is the cover (shown above the "
            f"article automatically — do not place it inline). Place these {n - 1} "
            f"placeholders, each on its own line, at natural points between sections: "
            f"{placeholders}. Use each placeholder exactly once. Their subjects are:\n"
            + "\n".join(f"- {{{{image_{i + 1}}}}}: {alt}" for i, alt in enumerate(image_alts[1:], start=1))
        )
    elif n == 1:
        image_instr = "You have 1 cover photo (shown automatically above the article). Do not add inline image placeholders."
    else:
        image_instr = "No photos are available; write the post without image placeholders."

    user = (
        f"Write a blog post targeting the keyword: \"{topic.keyword}\".\n"
        f"Angle / intent: {topic.notes or 'choose the most useful angle for the audience'}.\n\n"
        f"{image_instr}\n\nReturn JSON only."
    )

    response = client.messages.create(
        model=cfg.model,
        max_tokens=8192,
        system=_system_prompt(cfg),
        messages=[{"role": "user", "content": user}],
        output_config={"format": {"type": "json_schema", "schema": _POST_SCHEMA}},
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(f"Model refused to write post for {topic.keyword!r}.")

    text = next((b.text for b in response.content if b.type == "text"), "")
    data = json.loads(text)

    return {
        "title": " ".join(data["title"].split()),
        "slug": _slugify(data.get("slug") or data["title"]),
        "meta_title": _clamp(data["meta_title"], _META_TITLE_MAX),
        "meta_description": _clamp(data["meta_description"], _META_DESC_MAX),
        "excerpt": _clamp(data["excerpt"], _EXCERPT_MAX),
        "category": " ".join(data["category"].split()),
        "keywords": [str(k).strip() for k in data.get("keywords", []) if str(k).strip()],
        "body_markdown": data["body_markdown"].strip(),
    }


def _clamp(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:80] or "post"
