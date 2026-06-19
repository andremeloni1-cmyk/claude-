"""One-time helper: get an Etsy OAuth refresh token for the etsy-automation skill.

Run this locally ONCE, after your Etsy app's API key shows "Approved" at
https://www.etsy.com/developers/your-apps. It walks you through Etsy's
OAuth 2.0 + PKCE flow and prints the values to store as secrets:

    ETSY_API_KEY            (your app's keystring)
    ETSY_SHARED_SECRET      (your app's shared secret)
    ETSY_REFRESH_TOKEN

You'll also need ETSY_SHOP_ID — find it in Shop Manager -> Settings ->
Options (it's in that page's URL) — there's no API lookup for it until
you're authenticated, so grab it manually.

After this one-time setup, the skill refreshes its own access token from
the refresh token on every run.

Usage:
    pip install requests
    python .claude/skills/etsy-automation/scripts/get_etsy_refresh_token.py
"""

from __future__ import annotations

import base64
import hashlib
import secrets
import urllib.parse

import requests

AUTH_URL = "https://www.etsy.com/oauth/connect"
TOKEN_URL = "https://api.etsy.com/v3/public/oauth/token"
SCOPES = "listings_w listings_r shops_r"
TIMEOUT = 30


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def main() -> None:
    print("Etsy refresh-token setup\n" + "=" * 30)
    print(
        "Your app's API key must show as 'Approved' on\n"
        "https://www.etsy.com/developers/your-apps before this will work.\n"
    )
    keystring = input("Keystring (API key): ").strip()
    shared_secret = input("Shared secret: ").strip()
    redirect_uri = input(
        "Redirect URI (must EXACTLY match one configured in your app settings,\n"
        "  e.g. https://localhost/ ): "
    ).strip()

    code_verifier = _b64url(secrets.token_bytes(32))
    code_challenge = _b64url(hashlib.sha256(code_verifier.encode()).digest())
    state = _b64url(secrets.token_bytes(16))

    params = urllib.parse.urlencode(
        {
            "response_type": "code",
            "client_id": keystring,
            "redirect_uri": redirect_uri,
            "scope": SCOPES,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
    )
    print("\n1) Open this URL in your browser and approve access:\n")
    print(f"   {AUTH_URL}?{params}\n")
    print(
        "2) Your browser will redirect to your redirect URI with '?code=...'\n"
        "   in the address bar (the page itself may fail to load — that's fine)."
    )
    redirected = input("3) Paste the full redirected URL (or just the code): ").strip()

    code = redirected
    returned_state = None
    if "code=" in redirected:
        query = urllib.parse.urlparse(redirected).query
        parsed = urllib.parse.parse_qs(query)
        code = parsed.get("code", [""])[0]
        returned_state = parsed.get("state", [""])[0]
    code = code.split("#")[0]

    if returned_state and returned_state != state:
        raise SystemExit(
            "State mismatch -- the redirected URL doesn't match this session. "
            "Start over and don't reuse an old link."
        )

    resp = requests.post(
        TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "authorization_code",
            "client_id": keystring,
            "redirect_uri": redirect_uri,
            "code": code,
            "code_verifier": code_verifier,
        },
        timeout=TIMEOUT,
    )
    if resp.status_code >= 400:
        raise SystemExit(f"\nToken exchange failed ({resp.status_code}): {resp.text}")

    data = resp.json()
    refresh_token = data.get("refresh_token")
    access_token = data.get("access_token")
    if not refresh_token or not access_token:
        raise SystemExit(f"\nNo tokens in response: {data}")

    user_id = access_token.split(".")[0]

    print("\n=== SUCCESS -- add these as secrets ===\n")
    print(f"ETSY_API_KEY        = {keystring}")
    print(f"ETSY_SHARED_SECRET  = {shared_secret}")
    print(f"ETSY_REFRESH_TOKEN  = {refresh_token}")
    print(
        f"\nYour Etsy user id is {user_id}. Find your numeric ETSY_SHOP_ID in "
        "Shop Manager -> Settings -> Options (it's in that page's URL) and "
        "store it as a secret too."
    )
    print(
        "\nNote: Etsy rotates the refresh token every time it's used. If "
        "create_listing.py prints a new one, update the ETSY_REFRESH_TOKEN "
        "secret with it."
    )


if __name__ == "__main__":
    main()
