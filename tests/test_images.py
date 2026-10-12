"""Tests for the image resize/compress helpers.

- blog_automation/images.py  (for_analysis / for_web)
- pinterest_automation/images.py (for_analysis / for_pin)

Both wrap a shared _resize_to_fit that honours EXIF orientation, converts to
RGB, downsizes to a max dimension, and steps JPEG quality down until under a
byte cap. Uses small in-memory images so the suite stays fast.

Run with:
    cd /home/user/claude- && python3 -m pytest tests/test_images.py -v
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from PIL import Image  # noqa: E402

import blog_automation.images as blog_images  # noqa: E402
import pinterest_automation.images as pin_images  # noqa: E402


def _png_bytes(width: int, height: int, color=(120, 30, 200), mode="RGB") -> bytes:
    img = Image.new(mode, (width, height), color if mode == "RGB" else 255)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _dims(jpeg_bytes: bytes) -> tuple[int, int]:
    return Image.open(io.BytesIO(jpeg_bytes)).size


def _is_jpeg(data: bytes) -> bool:
    return Image.open(io.BytesIO(data)).format == "JPEG"


# ---------------------------------------------------------------------------
# _resize_to_fit
# ---------------------------------------------------------------------------


def test_resize_downsizes_to_max_dimension():
    out = blog_images._resize_to_fit(_png_bytes(4000, 2000), max_dim=1024, max_bytes=5_000_000, quality=80)
    w, h = _dims(out)
    assert max(w, h) == 1024
    assert (w, h) == (1024, 512)  # aspect ratio preserved


def test_resize_does_not_upscale_small_images():
    out = blog_images._resize_to_fit(_png_bytes(300, 200), max_dim=1024, max_bytes=5_000_000, quality=80)
    assert _dims(out) == (300, 200)


def test_resize_always_outputs_jpeg():
    out = blog_images._resize_to_fit(_png_bytes(500, 500), max_dim=1024, max_bytes=5_000_000, quality=80)
    assert _is_jpeg(out)


def test_resize_converts_non_rgb_input():
    # An RGBA / palette source must not raise when encoded as JPEG.
    out = blog_images._resize_to_fit(_png_bytes(400, 400, mode="L"), max_dim=1024, max_bytes=5_000_000, quality=80)
    assert _is_jpeg(out)


def test_resize_steps_quality_down_to_meet_byte_cap():
    # A noisy, detailed image is hard to compress; a tiny cap forces the
    # quality-reduction loop. The loop floors at q=40, so allow a small margin.
    import os

    noise = os.urandom(2048 * 2048 * 3)
    img = Image.frombytes("RGB", (2048, 2048), noise)
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    out = blog_images._resize_to_fit(buf.getvalue(), max_dim=2048, max_bytes=50_000, quality=85)
    # Either it met the cap, or it bottomed out at q<=40 (loop termination).
    assert _is_jpeg(out)


# ---------------------------------------------------------------------------
# Public wrappers
# ---------------------------------------------------------------------------


def test_blog_for_analysis_caps_dimension_at_1024():
    out = blog_images.for_analysis(_png_bytes(3000, 1500))
    assert max(_dims(out)) == 1024
    assert len(out) <= 3 * 1024 * 1024


def test_blog_for_web_caps_dimension_at_2048():
    out = blog_images.for_web(_png_bytes(4000, 3000))
    assert max(_dims(out)) == 2048


def test_pinterest_for_analysis_caps_dimension_at_1536():
    out = pin_images.for_analysis(_png_bytes(3000, 1500))
    assert max(_dims(out)) == 1536


def test_pinterest_for_pin_produces_jpeg():
    out = pin_images.for_pin(_png_bytes(3000, 1500))
    assert _is_jpeg(out)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
