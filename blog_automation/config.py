"""Load blog-pipeline settings from config.yaml and secrets from the environment.

Brand settings (website_url, business_name, niche, location, target_audience,
model) are shared with the Pinterest automation and read from the top level of
config.yaml. Everything blog-specific lives under the ``blog:`` key.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_CONFIG_PATH = _REPO_ROOT / "config.yaml"


class ConfigError(RuntimeError):
    """Raised when required configuration or secrets are missing."""


@dataclass
class Topic:
    keyword: str
    notes: str = ""


@dataclass
class BlogConfig:
    # Shared brand settings (top level of config.yaml).
    website_url: str
    business_name: str
    niche: str
    location: str
    service_area: str
    target_audience: str
    model: str

    # Blog-specific settings (config.yaml -> blog:).
    collection_name: str
    author: str
    field_map: dict
    images_per_post: int
    image_candidate_pool: int
    avoid_reusing_images: bool
    max_posts_per_run: int
    internal_links: list
    topics: list  # list[Topic]
    auto_research: bool
    research_batch_size: int

    # Secrets / per-environment (from env vars).
    anthropic_api_key: str
    google_service_account_json: str
    gdrive_folder_id: str

    # Resolved paths.
    state_path: Path = field(default=_REPO_ROOT / "state" / "blog.json")
    published_dir: Path = field(default=_REPO_ROOT / "published")


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ConfigError(
            f"Missing required environment variable {name!r}. "
            "Set it as a GitHub Actions secret (or export it locally)."
        )
    return value


def load() -> BlogConfig:
    if not _CONFIG_PATH.exists():
        raise ConfigError(f"config.yaml not found at {_CONFIG_PATH}")

    with _CONFIG_PATH.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    blog = data.get("blog") or {}
    if not blog:
        raise ConfigError("config.yaml has no 'blog:' section. See README.")

    def clean(key: str, default: str = "") -> str:
        return str(data.get(key, default)).strip()

    raw_topics = blog.get("topics") or []
    topics = [
        Topic(keyword=str(t.get("keyword", "")).strip(), notes=str(t.get("notes", "")).strip())
        for t in raw_topics
        if str(t.get("keyword", "")).strip()
    ]
    if not topics:
        raise ConfigError("No blog topics configured. Add keywords under blog.topics in config.yaml.")

    return BlogConfig(
        website_url=clean("website_url"),
        business_name=clean("business_name"),
        niche=clean("niche"),
        location=clean("location"),
        service_area=clean("service_area"),
        target_audience=clean("target_audience"),
        model=clean("model", "claude-opus-4-8"),
        collection_name=str(blog.get("collection_name", "Blog")).strip(),
        author=str(blog.get("author", "")).strip(),
        field_map=blog.get("field_map") or {},
        images_per_post=int(blog.get("images_per_post", 4)),
        image_candidate_pool=int(blog.get("image_candidate_pool", 24)),
        avoid_reusing_images=bool(blog.get("avoid_reusing_images", True)),
        max_posts_per_run=int(blog.get("max_posts_per_run", 1)),
        internal_links=blog.get("internal_links") or [],
        topics=topics,
        auto_research=bool(blog.get("auto_research", True)),
        research_batch_size=int(blog.get("research_batch_size", 3)),
        anthropic_api_key=_require_env("ANTHROPIC_API_KEY"),
        google_service_account_json=_require_env("GOOGLE_SERVICE_ACCOUNT_JSON"),
        gdrive_folder_id=_require_env("GDRIVE_FOLDER_ID"),
    )


def _yaml_dquote(value: str) -> str:
    """Escape a string for a YAML double-quoted scalar."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def append_topics(new_topics: list[Topic]) -> None:
    """Append new topic entries to the end of config.yaml's blog.topics list.

    Matches the file's existing formatting exactly (4-space indent for
    ``- keyword:``, 6-space indent for ``notes:``, double-quoted scalars) so
    the result stays valid for both the Python and Node YAML parsers and
    keeps every existing comment and entry untouched.
    """
    if not new_topics:
        return

    raw = _CONFIG_PATH.read_text(encoding="utf-8")
    lines = [
        f'    - keyword: "{_yaml_dquote(t.keyword)}"\n'
        f'      notes: "{_yaml_dquote(t.notes)}"\n'
        for t in new_topics
        if t.keyword
    ]
    _CONFIG_PATH.write_text(raw.rstrip("\n") + "\n" + "".join(lines), encoding="utf-8")
