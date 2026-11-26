# Photography Marketing Automations

This repo contains two hands-off marketing pipelines for a photography
business, both driven by Claude and run on a schedule by GitHub Actions:

1. **Pinterest Automation** — turns Drive photos into SEO-optimised pins (below).
2. **[SEO Blog Automation](#seo-blog-automation)** — prepares review-only plans
   for existing article bundles. CMS writes and site publishing are disabled.

A committed **[Ops Dashboard](#ops-dashboard)** (`dashboard.html`) gives you an
at-a-glance view of both pipelines' health — what's been posted, what's queued,
and whether anything is paused or running low on fresh photos.

It also includes an on-demand **[Etsy Listing Automation](#etsy-listing-automation)**
skill for creating Etsy listings for digital-download products, and the
[Claude SEO](https://github.com/AgriciDaniel/claude-seo) skill set for ad-hoc,
interactive SEO audits of the live site (see [below](#claude-seo-skill)).

---

# Pinterest Automation

Fully automated, SEO-optimised Pinterest posting for a photography business.

**How it works:** you drop photos into a Google Drive folder. On a schedule,
GitHub Actions runs this project, which:

1. Lists the photos in your Drive folder.
2. For each photo it hasn't posted yet, asks **Claude** (vision) to write
   SEO-optimised pin copy — a keyword-led title, a search-optimised
   description with hashtags, alt text, and target keywords.
3. Creates a pin directly via the **Pinterest API v5**, linking back to your
   website (with UTM tags so you can see the traffic in analytics).
4. Records what it posted in `state/posted.json` so nothing is ever
   double-posted.

You never touch it after setup — just keep adding photos to the Drive folder.

```
Google Drive folder ──▶ GitHub Actions (cron) ──▶ Claude writes SEO copy ──▶ Pinterest pin ──▶ your website
```

## Project layout

| File | Purpose |
|------|---------|
| `config.yaml` | Brand settings + behaviour (website, niche, board, post limit, model). Edit this. |
| `pinterest_automation/drive.py` | Reads photos from Google Drive (read-only). |
| `pinterest_automation/captions.py` | Claude vision → SEO pin copy. |
| `pinterest_automation/pinterest.py` | Pinterest API v5 client (boards + pins). |
| `pinterest_automation/main.py` | Orchestrates a run. |
| `state/posted.json` | Tracks posted photos (committed back automatically). |
| `.github/workflows/pinterest-automation.yml` | The scheduled run. |

## Setup

You need four secrets. Everything else lives in `config.yaml`.

### 1. Anthropic API key
- Get one at <https://console.anthropic.com> → **API Keys**.
- This is `ANTHROPIC_API_KEY`.

### 2. Google Drive (service account, headless-friendly)
1. In <https://console.cloud.google.com>, create (or pick) a project.
2. Enable the **Google Drive API** (APIs & Services → Library).
3. Create a **Service Account** (IAM & Admin → Service Accounts), then under
   its **Keys** tab, **Add key → Create new key → JSON**. Download the file.
4. The downloaded JSON contains a `client_email` like
   `something@your-project.iam.gserviceaccount.com`. **Share your Drive
   photos folder with that email** (Share → add the email → Viewer).
5. The folder id is the last part of the folder URL
   (`https://drive.google.com/drive/folders/THIS_PART`) — that's
   `GDRIVE_FOLDER_ID`.
6. `GOOGLE_SERVICE_ACCOUNT_JSON` is the service account file. You can provide
   it two ways:
   - **Raw JSON:** paste the entire contents of the `.json` file.
   - **Base64 (paste-safe, recommended):** if pasting raw JSON gets corrupted
     (the long `private_key` line is easy to mangle), base64-encode the file
     and paste that single block instead. Generate it with:
     ```bash
     base64 -w0 service-account.json   # Linux
     base64 service-account.json       # macOS
     ```
     The automation auto-detects and decodes base64.

### 3. Posting backend — Postiz (recommended)
Pinterest's own API gates the write scopes you need (`boards:write`,
`pins:write`) behind a manual **Standard access** review that can take days to
weeks. To skip that entirely, the automation can post through
[**Postiz**](https://postiz.com), which already holds approved Pinterest write
access. Set this up **once**:

1. Create a Postiz account at <https://postiz.com> (the public API requires a
   paid plan — see <https://platform.postiz.com/billing>).
2. In the Postiz dashboard, **connect your Pinterest account** as a channel.
3. Go to **Settings → Public API** and copy your **API key**.
4. Store it as the GitHub secret `POSTIZ_API_KEY`. The automation auto-detects
   your connected Pinterest channel.

Optional Postiz settings:
- `POSTIZ_INTEGRATION_ID` — pin to a specific channel instead of auto-detecting
  the Pinterest one (only needed if you connect more than one Pinterest
  account).
- `POSTIZ_BASE_URL` — point at a self-hosted Postiz instance (defaults to the
  cloud API).
- `pinterest_board_id` in `config.yaml` — the board to pin to. Leave blank to
  use the channel's default board.

If `POSTIZ_API_KEY` is set, posting goes through Postiz and the direct
Pinterest credentials below are ignored.

### 3b. Direct Pinterest API (only if you have Standard access)
If Pinterest grants your app Standard access, you can post directly instead.
Access tokens expire every ~30 days, so the automation can refresh its own
token from a long-lived refresh token. Set this up **once**:

1. You need a Pinterest **business account** (free to convert in Pinterest
   Settings → Account management).
2. Create an app at <https://developers.pinterest.com/apps/> with the
   `boards:read`, `boards:write`, `pins:read`, `pins:write` scopes, and apply
   for **Standard access** (write scopes are unavailable on the trial tier).
3. In the app settings, add a **Redirect URI** (e.g. `https://localhost/`).
4. Run the helper locally — it prints the three secrets to store:
   ```bash
   pip install requests
   python scripts/get_pinterest_refresh_token.py
   ```
   It asks for your App ID, App secret, and redirect URI, gives you a URL to
   approve in your browser, then prints `PINTEREST_APP_ID`,
   `PINTEREST_APP_SECRET`, and `PINTEREST_REFRESH_TOKEN`.
5. Add those three as GitHub secrets. After this you never touch Pinterest
   auth again — each run mints a fresh access token automatically.

**Simpler alternative (token expires monthly):** skip the refresh flow and
just generate a single access token in the Pinterest app UI, then store it as
`PINTEREST_ACCESS_TOKEN`. When it expires, posting fails and you generate a
new one. The automation accepts either setup.

### 4. Add the secrets to GitHub
In this repository: **Settings → Secrets and variables → Actions → New
repository secret**. Always add:

- `ANTHROPIC_API_KEY`
- `GOOGLE_SERVICE_ACCOUNT_JSON` (paste the entire JSON file contents)
- `GDRIVE_FOLDER_ID`

Plus a posting backend. **Recommended** — Postiz (no Pinterest review needed):

- `POSTIZ_API_KEY`

**or** the direct Pinterest API (requires Standard access) — either the
auto-refresh trio:

- `PINTEREST_APP_ID`
- `PINTEREST_APP_SECRET`
- `PINTEREST_REFRESH_TOKEN`

or the single static token:

- `PINTEREST_ACCESS_TOKEN`

### 5. Configure your brand
Edit `config.yaml` — set `website_url`, `business_name`, `niche`,
`target_audience`, and `board_name`. The board is created automatically on
the first run if it doesn't exist.

## Running it

- **Automatically:** the workflow runs every 6 hours (edit the `cron` in
  `.github/workflows/pinterest-automation.yml` to change the cadence).
- **On demand:** go to the **Actions** tab → *Pinterest Automation* → **Run
  workflow**. Use this to test your setup.
- **Locally:** export the four variables and run:
  ```bash
  pip install -r requirements.txt
  export ANTHROPIC_API_KEY=... PINTEREST_ACCESS_TOKEN=... GDRIVE_FOLDER_ID=...
  export GOOGLE_SERVICE_ACCOUNT_JSON="$(cat service-account.json)"
  python -m pinterest_automation.main
  ```

## Tuning

- **How many pins per run:** `max_pins_per_run` in `config.yaml` (default 4).
  This keeps you under Pinterest rate limits and spaces posts out instead of
  dumping a whole folder at once.
- **Cost vs. quality of the copy:** `model` in `config.yaml`. Default is
  `claude-opus-4-8` (highest quality); set `claude-sonnet-4-6` for cheaper
  high-volume captioning.
- **Where pins link:** `website_url` + the `utm` block in `config.yaml`.

## Notes

- Photos are matched by their Drive file id, so renaming a file in Drive
  won't cause a re-post, but re-uploading (which creates a new id) will.
- The Drive folder is opened **read-only** — the automation never changes or
  deletes your photos.

---

# SEO Blog Automation

The workflow is review-only. It does not generate paid content, change the CMS,
commit to main, or publish the website. The previous automatic publisher was
removed because it could overwrite newer Framer edits with old bundles.

Run with Node 22 or newer:

```bash
node framer/publish.mjs --baseline framer/cms-baseline.json
cd framer
npm test
```

The historical `npm run publish-posts` command is retained as a safe alias for
review generation. It cannot publish. No Framer credentials or npm dependencies
are needed. `--publish`, `--apply`, `--force` and unknown arguments are rejected.

The JSON review plan includes exact bundle and image hashes, explicit field IDs,
per-item blockers and `productionApproval: not-granted`. Existing items require
a matching content hash from a fresh main-branch CMS snapshot and an explicit
field allowlist. The snapshot expires after 24 hours. Missing alt text, invalid
or future dates, truncated metadata, duplicate slugs, unsafe asset paths and
unresolved image placeholders are blockers, not silently discarded content.
All six old bundles are currently blocked to protect later Framer edits.

The Python generation modules remain available for separately authorised local
draft generation. They are not called by this workflow. The separate Mac-based
`andre-seo-publishing` scheduler was not accessible in this environment and must
be reconciled before unattended publishing is enabled anywhere.

See [Framer release procedure](framer/RELEASE.md). Only an explicitly approved,
verified Framer branch may be released manually; this repository has no release
command. Scheduled publication remains disabled.

---

# Ops Dashboard

A single, self-contained `dashboard.html` at the repo root that shows both
pipelines at a glance: pins posted (and the daily cadence), which shoots they
came from, blog posts published, keywords done, and how many topics are still
in the queue — plus whether each pipeline is **live** or **paused**. It's built
by `scripts/build_dashboard.py`, which only ever **reads committed state**
(`state/posted.json`, `state/blog.json`, `config.yaml` and the workflow files),
so it needs no API keys and makes no network calls.

The page is a plain HTML file — open it locally, or (since the repo is public
for image hosting) view the latest committed copy at
`https://raw.githack.com/<owner>/<repo>/<branch>/dashboard.html`.

**It stays current automatically:**

- The **Pinterest** and **SEO Blog** workflows rebuild it inline in their commit
  step, so it refreshes the moment new pins or posts land.
- A dedicated **Ops Dashboard** workflow (`.github/workflows/dashboard.yml`)
  rebuilds it on a manual trigger (Actions tab → *Ops Dashboard* → **Run
  workflow**) and on a light weekly schedule, so it self-heals even while the
  two automations are paused.

**Rebuild it locally** (no secrets needed):

```bash
pip install PyYAML
python scripts/build_dashboard.py          # writes dashboard.html
```

The generator splits data collection (`collect()`) from rendering
(`render_body()`), so the numbers are unit-tested in
`tests/test_build_dashboard.py` without touching the HTML.

---

# Etsy Listing Automation

An on-demand Claude Code skill (`.claude/skills/etsy-automation/`) for
creating Etsy listings for digital-download products (presets, templates,
printables, guides). Unlike the two cron pipelines above, you invoke this
yourself in a Claude Code session whenever you have a new product to list —
nothing runs on a schedule.

**How it works:** you tell Claude what the product is and where the photos
and digital files live on disk. It writes SEO-ready listing copy (title,
description, tags, materials) and then either:

- **Creates the listing as a draft via the Etsy API** (if you have an
  approved Etsy app set up — see setup below), uploading the images and
  files and reporting the resulting `listing_id`; or
- **Prints a ready-to-paste draft** for you to enter manually in Etsy's
  listing editor, if API access isn't set up yet.

Either way, the listing is **never published live automatically** — moving
a draft to active is always a separate, explicit step you ask for after
reviewing it.

```
"List this on Etsy" ─▶ Claude writes SEO copy ─▶ Etsy draft listing (API or copy-paste) ─▶ you review ─▶ you say "publish it"
```

## Project layout

| File | Purpose |
|------|---------|
| `.claude/skills/etsy-automation/SKILL.md` | The skill definition Claude follows. |
| `.claude/skills/etsy-automation/scripts/etsy_client.py` | Etsy Open API v3 client (listings, images, files, taxonomy). |
| `.claude/skills/etsy-automation/scripts/etsy_auth.py` | Refreshes an Etsy access token from a refresh token. |
| `.claude/skills/etsy-automation/scripts/create_listing.py` | CLI the skill runs: `create`, `activate`, `taxonomy`. |
| `.claude/skills/etsy-automation/scripts/get_etsy_refresh_token.py` | One-time OAuth setup helper (run locally). |
| `.claude/skills/etsy-automation/references/auth-setup.md` | Etsy app approval tips + first-time OAuth setup walkthrough. |
| `.claude/skills/etsy-automation/references/digital-listing-fields.md` | Field cheat sheet (title/tag/taxonomy rules). |
| `config.yaml` (`etsy:` block) | Non-secret copywriting defaults (currency, who_made, when_made, type, quantity). |
| `state/etsy_listings.json` | Tracks created listings (created on first live-mode use). |

## Setup

**Nothing is required to use draft/copy-paste mode** — just invoke the
skill. To enable live API mode (the skill creates real draft listings
directly via the Etsy API):

1. Register an app at <https://www.etsy.com/developers/your-apps> and wait
   for it to show **Approved** — Etsy manually reviews every app, including
   the API key itself, so nothing works until then. If you've been denied,
   see `.claude/skills/etsy-automation/references/auth-setup.md` for common
   denial causes and how to escalate (developers@etsy.com is the only
   official channel).
2. Run the one-time OAuth helper locally:
   ```bash
   pip install requests
   python .claude/skills/etsy-automation/scripts/get_etsy_refresh_token.py
   ```
   It prints `ETSY_API_KEY`, `ETSY_SHARED_SECRET`, and `ETSY_REFRESH_TOKEN`.
3. Find your shop id manually (Shop Manager → Settings → Options — it's in
   that page's URL) and store it as `ETSY_SHOP_ID`.
4. Store all four as secrets (GitHub Actions secrets, or export them locally
   for ad-hoc sessions): `ETSY_API_KEY`, `ETSY_SHARED_SECRET`,
   `ETSY_SHOP_ID`, `ETSY_REFRESH_TOKEN`.

## Running it

In a Claude Code session in this repo:

```
List this digital download on Etsy: a set of 10 Lightroom presets, photos
and zip file are in ~/Desktop/preset-pack/, $12 AUD.
```

The skill asks for anything it still needs, writes the copy, and reports
either a draft `listing_id` (live mode) or copy-paste-ready text (draft
mode). To publish a draft it already created, ask explicitly — e.g. "publish
listing 12345".

## Notes

- Listing photos and digital product files are **never** committed to this
  (public) repo — the skill reads them straight from the local paths you
  give it.
- Etsy rotates the refresh token every time it's used; if
  `create_listing.py` prints a new one, update the `ETSY_REFRESH_TOKEN`
  secret with it or the next run will fail.

---

# Topic scout agent

`topic-scout` (`.claude/agents/topic-scout.md`) is an on-demand sub-agent for
planning the blog content queue ahead of time, instead of waiting for
`blog_automation/research.py`'s quick five-search top-up to kick in once the
queue nearly runs dry. It reads your current `blog.topics` and
`state/blog.json`, does deeper SERP and competitor research with WebSearch,
and appends the strongest new keywords to `config.yaml` in the same format
the automated pipeline uses.

## Usage

In a Claude Code session in this repo:

```
Use the topic-scout agent to find 5 new blog topics.
```

It reports what it added (and why), what it rejected (and why), and any
Pinterest-keyword angles that don't fit the blog queue.

---

# Claude SEO skill

[Claude SEO](https://github.com/AgriciDaniel/claude-seo) (MIT licensed) is
installed at the project level — 25 sub-skills under `.claude/skills/` and 18
specialist sub-agents under `.claude/agents/`. It's independent of the two
automations above: it's an interactive toolkit you invoke yourself in a
Claude Code session to audit a live site on demand.

## Usage

In a Claude Code session in this repo:

```
/seo audit https://yoursite.com
/seo technical https://yoursite.com
/seo schema https://yoursite.com
/seo content https://yoursite.com
/seo geo https://yoursite.com
```

Run `/seo` with no arguments for the full command list (audit, page,
technical, content, schema, geo, local, ecommerce, backlinks, sitemap,
images, and more).

## One-time setup

The skill's Python dependencies are kept separate from this project's own
`requirements.txt` since they're only needed when you actually run a `/seo`
command:

```bash
pip install -r .claude/skills/seo/requirements.txt
playwright install chromium   # optional, enables visual/SPA rendering
```

Optional MCP extensions (DataForSEO, Firecrawl, Google Search Console/PageSpeed,
Ahrefs, Bing Webmaster, etc.) are not installed — see the
[upstream docs](https://github.com/AgriciDaniel/claude-seo/blob/main/docs/MCP-INTEGRATION.md)
if you want to add any of those.

---

# Ship-feature pipeline

A four-agent dev pipeline under `.claude/agents/` (`pipeline-planner`,
`pipeline-coder`, `pipeline-tester`, `pipeline-reviewer`) chained together by
the `/ship-feature` command. Each stage hands context to the next through
plain files in a local `.pipeline/` scratch folder (gitignored) instead of
through the orchestrator's own context window:

| Stage | Agent | Model | Reads | Writes |
|---|---|---|---|---|
| Plan | `pipeline-planner` | Opus | `.pipeline/request.md` | `.pipeline/specs.md` |
| Code | `pipeline-coder` | Sonnet | `.pipeline/specs.md` | code + `.pipeline/changes.md` |
| Test | `pipeline-tester` | Sonnet | `specs.md` + `changes.md` | tests + `.pipeline/tests.md` |
| Review | `pipeline-reviewer` (read-only) | Sonnet | all of the above + `git diff` | `.pipeline/review.md` |

## Usage

In a Claude Code session in this repo:

```
/ship-feature add rate limiting to the login endpoint
```

The reviewer's verdict (`APPROVE` / `REQUEST_CHANGES` / `BLOCK`) is reported
back at the end, but nothing is committed, pushed, or merged automatically —
the pipeline only prepares a reviewed diff on the current branch for a human
to act on.
