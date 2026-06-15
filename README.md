# Photography Marketing Automations

This repo contains two hands-off marketing pipelines for a photography
business, both driven by Claude and run on a schedule by GitHub Actions:

1. **Pinterest Automation** — turns Drive photos into SEO-optimised pins (below).
2. **[SEO Blog Automation](#seo-blog-automation)** — writes full SEO blog posts,
   illustrates them with your photos, and publishes them straight to your
   **Framer** CMS.

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
