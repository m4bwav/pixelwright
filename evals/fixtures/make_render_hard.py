"""Fixture for outcome-make-2: python evals/fixtures/make_render_hard.py <folder>.

Writes render.png (make_render's 16x16 potion drawn at 5.5x, so blocks alternate 5 and 6 px, on a 3 px offset over a
flat sky, blurred and noised) and refs/ (three sprites from the same set; the palette is their union, and no one of
them holds all five colours). The truth stays in code, so check_make_hard.py can rebuild it.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_render import CORK, GLASS, INK, PINK, RED, SKY, potion  # noqa: E402

SCALE, OFF, PAD = 5.5, 3, 4


def refs():
    a = np.zeros((10, 10, 4), np.uint8)
    a[1:9, 1:9] = INK + [255]
    a[2:8, 2:8] = RED + [255]
    b = np.zeros((10, 10, 4), np.uint8)
    b[2:8, 3:7] = INK + [255]
    b[3:7, 4:6] = GLASS + [255]
    b[1, 4:6] = CORK + [255]
    c = np.zeros((8, 8, 4), np.uint8)
    c[1:7, 1:7] = INK + [255]
    c[2:6, 2:6] = PINK + [255]
    return {"heart.png": a, "bottle.png": b, "gem.png": c}


def render(a, s=SCALE, off=OFF, pad=PAD, seed=11):
    h, w = a.shape[:2]
    H, W = int(round(h * s)) + off + pad, int(round(w * s)) + off + pad
    c = np.zeros((H, W, 4), np.uint8)
    c[...] = SKY + [255]
    for v in range(off, off + int(round(h * s))):
        for u in range(off, off + int(round(w * s))):
            y, x = int((v - off) / s), int((u - off) / s)
            if a[y, x, 3]:
                c[v, u] = a[y, x]
    b = np.array(Image.fromarray(c, "RGBA").filter(ImageFilter.GaussianBlur(1.1))).astype(np.int16)
    b[..., :3] += np.random.default_rng(seed).integers(-7, 8, b[..., :3].shape).astype(np.int16)
    return np.clip(b, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    d = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    (d / "refs").mkdir(parents=True, exist_ok=True)
    Image.fromarray(render(potion()), "RGBA").save(d / "render.png")
    for name, r in refs().items():
        Image.fromarray(r, "RGBA").save(d / "refs" / name)
    print("wrote render.png and refs/heart.png, refs/bottle.png, refs/gem.png")
