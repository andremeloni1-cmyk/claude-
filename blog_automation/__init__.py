"""Automated SEO blog pipeline: write posts, illustrate from Drive, publish to Framer.

The Python side (this package) writes each post and its images into a
``published/<slug>/`` bundle and records progress in ``state/blog.json``. The
Node side (``framer/publish.mjs``) pushes those bundles into the Framer CMS via
the Framer Server API and publishes the site.
"""

__all__ = [
    "config",
    "images",
    "writer",
    "bundle",
    "state",
    "main",
]
