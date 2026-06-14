"""Obtain a Pinterest access token, refreshing automatically from a refresh token.

Pinterest access tokens expire (~30 days), but refresh tokens are long-lived
(~1 year). Storing the refresh token (plus app id/secret) lets each run mint a
fresh access token, so the secret never has to be touched by hand.
"""

from __future__ import annotations

import base64

import requests

_TOKEN_URL = "https://api.pinterest.com/v5/oauth/token"
_TIMEOUT = 30


class PinterestAuthError(RuntimeError):
    pass


def refresh_access_token(app_id: str, app_secret: str, refresh_token: str) -> str:
    """Exchange a refresh token for a short-lived access token."""
    creds = base64.standard_b64encode(f"{app_id}:{app_secret}".encode()).decode()
    resp = requests.post(
        _TOKEN_URL,
        headers={
            "Authorization": f"Basic {creds}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "refresh_token", "refresh_token": refresh_token},
        timeout=_TIMEOUT,
    )
    if resp.status_code >= 400:
        raise PinterestAuthError(
            f"Failed to refresh Pinterest access token ({resp.status_code}): {resp.text}"
        )
    token = resp.json().get("access_token")
    if not token:
        raise PinterestAuthError(
            "Pinterest refresh response did not contain an access_token."
        )
    return token
