#!/usr/bin/env python3
"""Inject a market-analysis JSON snapshot into investment-dashboard.html.

The dashboard reads its dated research from an embedded
<script id="analysis-data" type="application/json"> block so it stays
fully self-contained and works offline. This script replaces that block
with the contents of market-analysis.json.

Usage:
    python3 scripts/refresh_analysis.py [market-analysis.json] [investment-dashboard.html]

Refreshing the *data* itself (current prices, ratings, commentary) is a
research task — update market-analysis.json (by hand, or by asking Claude to
re-run the research), then run this script to embed it.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "market-analysis.json"
HTML = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "investment-dashboard.html"

PATTERN = re.compile(
    r'(<script id="analysis-data" type="application/json">)(.*?)(</script>)',
    re.DOTALL,
)


def main() -> int:
    if not DATA.exists():
        print(f"error: {DATA} not found", file=sys.stderr)
        return 1
    if not HTML.exists():
        print(f"error: {HTML} not found", file=sys.stderr)
        return 1

    data = json.loads(DATA.read_text())  # validates JSON
    # keep it compact and safe to embed inside HTML
    compact = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    compact = compact.replace("</", "<\\/")  # avoid closing the <script> early

    html = HTML.read_text()
    if not PATTERN.search(html):
        print("error: analysis-data script block not found in HTML", file=sys.stderr)
        return 1

    new_html = PATTERN.sub(lambda m: m.group(1) + "\n" + compact + "\n" + m.group(3), html)
    HTML.write_text(new_html)
    print(f"Embedded {DATA.name} (asOf={data.get('asOf','?')}, "
          f"{len(data.get('companies', []))} companies, "
          f"{len(data.get('suggestions', []))} suggestions) into {HTML.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
