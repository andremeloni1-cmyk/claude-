# Photography Marketing Automations

This repo contains two hands-off marketing pipelines for a photography
business, both driven by Claude and run on a schedule by GitHub Actions:

1. **Pinterest Automation** — turns Drive photos into SEO-optimised pins (below).
2. **[SEO Blog Automation](#seo-blog-automation)** — writes full SEO blog posts,
   illustrates them with your photos, and publishes them straight to your
   **Framer** CMS.

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

Fully automated, SEO-optimised blog posts for your photography website,
written by Claude, illustrated with your own photos, and published straight
into your **Framer** CMS — no copy-paste, and you never have to open Framer.

**How it works:** you list the keywords you want to rank for in `config.yaml`.
On a schedule, GitHub Actions runs the pipeline, which:

1. Takes the next keyword you haven't covered yet.
2. Pulls candidate photos from your Google Drive folder and asks **Claude**
   (vision) to pick the ones that best fit the topic and write alt text.
3. Asks **Claude** to write a complete, genuinely useful SEO article — title,
   slug, meta title + description, excerpt, category, keywords, and a
   markdown body with headings, internal links, a FAQ and a call to action —
   with your photos placed inline.
4. Commits the post + resized images to the repo (so the images have public
   URLs), then pushes the post into your **Framer CMS** via the **Framer
   Server API** and publishes the site.
5. Records what it wrote in `state/blog.json` so nothing is ever duplicated.

```
config.yaml keywords ─▶ GitHub Actions (cron) ─▶ Claude picks photos + writes post ─▶ Framer CMS ─▶ published site
```

## How the two halves fit together

| Part | What it does |
|------|--------------|
| `blog_automation/` (Python) | Picks the topic, chooses + resizes photos, writes the post, and saves a self-contained bundle under `published/<slug>/`. |
| `framer/publish.mjs` (Node) | Reads each bundle and pushes it into the Framer CMS via the Framer Server API, then publishes the site. |
| `published/<slug>/` | A committed bundle: `post.json` (the CMS fields) + the resized JPEGs. Committing them gives the images public URLs Framer can ingest. |
| `state/blog.json` | Tracks which keywords are done and which photos have been used. |
| `.github/workflows/blog-automation.yml` | The scheduled run (weekly by default). |

> **Why two languages?** Framer has no public REST CMS write API; the official,
> first-party way to write to the CMS from a server is the `framer-api` npm
> package (the **Server API**, free in open beta). So the post is generated in
> Python and pushed to Framer in a small Node step.

## Setup

You reuse the **Anthropic** and **Google Drive** secrets from the Pinterest
setup above, plus two new Framer secrets.

### 1. Reuse existing secrets
- `ANTHROPIC_API_KEY` and `GOOGLE_SERVICE_ACCOUNT_JSON` — already set up for
  Pinterest, nothing to do.
- Photos: by default the blog reuses `GDRIVE_FOLDER_ID`. To draw blog images
  from a **different** Drive folder, set `BLOG_GDRIVE_FOLDER_ID` instead
  (share that folder with the same service-account email).

### 2. Framer Server API key + project URL
1. Open your site in Framer → **Site Settings → General** → generate an
   **API key**. Add it as the secret `FRAMER_API_KEY`.
2. Your project URL is `https://framer.com/projects/Sites--xxxxxxxx` (copy it
   from the address bar in the Framer editor). Add it as `FRAMER_PROJECT_URL`.
3. *(Optional)* To target an exact collection, set `FRAMER_COLLECTION_ID`.
   Otherwise the pipeline matches the collection by name (`blog.collection_name`
   in `config.yaml`, default `Blog`).

### 3. Your Framer blog collection
You need a CMS collection in Framer for blog posts (most blog templates ship
with one). Map your collection's **field names** to the pipeline's logical
fields in `config.yaml` under `blog.field_map`. Names are matched
case-insensitively, and any logical field your collection doesn't have is simply
skipped — so a partial map is fine. The post **slug** is set automatically and
never needs mapping.

The logical fields the pipeline can produce are: `title`, `intro_1`, `intro_2`
(two short lede paragraphs shown above the article), `body` (the full article —
map this to a *formatted text / rich text* field), `cover` (map to an *image*
field), `cover_alt` (alt text for the cover, a *string* field), `image_1` (a
secondary feature image, also shown above the article) and `date`. The default
map matches this project's "Blog" collection:

```yaml
field_map:
  title: "Title"
  intro_1: "Intro 1"
  intro_2: "Intro 2"
  body: "Content"
  cover: "Preview"
  cover_alt: "Alt text"
  image_1: "Image 1"
  date: "Date"
```

If a mapped name isn't found, the publisher falls back to the only field of an
unambiguous type (image → cover, formatted-text → body, date → date) so cover
photos still land even if a name is slightly off. The run log prints every
collection field name so you can correct the map.

### 4. Make the repo public (for image hosting)
Images are served to Framer from `raw.githubusercontent.com`, which requires a
**public** repository. If you'd rather keep the repo private, host the images
elsewhere (an S3/R2 bucket or CDN) and set the workflow's `IMAGE_BASE_URL` to
that base instead — everything else stays the same.

### 5. Add your keywords
Edit `config.yaml` → `blog.topics`: one entry per keyword you want to target,
with optional `notes` to steer the angle. The pipeline works through them in
order, one (by `blog.max_posts_per_run`) per run.

## Running it

- **Automatically:** the workflow runs weekly (Monday 09:00 UTC). Change the
  `cron` in `.github/workflows/blog-automation.yml` and `max_posts_per_run` in
  `config.yaml` to change the pace.
- **On demand:** Actions tab → *SEO Blog Automation* → **Run workflow**.
- **Locally (generate only):**
  ```bash
  pip install -r requirements.txt
  export ANTHROPIC_API_KEY=... GDRIVE_FOLDER_ID=...
  export GOOGLE_SERVICE_ACCOUNT_JSON="$(cat service-account.json)"
  python -m blog_automation.main          # writes published/<slug>/
  # then push to Framer:
  cd framer && npm install
  export FRAMER_API_KEY=... FRAMER_PROJECT_URL=...
  export IMAGE_BASE_URL="https://raw.githubusercontent.com/<owner>/<repo>/<branch>"
  node publish.mjs
  ```

## Tuning

- **Topics & angles:** `blog.topics` in `config.yaml`.
- **Posts per run / cadence:** `blog.max_posts_per_run` + the workflow `cron`.
- **Photos per post:** `blog.images_per_post` (first is the cover, second is the
  secondary feature image, the rest are placed inline in the article).
- **Image matching cost:** `blog.image_candidate_pool` (how many photos Claude
  reviews per post).
- **Cost vs. quality:** `model` in `config.yaml` (`claude-opus-4-8` for best
  writing, `claude-sonnet-4-6` for cheaper high-volume).
- **Field mapping & internal links:** `blog.field_map` and `blog.internal_links`.

## Notes

- Re-runs are safe: a keyword already in `state/blog.json` is never rewritten.
  In Framer, a new slug is created and an existing slug is **updated in place**
  (never duplicated), so a failed push is retried — and a field-map fix is
  back-filled onto already-published posts — on the next run.
- The Drive folder is opened **read-only**. Photos are matched by Drive file id
  and (by default) not reused across posts until the unused pool runs out.

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

Optional MCP extensions (Google Search Console/PageSpeed, Ahrefs, Bing
Webmaster, etc. — DataForSEO and Firecrawl are wired up below) are not
installed — see the
[upstream docs](https://github.com/AgriciDaniel/claude-seo/blob/main/docs/MCP-INTEGRATION.md)
if you want to add any of those.

## DataForSEO extension (live SERP, keywords, backlinks, AI visibility)

The `seo-dataforseo` skill/agent are installed, and the MCP server is
configured in `.mcp.json` — but it needs your own
[DataForSEO](https://app.dataforseo.com/register) credentials (paid,
pay-as-you-go; new accounts get a free trial balance). The config reads them
from environment variables rather than storing them in the repo:

```bash
DATAFORSEO_USERNAME=your-email@example.com
DATAFORSEO_PASSWORD=your-api-password
```

Set these as secrets/environment variables in whatever environment runs
Claude Code (e.g. this repo's Claude Code on the web environment settings,
or your local shell before running `claude`) — never commit them. The first
time Claude Code starts with these set, it'll prompt you to approve the new
`dataforseo` MCP server from `.mcp.json`.

Once connected:

```
/seo dataforseo serp best wedding photographers near me
/seo dataforseo keywords wedding photography
/seo dataforseo backlinks yoursite.com
/seo dataforseo ai-mentions your brand name
```

`/seo audit`, `/seo technical`, `/seo content`, and `/seo geo` also
automatically use live DataForSEO data instead of estimates once it's
connected. Full command list and per-call credit costs:
[extension README](https://github.com/AgriciDaniel/claude-seo/blob/main/extensions/dataforseo/README.md).

## Firecrawl extension (full-site crawling with JS rendering)

The `seo-firecrawl` skill is installed and the MCP server is configured in
`.mcp.json`. It needs a [Firecrawl](https://www.firecrawl.dev/app/sign-up)
API key (free tier: 500 credits/month):

```bash
FIRECRAWL_API_KEY=fc-your-api-key
```

Set this the same way as the DataForSEO credentials above — as an
environment variable/secret in whatever runs Claude Code, never committed.
Once connected:

```
/seo firecrawl map https://yoursite.com
/seo firecrawl crawl https://yoursite.com
/seo firecrawl scrape https://yoursite.com/some-page
/seo firecrawl search "wedding photographer" https://yoursite.com
```

`/seo audit`, `/seo technical`, and `/seo sitemap` use Firecrawl's `map`/
`crawl` to discover and analyze pages beyond what the XML sitemap lists.
Details: [extension README](https://github.com/AgriciDaniel/claude-seo/blob/main/extensions/firecrawl/README.md).

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
