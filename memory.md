# memory.md — durable project context

Long-lived notes and decisions for this repo. CLAUDE.md says *how to work
here*; this file records *what we know and what we've decided* so context
survives between sessions. Keep it short and current.

## Key facts

- **Two Python pipelines** share `config.yaml` and the `state/` directory:
  - `blog_automation/` → writes `published/<slug>/` bundles → `framer/publish.mjs`
    pushes them to the Framer CMS. Entry point: `python -m blog_automation.main`.
  - `pinterest_automation/` → posts pins via Postiz (or direct Pinterest API).
    Entry point: `python -m pinterest_automation.main`.
- **Idempotency is a hard requirement.** `state/blog.json` and
  `state/posted.json` (committed) ensure a topic is never written twice and a
  photo is never reused/reposted. A regression here double-publishes to *live*
  accounts — protect it with tests.
- **Posting backend:** Postiz is preferred (it already holds approved Pinterest
  write access). The direct Pinterest API path requires Pinterest "Standard
  access" review and is the fallback.
- **Secrets** are env vars only (`ANTHROPIC_API_KEY`, `GOOGLE_SERVICE_ACCOUNT_JSON`,
  `GDRIVE_FOLDER_ID`, `POSTIZ_API_KEY`/`PINTEREST_*`). `config.yaml` is non-secret.
- **Model:** `claude-opus-4-8` (set in `config.yaml`).

## Testing status (as of 2026-06-24)

- CI: `.github/workflows/tests.yml` runs `pytest tests/ -v` on push/PR.
- Coverage was expanded from 2 test files to a fuller suite. Now covered:
  - `blog_automation/`: `research`, `config` (load + append_topics), `writer`
    (`_clamp`/`_slugify`/`select_images`/`write_post`), `state`, `bundle`,
    `images`, and `main`'s auto-research path.
  - `pinterest_automation/`: pure helpers (`_link_with_utm`, `_jpeg_name`,
    `_parse_service_account`, `_extract_post_id`), `PostizClient` (mocked HTTP),
    `config` credential resolution, `captions.generate`, `state`, `images`.
- **Still untested / future work:**
  - `blog_automation/main.py` `_pick_candidates` / `_build_post` end-to-end.
  - `pinterest_automation/main.py` `_resolve_board_id` / `_build_poster` / `run`.
  - `PinterestClient` (`pinterest.py`) and `pinterest_auth.refresh_access_token`.
  - `framer/publish.mjs` (Node side) has no tests.
  - The `.claude/skills/` scripts are intentionally out of scope.

## Decisions / conventions

- External services are always **stubbed** in tests (Anthropic client, HTTP
  session). No test makes a real network call or needs real credentials.
- SEO field length limits are enforced **in code** (clamping), not by the API's
  JSON schema — keep the clamps and test their boundaries.
- `config.append_topics()` edits `config.yaml` textually to preserve formatting
  and comments; don't swap it for a YAML round-trip dump.

## Open questions

- Should the `framer/` Node publisher get its own test harness (mirroring what
  `joinery-` now has with `node --test`)?
- Is end-to-end coverage of `main.run()` (both pipelines) worth the mocking
  cost, or is the current per-unit coverage sufficient?
