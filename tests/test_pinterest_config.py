"""Tests for pinterest_automation/config.py credential resolution.

Covers the posting-credential validation in load() (the main failure mode for a
misconfigured GitHub Action), the use_postiz switch, and token resolution.

Run with:
    cd /home/user/claude- && python3 -m pytest tests/test_pinterest_config.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import pinterest_automation.config as config  # noqa: E402


# ---------------------------------------------------------------------------
# _require_env
# ---------------------------------------------------------------------------


def test_require_env_returns_stripped_value(monkeypatch):
    monkeypatch.setenv("SOME_VAR", "  value  ")
    assert config._require_env("SOME_VAR") == "value"


def test_require_env_raises_when_missing(monkeypatch):
    monkeypatch.delenv("SOME_VAR", raising=False)
    with pytest.raises(config.ConfigError):
        config._require_env("SOME_VAR")


# ---------------------------------------------------------------------------
# Config.use_postiz / resolve_pinterest_token
# ---------------------------------------------------------------------------


def _config(**overrides):
    base = dict(
        website_url="https://x.com", business_name="b", niche="n", location="l",
        target_audience="t", service_area="s", board_name="bn", board_description="bd",
        utm={}, model="m", max_pins_per_run=4,
        anthropic_api_key="ak", google_service_account_json="{}", gdrive_folder_id="gf",
    )
    base.update(overrides)
    return config.Config(**base)


def test_use_postiz_true_when_key_present():
    assert _config(postiz_api_key="pk").use_postiz is True


def test_use_postiz_false_when_key_absent():
    assert _config().use_postiz is False


def test_resolve_token_returns_static_access_token_when_no_refresh():
    cfg = _config(pinterest_access_token="static-token")
    assert cfg.resolve_pinterest_token() == "static-token"


def test_resolve_token_refreshes_when_refresh_token_present(monkeypatch):
    import pinterest_automation.pinterest_auth as auth

    captured = {}

    def fake_refresh(app_id, app_secret, refresh_token):
        captured.update(app_id=app_id, app_secret=app_secret, refresh_token=refresh_token)
        return "fresh-token"

    monkeypatch.setattr(auth, "refresh_access_token", fake_refresh)

    cfg = _config(
        pinterest_app_id="aid", pinterest_app_secret="asec", pinterest_refresh_token="rt"
    )
    assert cfg.resolve_pinterest_token() == "fresh-token"
    assert captured == {"app_id": "aid", "app_secret": "asec", "refresh_token": "rt"}


# ---------------------------------------------------------------------------
# load() credential validation
# ---------------------------------------------------------------------------


def _set_required_secrets(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "ak")
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", "{}")
    monkeypatch.setenv("GDRIVE_FOLDER_ID", "folder")


def _clear_posting_creds(monkeypatch):
    for var in (
        "POSTIZ_API_KEY", "POSTIZ_BASE_URL", "POSTIZ_INTEGRATION_ID",
        "PINTEREST_ACCESS_TOKEN", "PINTEREST_APP_ID", "PINTEREST_APP_SECRET",
        "PINTEREST_REFRESH_TOKEN",
    ):
        monkeypatch.delenv(var, raising=False)


def test_load_raises_when_no_posting_credentials(monkeypatch):
    _set_required_secrets(monkeypatch)
    _clear_posting_creds(monkeypatch)
    with pytest.raises(config.ConfigError):
        config.load()


def test_load_succeeds_with_postiz_key(monkeypatch):
    _set_required_secrets(monkeypatch)
    _clear_posting_creds(monkeypatch)
    monkeypatch.setenv("POSTIZ_API_KEY", "pk")
    cfg = config.load()
    assert cfg.use_postiz is True
    assert cfg.gdrive_folder_id == "folder"


def test_load_succeeds_with_full_refresh_credentials(monkeypatch):
    _set_required_secrets(monkeypatch)
    _clear_posting_creds(monkeypatch)
    monkeypatch.setenv("PINTEREST_APP_ID", "aid")
    monkeypatch.setenv("PINTEREST_APP_SECRET", "asec")
    monkeypatch.setenv("PINTEREST_REFRESH_TOKEN", "rt")
    cfg = config.load()
    assert cfg.use_postiz is False
    assert cfg.pinterest_refresh_token == "rt"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
