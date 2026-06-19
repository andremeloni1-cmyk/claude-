"""Obtain a fresh Etsy access token from a long-lived refresh token.

Etsy access tokens expire after 1 hour. Refresh tokens last ~90 days, and
Etsy issues a *new* refresh token every time one is used — so the caller
must check whether the refresh token rotated and surface that to the user.
"""

from __future__ import annotations

import requests

_TOKEN_URL = "https://api.etsy.com/v3/public/oauth/token"
_TIMEOUT = 30


class EtsyAuthError(RuntimeError):
    pass


def refresh_access_token(keystring: str, refresh_token: str) -> tuple[str, str]:
    """Exchange a refresh token for a fresh (access_token, refresh_token) pair."""
    resp = requests.post(
        _TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "refresh_token",
            "client_id": keystring,
            "refresh_token": refresh_token,
        },
        timeout=_TIMEOUT,
    )
    if resp.status_code >= 400:
        raise EtsyAuthError(
            f"Failed to refresh Etsy access token ({resp.status_code}): {resp.text}"
        )
    data = resp.json()
    access_token = data.get("access_token")
    new_refresh_token = data.get("refresh_token")
    if not access_token or not new_refresh_token:
        raise EtsyAuthError(f"Etsy refresh response missing tokens: {data}")
    return access_token, new_refresh_token
