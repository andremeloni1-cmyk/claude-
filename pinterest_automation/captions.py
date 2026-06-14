"""Generate SEO-optimised Pinterest copy from a photo using Claude vision."""

from __future__ import annotations

import base64
import json

import anthropic

# Anthropic vision accepts these image media types. Anything else we send as
# JPEG-ish bytes won't be accepted, so we map/validate before the call.
_SUPPORTED_MEDIA = {"image/jpeg", "image/png", "image/gif", "image/webp"}

# Structured-output schema. Note: JSON-schema length constraints aren't
# enforced by the API, so limits are stated in the prompt and clamped in code.
_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "alt_text": {"type": "string"},
        "keywords": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "description", "alt_text", "keywords"],
    "additionalProperties": False,
}

# Pinterest field limits.
_TITLE_MAX = 100
_DESCRIPTION_MAX = 500
_ALT_MAX = 500


def _system_prompt(cfg) -> str:
    return (
        "You are an SEO specialist writing Pinterest pin copy for a "
        "photography business. Your goal is to drive qualified visitors from "
        "Pinterest search to the photographer's website so they book a "
        "session.\n\n"
        f"Business: {cfg.business_name}\n"
        f"Niche: {cfg.niche}\n"
        f"Location: {cfg.location}\n"
        f"Target audience: {cfg.target_audience}\n\n"
        "Write copy that is keyword-rich but natural, matches what this "
        "audience actually searches for on Pinterest, and never sounds "
        "spammy or AI-generated. Describe only what is genuinely visible in "
        "the photo — do not invent details, names, or locations.\n\n"
        "Rules:\n"
        f"- title: a compelling, keyword-led headline, max {_TITLE_MAX} characters.\n"
        f"- description: 2-3 sentences of search-optimised copy, max "
        f"{_DESCRIPTION_MAX} characters, ending with 3-5 relevant lowercase "
        "hashtags.\n"
        f"- alt_text: a plain, accurate description of the image for "
        f"accessibility and SEO, max {_ALT_MAX} characters.\n"
        "- keywords: 5-8 Pinterest search terms this pin should rank for."
    )


def _clamp(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def generate(cfg, image_bytes: bytes, content_type: str, file_name: str) -> dict:
    """Return {title, description, alt_text, keywords} for one photo."""
    media_type = content_type if content_type in _SUPPORTED_MEDIA else "image/jpeg"
    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)
    response = client.messages.create(
        model=cfg.model,
        max_tokens=1024,
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
                            f"Write Pinterest pin copy for this photo "
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
        "description": _clamp(data["description"], _DESCRIPTION_MAX),
        "alt_text": _clamp(data["alt_text"], _ALT_MAX),
        "keywords": [str(k).strip() for k in data.get("keywords", []) if str(k).strip()],
    }
