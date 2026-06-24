# CLAUDE.md — working in this repo

Guidance for Claude Code (and humans) working in this repository. For the
full product write-up see `README.md`; this file is the short, practical
orientation plus the testing conventions.

## What this repo is

Two hands-off marketing pipelines for a photography business, both driven by
Claude and run on a schedule by GitHub Actions:

1. **SEO Blog Automation** (`blog_automation/`, Python) — researches topics,
   writes a full SEO blog post with Claude, picks and resizes photos from
   Google Drive, and writes each post + images into a `published/<slug>/`
   bundle. A small Node publisher (`framer/publish.mjs`) pushes those bundles
   into the Framer CMS.
2. **Pinterest Automation** (`pinterest_automation/`, Python) — finds new
   Drive photos, writes SEO pin copy with Claude vision, and posts pins via
   Postiz (preferred) or the direct Pinterest API.

There are also on-demand **skills** under `.claude/skills/` (Etsy listing
automation and the Claude SEO toolkit) — these are largely self-contained
vendored tools and are *not* part of the pytest suite.

## Layout

```
blog_automation/        Blog pipeline (config, research, writer, images, bundle, state, main)
pinterest_automation/   Pinterest pipeline (config, captions, drive, images, pinterest, postiz, state, main)
framer/                 Node publisher (publish.mjs) that uploads bundles to Framer
scripts/                One-off helpers (e.g. Pinterest refresh-token bootstrap)
published/              Generated post bundles (committed)
state/                  Committed JSON progress files (blog.json, posted.json)
config.yaml             Brand settings + topic queue (non-secret)
tests/                  pytest suite
.github/workflows/      tests.yml (CI), blog-automation.yml, pinterest-automation.yml (schedules)
```

## Configuration model

- **`config.yaml`** holds non-secret brand/behaviour settings (business name,
  service area, model, topic queue, limits). Both pipelines read it.
- **Secrets come from environment variables** (GitHub Actions secrets locally
  exported): `ANTHROPIC_API_KEY`, `GOOGLE_SERVICE_ACCOUNT_JSON`,
  `GDRIVE_FOLDER_ID`, and posting credentials (`POSTIZ_API_KEY` or
  `PINTEREST_*`). Never hard-code or commit secrets.
- **State files are committed** (`state/`). They guarantee idempotency: a topic
  is never written twice and a photo is never reused/reposted. Treat changes to
  the state schema with care.

## Running the tests

CI (`.github/workflows/tests.yml`) runs:

```bash
pip install -r requirements.txt
pip install pytest
pytest tests/ -v
```

Do the same locally. The suite needs `anthropic`, `google-api-python-client`,
`google-auth`, `Pillow`, and `PyYAML` (all in `requirements.txt`). No network
access or real credentials are required — every external dependency is stubbed.

## Test conventions (follow these when adding tests)

- Tests live in `tests/test_*.py` and start with:
  ```python
  REPO_ROOT = Path(__file__).resolve().parent.parent
  sys.path.insert(0, str(REPO_ROOT))
  ```
- **Stub the Anthropic client** rather than calling it. The established pattern
  is a `_FakeResponse` exposing `.content` (a list of blocks with `.type` /
  `.text`) and `.stop_reason`, installed with
  `monkeypatch.setattr(mod.anthropic, "Anthropic", lambda api_key=None: client)`.
  See `tests/test_writer.py` and `tests/test_research.py`.
- **Stub HTTP** by replacing the client's `_session` with a fake that returns
  canned responses (see `tests/test_postiz_client.py`).
- Use `tmp_path` for anything that touches the filesystem; use `monkeypatch.setenv`
  for config/secret resolution (see `tests/test_pinterest_config.py`).
- Keep image tests fast with small in-memory PIL images (`tests/test_images.py`).

## Conventions & gotchas

- Match the surrounding code style; modules are small, single-purpose, and
  prefer pure functions where possible (good for testing).
- `config.append_topics()` writes `config.yaml` by hand to preserve exact
  formatting and comments — don't replace it with a naive YAML dump.
- Model copy is post-processed in code (clamping to SEO field limits,
  slugifying); the JSON-schema length limits are *not* enforced by the API, so
  the clamping in `writer.py` / `captions.py` is load-bearing.
- The two GitHub Actions schedules call `python -m blog_automation.main` and
  `python -m pinterest_automation.main`.

## Branch / PR workflow for this task

Active development branch: `claude/test-coverage-analysis-xz339z`. Commit there
and open a draft PR; do not push to `main` without explicit permission.
