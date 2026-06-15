"""Upload wedding photos from a Drive folder into the Framer Portfolio CMS.

This is the photography "profile / portfolio" pipeline. You drop wedding photos
into a Google Drive folder; on a schedule this package downloads each new photo,
asks Claude (vision) for a short title and honest alt text, resizes it for the
web, and writes a self-contained bundle under ``published_profile/<slug>/``. The
Node side (``framer/publish-profile.mjs``) pushes those bundles into the Framer
``Portfolio`` collection (filed under the configured category) and publishes the
site.

Re-runs are safe: each Drive photo is tracked by its file id in
``state/profile.json`` and never uploaded twice, and an existing slug in Framer
is updated in place rather than duplicated.
"""

__all__ = [
    "config",
    "captioner",
    "bundle",
    "state",
    "main",
]
