# Etsy API access: one-time setup

Etsy manually reviews every app before its API key works at all — this
applies to the **API key itself**, not just to specific OAuth scopes. Until
an app is approved, even basic read-only calls (like looking up taxonomy
categories) return errors. There's no documented way around this review; it
exists to keep spam/scraper apps off Etsy's API.

If you've registered an app and it keeps getting denied, the most common
reasons (per developer reports and Etsy's own app-registration guidance)
are:

- **The description reads like a bot/scraper.** Avoid words like "bot",
  "scraper", "automate", "automatically" in the app name or description.
  Etsy's reviewers are specifically screening for tools that look like mass
  automation or scraping, even when the actual use is a single seller
  managing their own shop.
- **Vague scope.** Be concrete: state that this is a personal tool for one
  specific shop (name it) to create and manage that shop's own listings —
  not a multi-shop or third-party tool.
- **Requesting more than you need.** Only request `listings_w`,
  `listings_r`, and `shops_r`. Anything broader (financial data, other
  shops' data) raises more scrutiny for no benefit here.
- **Incomplete registration.** Fill in every optional field in the app
  registration form (website/use-case fields especially) — sparse
  submissions are reviewed more harshly.

If a resubmission is still denied, the only official escalation path is to
email **developers@etsy.com** describing the app's exact purpose and asking
what specifically needs to change. There's no public appeals process beyond
that channel.

## Once your app shows "Approved"

Check at <https://www.etsy.com/developers/your-apps>.

1. Install the one dependency these scripts need:
   ```bash
   pip install requests
   ```
2. Run the one-time OAuth helper locally (it opens a browser flow and asks
   you to paste back a redirect URL — this can't run unattended):
   ```bash
   python .claude/skills/etsy-automation/scripts/get_etsy_refresh_token.py
   ```
   It prints `ETSY_API_KEY`, `ETSY_SHARED_SECRET`, and `ETSY_REFRESH_TOKEN`.
   Store all three as secrets (GitHub Actions secrets, or exported locally
   for ad-hoc runs).
3. Find your shop id manually — there's no API lookup for it until you're
   authenticated. Shop Manager → Settings → Options; it's in that page's
   URL. Store it as `ETSY_SHOP_ID`.
4. From then on, `scripts/create_listing.py` refreshes its own access token
   from `ETSY_REFRESH_TOKEN` on every run. Etsy rotates the refresh token
   every time it's used — if the script prints a new one to stderr, update
   the stored secret with it, or the next run will fail.

Once these are set, the etsy-automation skill switches from draft-copy mode
to live API mode automatically — no other change needed.
