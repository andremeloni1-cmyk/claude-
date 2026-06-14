"""Load brand settings from config.yaml and secrets from the environment."""

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
class Config:
    # Brand / behaviour (from config.yaml)
    website_url: str
    business_name: str
    niche: str
    location: str
    target_audience: str
    board_name: str
    board_description: str
    utm: dict
    model: str
    max_pins_per_run: int

    # Secrets / per-environment (from env vars)
    anthropic_api_key: str
    pinterest_access_token: str
    google_service_account_json: str
    gdrive_folder_id: str

    # Resolved paths
    state_path: Path = field(default=_REPO_ROOT / "state" / "posted.json")


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ConfigError(
            f"Missing required environment variable {name!r}. "
            "Set it as a GitHub Actions secret (or export it locally)."
        )
    return value


def load() -> Config:
    if not _CONFIG_PATH.exists():
        raise ConfigError(f"config.yaml not found at {_CONFIG_PATH}")

    with _CONFIG_PATH.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    def clean(key: str, default: str = "") -> str:
        return str(data.get(key, default)).strip()

    return Config(
        website_url=clean("website_url"),
        business_name=clean("business_name"),
        niche=clean("niche"),
        location=clean("location"),
        target_audience=clean("target_audience"),
        board_name=clean("board_name", "My Photography"),
        board_description=clean("board_description"),
        utm=data.get("utm") or {},
        model=clean("model", "claude-opus-4-8"),
        max_pins_per_run=int(data.get("max_pins_per_run", 4)),
        anthropic_api_key=_require_env("ANTHROPIC_API_KEY"),
        pinterest_access_token=_require_env("PINTEREST_ACCESS_TOKEN"),
        google_service_account_json=_require_env("GOOGLE_SERVICE_ACCOUNT_JSON"),
        gdrive_folder_id=_require_env("GDRIVE_FOLDER_ID"),
    )
