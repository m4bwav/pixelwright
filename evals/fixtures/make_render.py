"""Fixture for the make cases: python evals/fixtures/make_render.py <folder>.

Writes render.png (a 16x16 potion drawn at 5x on a 3 px offset over a flat sky, blurred and noised like an image
model's "pixel art"), ref.png (another sprite in the same five colours, the set's palette) and keeps the truth in
code only, so check_make_outcome.py can rebuild it.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

INK, RED, PINK, GLASS, CORK, SKY = [24, 20, 37], [190, 38, 51], [224, 111, 139], [178, 220, 239], [164, 100, 34], \
    [120, 170, 230]


def potion():
    a = np.zeros((16, 16, 4), np.uint8)
    yy, xx = np.mgrid[0:16, 0:16]
    a[(yy - 10) ** 2 + (xx - 7.5) ** 2 <= 30] = INK + [255]
    a[(yy - 10) ** 2 + (xx - 7.5) ** 2 <= 18] = RED + [255]
    a[8:10, 4:6] = PINK + [255]
    a[2:6, 5:11] = INK + [255]
    a[3:6, 6:10] = GLASS + [255]
    a[1:3, 6:10] = CORK + [255]
    a[0, 6:10] = INK + [255]
    return a


def ref():
    a = np.zeros((12, 12, 4), np.uint8)
    a[1:11, 1:11] = INK + [255]
    a[2:10, 2:10] = CORK + [255]
    a[4:6, 2:10] = RED + [255]
    a[6, 5:7] = PINK + [255]
    a[3, 3:9] = GLASS + [255]
    return a


def render(a, s=5, off=3, pad=2, seed=7):
    big = np.repeat(np.repeat(a, s, 0), s, 1)
    h, w = big.shape[:2]
    c = np.zeros((h + off + pad, w + off + pad, 4), np.uint8)
    c[...] = SKY + [255]
    m = big[..., 3] > 0
    c[off:off + h, off:off + w][m] = big[m]
    b = np.array(Image.fromarray(c, "RGBA").filter(ImageFilter.GaussianBlur(1.0))).astype(np.int16)
    b[..., :3] += np.random.default_rng(seed).integers(-6, 7, b[..., :3].shape).astype(np.int16)
    return np.clip(b, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    d = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    Image.fromarray(render(potion()), "RGBA").save(d / "render.png")
    Image.fromarray(ref(), "RGBA").save(d / "ref.png")
    print("wrote render.png and ref.png")
