"""Use Claude vision to write a short gallery title and honest alt text for a photo."""

from __future__ import annotations

import base64
import json

import anthropic

# Anthropic vision accepts these image media types.
_SUPPORTED_MEDIA = {"image/jpeg", "image/png", "image/gif", "image/webp"}

_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "alt_text": {"type": "string"},
    },
    "required": ["title", "alt_text"],
    "additionalProperties": False,
}

# Portfolio display limits.
_TITLE_MAX = 70
_ALT_MAX = 125


def _system_prompt(cfg) -> str:
    return (
        "You write short, elegant titles and honest alt text for photos shown "
        "in the portfolio gallery of a professional photography website.\n\n"
        f"Business: {cfg.business_name}\n"
        f"Niche: {cfg.niche}\n"
        f"Location: {cfg.location}\n"
        f"Wedding service area: {cfg.service_area}\n"
        f"Website: {cfg.website_url}\n\n"
        "You are given one photo and its original filename. The filename often "
        "contains real context such as the couple's names and the location "
        "(e.g. \"Wollongong botanical gardens Alana + Jacque-92.jpg\"). Use that "
        "context for the title when it clearly looks like real information, but "
        "never invent names, venues, or places that are not in the filename or "
        "plainly visible in the photo.\n\n"
        "Rules:\n"
        f"- title: a short, refined gallery caption, max {_TITLE_MAX} characters. "
        "Prefer a natural form like \"Alana & Jacque — Wollongong Botanical "
        "Gardens\" when the filename gives names and a place; otherwise a brief "
        "descriptive title of the moment. No quotes, no trailing punctuation, no "
        "file extensions, no numbering.\n"
        f"- alt_text: a plain, accurate description of the image for "
        f"accessibility and SEO, max {_ALT_MAX} characters. Describe only what "
        "is genuinely visible — do not invent details."
    )


def _clamp(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def generate(cfg, image_bytes: bytes, content_type: str, file_name: str) -> dict:
    """Return {title, alt_text} for one photo."""
    media_type = content_type if content_type in _SUPPORTED_MEDIA else "image/jpeg"
    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)
    response = client.messages.create(
        model=cfg.model,
        max_tokens=512,
        system=_system_prompt(cfg),
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            f"Write a portfolio title and alt text for this photo "
                            f"(filename: {file_name}). Return JSON only."
                        ),
                    },
                ],
            }
        ],
        output_config={"format": {"type": "json_schema", "schema": _SCHEMA}},
    )

    if response.stop_reason == "refusal":
        raise RuntimeError(f"Model refused to caption {file_name!r}.")

    text = next((b.text for b in response.content if b.type == "text"), "")
    data = json.loads(text)

    return {
        "title": _clamp(data["title"], _TITLE_MAX),
        "alt_text": _clamp(data["alt_text"], _ALT_MAX),
    }
