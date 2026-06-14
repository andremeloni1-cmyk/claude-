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
    google_service_account_json: str
    gdrive_folder_id: str

    # Posting backend. If a Postiz API key is set, posting is routed through
    # Postiz (which holds approved Pinterest write access). Otherwise the
    # direct Pinterest API path below is used.
    postiz_api_key: str = ""
    postiz_base_url: str = ""
    postiz_integration_id: str = ""  # optional; auto-detected if blank
    pinterest_board_id: str = ""  # Postiz Pinterest board id (from config.yaml)

    # Pinterest auth: either a static access token, or app id/secret + refresh
    # token for automatic refresh (preferred — never expires in practice).
    pinterest_access_token: str = ""
    pinterest_app_id: str = ""
    pinterest_app_secret: str = ""
    pinterest_refresh_token: str = ""

    @property
    def use_postiz(self) -> bool:
        return bool(self.postiz_api_key)

    # Resolved paths
    state_path: Path = field(default=_REPO_ROOT / "state" / "posted.json")

    def resolve_pinterest_token(self) -> str:
        """Return a usable access token, refreshing from credentials if needed."""
        if self.pinterest_refresh_token:
            from . import pinterest_auth

            return pinterest_auth.refresh_access_token(
                self.pinterest_app_id,
                self.pinterest_app_secret,
                self.pinterest_refresh_token,
            )
        return self.pinterest_access_token


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

    postiz_api_key = os.environ.get("POSTIZ_API_KEY", "").strip()
    postiz_base_url = os.environ.get("POSTIZ_BASE_URL", "").strip()
    postiz_integration_id = os.environ.get("POSTIZ_INTEGRATION_ID", "").strip()

    access_token = os.environ.get("PINTEREST_ACCESS_TOKEN", "").strip()
    app_id = os.environ.get("PINTEREST_APP_ID", "").strip()
    app_secret = os.environ.get("PINTEREST_APP_SECRET", "").strip()
    refresh_token = os.environ.get("PINTEREST_REFRESH_TOKEN", "").strip()

    has_refresh = bool(app_id and app_secret and refresh_token)
    if not postiz_api_key and not access_token and not has_refresh:
        raise ConfigError(
            "Missing posting credentials. Set POSTIZ_API_KEY to post via Postiz "
            "(recommended — no Pinterest review needed), or set "
            "PINTEREST_ACCESS_TOKEN, or all of PINTEREST_APP_ID, "
            "PINTEREST_APP_SECRET and PINTEREST_REFRESH_TOKEN for the direct "
            "Pinterest API (requires Pinterest Standard access)."
        )

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
        google_service_account_json=_require_env("GOOGLE_SERVICE_ACCOUNT_JSON"),
        gdrive_folder_id=_require_env("GDRIVE_FOLDER_ID"),
        postiz_api_key=postiz_api_key,
        postiz_base_url=postiz_base_url,
        postiz_integration_id=postiz_integration_id,
        pinterest_board_id=clean("pinterest_board_id"),
        pinterest_access_token=access_token,
        pinterest_app_id=app_id,
        pinterest_app_secret=app_secret,
        pinterest_refresh_token=refresh_token,
    )
