---
name: etsy-automation
description: >
  Create Etsy listings for digital-download products (presets, templates,
  printables, guides). Writes SEO-ready titles, descriptions and tags, then
  either creates the listing as a draft via the Etsy API, or — if your Etsy
  app isn't approved yet — prints a ready-to-paste draft for Etsy's listing
  editor. Use when the user says "Etsy listing", "Etsy automation", "create
  an Etsy product", "list this on Etsy", "Etsy draft", or "publish to Etsy".
user-invocable: true
argument-hint: "<product description, or path to the photos/files to list>"
license: MIT
metadata:
  category: ecommerce
---

# Etsy Listing Automation

Turns a digital-download product (files on disk + a description of what it
is) into Etsy-ready listing copy, and creates the listing as a **draft** —
either through the Etsy API directly, or as copy-paste text if API access
isn't available yet. Nothing is ever published live without an explicit,
separate confirmation from the user.

## Two modes — pick automatically based on credentials

| | Mode A: Draft copy (works today) | Mode B: Live API |
|---|---|---|
| Requires | Nothing | An **approved** Etsy app + OAuth setup |
| What it does | Writes the listing copy and prints it formatted for manual paste into Etsy's listing editor | Calls the Etsy API to actually create the draft listing and upload images/files |
| Output | Copy-paste-ready text (+ optionally a saved spec JSON) | A real Etsy `listing_id` you can open and review |

Check mode by looking for these environment variables:
`ETSY_API_KEY`, `ETSY_SHARED_SECRET`, `ETSY_SHOP_ID`, and either
`ETSY_REFRESH_TOKEN` or `ETSY_ACCESS_TOKEN`.

- All four present → attempt Mode B.
- Any missing → use Mode A. Mention *once* (don't belabor it) that running
  Mode B requires an approved Etsy app, and point to
  `references/auth-setup.md` if the user wants to pursue that — Etsy
  manually reviews every app, including this one's API key itself, so even
  read-only calls fail until that review clears.
- If Mode B is attempted but the API returns 401/403, treat it as "not
  approved yet": explain that plainly, fall back to Mode A for this run, and
  point to `references/auth-setup.md`. Don't retry the same call.

## Workflow

1. **Gather inputs.** Ask only for what's missing:
   - What the product is (preset pack, template, printable, guide, etc.) and
     its key selling points.
   - Local paths to the listing photos (1-10 images) and the digital file(s)
     buyers receive. These stay on disk — see *File handling* below.
   - Price (and currency — default from `config.yaml`'s `etsy.currency` if
     set, otherwise ask).
   - Anything that changes the Etsy taxonomy category (e.g. "Lightroom
     presets" vs "wedding planning printable").

2. **Resolve the taxonomy category.** In Mode B, run:
   ```bash
   python3 .claude/skills/etsy-automation/scripts/create_listing.py taxonomy "<keyword>"
   ```
   and pick the best-matching `id` as `taxonomy_id`. In Mode A, ask the user
   to pick a category in Etsy's editor instead (no need to guess an id that
   can't be verified).

3. **Write the listing copy.** Etsy SEO conventions (see
   `references/digital-listing-fields.md` for the full cheat sheet):
   - Title: front-load the main keyword, ≤140 characters.
   - Description: lead with what the buyer gets and how to use it; plain
     language, no keyword stuffing.
   - Tags: exactly up to 13, each ≤20 characters, multi-word phrases buyers
     would actually search.
   - Materials (optional for digital goods): e.g. `"PDF"`, `"Digital file"`.
   - `who_made`, `when_made`, `type: "download"`, `quantity` — use the
     defaults in `config.yaml`'s `etsy:` block unless the user overrides them.

4. **Mode A — draft copy.** Print the finished title, description, tags,
   materials, price and category in a clearly labeled, easy-to-copy block.
   Offer to also save it as a spec JSON (see step 5's format) somewhere
   outside git history (e.g. `/tmp/`) in case the user wants to run Mode B
   later without redoing the copywriting.

5. **Mode B — create the draft listing.** Build a spec JSON with the listing
   fields plus `images`/`files` arrays of local paths:
   ```json
   {
     "title": "...",
     "description": "...",
     "price": 12.0,
     "quantity": 999,
     "who_made": "i_did",
     "when_made": "2020_2026",
     "taxonomy_id": 1234,
     "type": "download",
     "tags": ["...", "..."],
     "materials": ["PDF"],
     "images": ["/abs/path/photo1.jpg"],
     "files": ["/abs/path/product.zip"]
   }
   ```
   Save it to a path outside git (e.g. `/tmp/etsy_spec.json`), then:
   ```bash
   python3 .claude/skills/etsy-automation/scripts/create_listing.py create /tmp/etsy_spec.json
   ```
   Report the resulting `listing_id` and `url`. The listing is a **draft** —
   stop here.

6. **Activation is opt-in and explicit.** Never run `activate` as part of
   the same turn as `create`. Only do it if the user clearly asks to publish
   *this specific listing*, after they've had a chance to review it (ideally
   by opening the draft in Etsy). Then:
   ```bash
   python3 .claude/skills/etsy-automation/scripts/create_listing.py activate <listing_id>
   ```

7. **Record the outcome.** After a successful create (or activate) in Mode
   B, append a small entry to `state/etsy_listings.json` — `listing_id`,
   `title`, `state`, `created_at` (UTC ISO timestamp). Follow the existing
   pattern in `state/posted.json`. Only non-sensitive metadata goes here;
   never the product files or photos themselves.

## File handling — do not commit product assets

This repo is public. Listing photos and digital product files must **never**
be added to git — read them directly from the local paths the user gives
you and pass those paths straight to the upload calls. If the user asks you
to "add" or "save" their files into the repo, decline and explain why; work
from wherever the files already live on disk instead.

## Credentials

Set as environment variables / GitHub Actions secrets — never in
`config.yaml`:

| Variable | Needed for |
|---|---|
| `ETSY_API_KEY` | Both modes' API calls (Mode B only is invoked by this skill) |
| `ETSY_SHARED_SECRET` | Mode B |
| `ETSY_SHOP_ID` | Mode B |
| `ETSY_REFRESH_TOKEN` | Mode B (preferred — auto-renews; rotates on every use, see below) |
| `ETSY_ACCESS_TOKEN` | Mode B (alternative to the refresh token; expires hourly) |

`scripts/create_listing.py` refreshes the access token automatically when a
refresh token is set. If Etsy rotates it (it always does), the script prints
the new value to stderr — update the `ETSY_REFRESH_TOKEN` secret with it.

First-time setup of these credentials: `references/auth-setup.md`.

## Error handling

| Situation | Response |
|---|---|
| Missing env vars | Use Mode A silently — this is the expected default, not an error |
| 401/403 from any Etsy call | Not approved yet — explain, fall back to Mode A, point to `references/auth-setup.md` |
| `create_draft_listing` validation error (4xx with field detail) | Surface the specific field/message from the API response and fix the spec — don't guess |
| Image/file upload fails after listing created | Report the partial state (`listing_id` exists, N of M assets uploaded) so the user can retry just the upload, not recreate the listing |
