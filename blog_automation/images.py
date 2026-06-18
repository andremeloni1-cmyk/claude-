"""Resize/compress photos for Claude vision and for web display in the post.

Full-resolution photos exceed the Claude vision API's per-image limit and are
larger than a web page needs. This downsizes and re-encodes to JPEG, dropping
quality only as far as needed to fit a byte cap.
"""

from __future__ import annotations

import io

from PIL import Image, ImageOps

JPEG = "image/jpeg"


def _resize_to_fit(image_bytes: bytes, max_dim: int, max_bytes: int, quality: int) -> bytes:
    img = Image.open(io.BytesIO(image_bytes))
    img = ImageOps.exif_transpose(img)  # honour camera orientation
    if img.mode != "RGB":
        img = img.convert("RGB")

    width, height = img.size
    longest = max(width, height)
    if longest > max_dim:
        scale = max_dim / longest
        img = img.resize((round(width * scale), round(height * scale)), Image.LANCZOS)

    q = quality
    while True:
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=q, optimize=True)
        data = buffer.getvalue()
        if len(data) <= max_bytes or q <= 40:
            return data
        q -= 10


def for_analysis(image_bytes: bytes) -> bytes:
    """A small JPEG for Claude vision: enough detail to choose photos, well under 10 MB."""
    return _resize_to_fit(image_bytes, max_dim=1024, max_bytes=3 * 1024 * 1024, quality=80)


def for_web(image_bytes: bytes) -> bytes:
    """A high-quality JPEG sized for display in a blog post."""
    return _resize_to_fit(image_bytes, max_dim=2048, max_bytes=2 * 1024 * 1024, quality=85)
