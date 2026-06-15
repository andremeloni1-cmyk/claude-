"""Load profile-pipeline settings from config.yaml and secrets from the environment.

Brand settings (website_url, business_name, niche, location, target_audience,
model) are shared with the other automations and read from the top level of
config.yaml. Everything profile-specific lives under the ``profile:`` key.
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
class ProfileConfig:
    # Shared brand settings (top level of config.yaml).
    website_url: str
    business_name: str
    niche: str
    location: str
    service_area: str
    target_audience: str
    model: str

    # Profile-specific settings (config.yaml -> profile:).
    collection_name: str
    category: str
    field_map: dict
    max_per_run: int

    # Secrets / per-environment (from env vars).
    anthropic_api_key: str
    google_service_account_json: str
    gdrive_folder_id: str

    # Resolved paths.
    state_path: Path = field(default=_REPO_ROOT / "state" / "profile.json")
    published_dir: Path = field(default=_REPO_ROOT / "published_profile")


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ConfigError(
            f"Missing required environment variable {name!r}. "
            "Set it as a GitHub Actions secret (or export it locally)."
        )
    return value


def load() -> ProfileConfig:
    if not _CONFIG_PATH.exists():
        raise ConfigError(f"config.yaml not found at {_CONFIG_PATH}")

    with _CONFIG_PATH.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    profile = data.get("profile") or {}
    if not profile:
        raise ConfigError("config.yaml has no 'profile:' section. See README.")

    def clean(key: str, default: str = "") -> str:
        return str(data.get(key, default)).strip()

    return ProfileConfig(
        website_url=clean("website_url"),
        business_name=clean("business_name"),
        niche=clean("niche"),
        location=clean("location"),
        service_area=clean("service_area"),
        target_audience=clean("target_audience"),
        model=clean("model", "claude-opus-4-8"),
        collection_name=str(profile.get("collection_name", "Portfolio")).strip(),
        category=str(profile.get("category", "Wedding")).strip(),
        field_map=profile.get("field_map") or {},
        max_per_run=int(profile.get("max_per_run", 8)),
        anthropic_api_key=_require_env("ANTHROPIC_API_KEY"),
        google_service_account_json=_require_env("GOOGLE_SERVICE_ACCOUNT_JSON"),
        gdrive_folder_id=_require_env("GDRIVE_FOLDER_ID"),
    )
