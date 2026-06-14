"""One-time helper: get a Pinterest refresh token for hands-off posting.

Run this locally ONCE. It walks you through Pinterest's OAuth flow and prints
the three values to store as GitHub secrets:

    PINTEREST_APP_ID
    PINTEREST_APP_SECRET
    PINTEREST_REFRESH_TOKEN

After that the automation refreshes its own access token forever — you never
touch the Pinterest secret again.

Usage:
    pip install requests
    python scripts/get_pinterest_refresh_token.py
"""

from __future__ import annotations

import base64
import urllib.parse

import requests

AUTH_URL = "https://www.pinterest.com/oauth/"
TOKEN_URL = "https://api.pinterest.com/v5/oauth/token"
SCOPES = "boards:read,boards:write,pins:read,pins:write"
TIMEOUT = 30


def main() -> None:
    print("Pinterest refresh-token setup\n" + "=" * 30)
    app_id = input("App ID (client id): ").strip()
    app_secret = input("App secret: ").strip()
    redirect_uri = input(
        "Redirect URI (must EXACTLY match one configured in your app settings,\n"
        "  e.g. https://localhost/ ): "
    ).strip()

    params = urllib.parse.urlencode(
        {
            "client_id": app_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": SCOPES,
        }
    )
    print("\n1) Open this URL in your browser and click 'Give access':\n")
    print(f"   {AUTH_URL}?{params}\n")
    print(
        "2) Your browser will redirect to your redirect URI with '?code=...'\n"
        "   in the address bar (the page itself may fail to load — that's fine)."
    )
    redirected = input("3) Paste the full redirected URL (or just the code): ").strip()

    code = redirected
    if "code=" in redirected:
        query = urllib.parse.urlparse(redirected).query
        code = urllib.parse.parse_qs(query).get("code", [""])[0]
    code = code.split("#")[0]

    creds = base64.standard_b64encode(f"{app_id}:{app_secret}".encode()).decode()
    resp = requests.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {creds}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        },
        timeout=TIMEOUT,
    )
    if resp.status_code >= 400:
        raise SystemExit(f"\nToken exchange failed ({resp.status_code}): {resp.text}")

    data = resp.json()
    refresh_token = data.get("refresh_token")
    if not refresh_token:
        raise SystemExit(f"\nNo refresh_token in response: {data}")

    print("\n=== SUCCESS — add these as GitHub Actions secrets ===\n")
    print(f"PINTEREST_APP_ID         = {app_id}")
    print(f"PINTEREST_APP_SECRET     = {app_secret}")
    print(f"PINTEREST_REFRESH_TOKEN  = {refresh_token}")
    print(
        "\n(You can delete PINTEREST_ACCESS_TOKEN if you set it earlier — "
        "the refresh token replaces it.)"
    )


if __name__ == "__main__":
    main()
