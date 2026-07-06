#!/usr/bin/env python3
"""Refresh the numeric fields in market-analysis.json from a live price API.

Designed to run in CI (GitHub Actions) on a daily schedule. It updates the
things that actually move day to day — index levels, the AUD/USD rate, and
each company's approximate share price — while leaving the qualitative
analysis (theses, ratings, sector notes, suggestions) untouched. Any value
that can't be verified this run keeps its previous value, so a partial API
outage never corrupts the file.

Provider: Twelve Data (free tier covers ASX + US). Set the API key in the
TWELVEDATA_API_KEY environment variable (a GitHub Actions secret in CI).

Usage:
    TWELVEDATA_API_KEY=xxxx python3 scripts/refresh_prices.py [market-analysis.json]
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, timezone, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "market-analysis.json"
API_KEY = os.environ.get("TWELVEDATA_API_KEY", "").strip()
BASE = "https://api.twelvedata.com/price"

# Twelve Data index symbols (best-effort; a miss just leaves the level unchanged).
INDEX_SYMBOLS = {"asx200": "XJO", "sp500": "GSPC", "nasdaq": "IXIC"}
# How long to pause between calls to respect the free tier (8 requests/min).
THROTTLE_SECONDS = float(os.environ.get("TD_THROTTLE", "8"))


def fetch_price(symbol: str, exchange: str | None = None) -> float | None:
    """Return a positive float price, or None on any error/ambiguity."""
    if not API_KEY:
        return None
    params = {"symbol": symbol, "apikey": API_KEY}
    if exchange:
        params["exchange"] = exchange
    url = BASE + "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # network, JSON, HTTP — all non-fatal
        print(f"  ! {symbol}: {exc}")
        return None
    price = data.get("price") if isinstance(data, dict) else None
    if price is None:
        msg = data.get("message") or data.get("code") if isinstance(data, dict) else "no price"
        print(f"  ! {symbol}: {msg}")
        return None
    try:
        val = float(price)
    except (TypeError, ValueError):
        return None
    return val if val > 0 else None


def exchange_for(company: dict) -> str | None:
    return "ASX" if str(company.get("exchange", "")).upper() == "ASX" else None


def main() -> int:
    if not DATA.exists():
        print(f"error: {DATA} not found", file=sys.stderr)
        return 1
    if not API_KEY:
        print("error: TWELVEDATA_API_KEY is not set", file=sys.stderr)
        return 2

    doc = json.loads(DATA.read_text())
    updated, kept = 0, 0

    # Company share prices
    for c in doc.get("companies", []):
        ticker = str(c.get("ticker", "")).strip()
        if not ticker:
            continue
        px = fetch_price(ticker, exchange_for(c))
        time.sleep(THROTTLE_SECONDS)
        if px is not None:
            c["priceApprox"] = round(px, 2)
            updated += 1
            print(f"  + {ticker}: {px}")
        else:
            kept += 1

    # Index levels
    snap = doc.get("marketSnapshot", {})
    for key, sym in INDEX_SYMBOLS.items():
        lvl = fetch_price(sym)
        time.sleep(THROTTLE_SECONDS)
        if lvl is not None and isinstance(snap.get(key), dict):
            snap[key]["level"] = round(lvl, 2)
            updated += 1
            print(f"  + {key} ({sym}): {lvl}")
        else:
            kept += 1

    # AUD/USD (Twelve Data forex: USD value of 1 AUD)
    fx = fetch_price("AUD/USD")
    time.sleep(THROTTLE_SECONDS)
    if fx is not None and 0.3 < fx < 1.5:
        snap["audUsd"] = round(fx, 4)
        updated += 1
        print(f"  + audUsd: {fx}")
    else:
        kept += 1

    # Stamp the refresh date (UTC)
    today = datetime.now(timezone.utc).date().isoformat()
    doc["asOf"] = today

    # Validate + write with a trailing newline, preserving readable formatting
    text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    json.loads(text)  # guard against corruption
    DATA.write_text(text)
    print(f"Done: {updated} field(s) updated, {kept} kept, asOf={today}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
