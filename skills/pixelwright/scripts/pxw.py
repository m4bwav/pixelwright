#!/usr/bin/env python3
"""pxw.py (pixelwright): real pixel art made from a render, and sprite animation made in code from a still.

Make: a render or drawing is snapped to its true pixel grid, its background removed, its colours locked to a
palette, its outline and stray pixels cleaned, cropped to an engine size, and gated.
Animate: every pixel outside a brief's regions stays identical to the still, and colours are snapped to the
still's own palette plus the brief's declared extra colours, so a frame can never drift from the art it animates.

Commands (each prints one JSON object; exit 1 on failure, 2 on a usage error, which prints argparse's usage text):
  make    <recipe.json> <outdir> [--root DIR] [--no-aw]      the whole make pipeline from one recipe, then gates
  snap    <in.png> <out.png> [--scale S] [--offset X,Y]      detect the pixel grid; one pixel per block (mode)
  bg      <in.png> <out.png> [--colour auto|R,G,B] [--tol 40]  background flood-filled from the border to clear
  palette <in.png> <out.png> (--palette P | --colours N) [--dither bayer4] [--gpl OUT]  lock or extract colours
  clean   <in.png> <out.png> [--alpha 128] [--orphans] [--thin] [--outline auto|selective|R,G,B]
  crop    <in.png> <out.png> [--pad 0] [--size pow2|WxH] [--anchor bottom|centre]
  tile    <in.png> <out.png> [--band N]                     make a tile wrap, with no new colours
  palettes                                                   built-in palette names
  frames  <brief.json> <outdir> [--root DIR] [--only NAME]   sheets, frames, previews, contact sheets, gates
  grid    <image> <out.png> [--zoom 8] [--step 8]            zoomed still with coordinates, for writing regions
  mask    <brief.json> <out.png> [--root DIR] [--zoom 4]     every region tinted and labelled, to check a brief
  buildup <brief.json> <out.json> [--anim place] [--frames 6]  prefix an animation with construction frames
  assemble <brief.json> <out.json> --plan plan.json [--anim place]  prefix with crane/drone/trolley assembly,
                                                             or a natural site build ("vocabulary": "natural")
  contact <sheet.png> <out.png> --frames N [--per 5] [--zoom 3]
  pack    <out.png> <frame.png>...                           horizontal strip in the order given
  review  <dir> [--port 8765] [--extra items.json]           click page; every click saves <dir>/picks.json
  doctor                                                     versions, dependencies, artwright's aw.py

Needs Python 3.9+, numpy and Pillow. Works on Windows, macOS and Linux.
"""
import argparse
import datetime as dt
import html
import json
import math
import os
import random
import socket
import subprocess
import sys
from pathlib import Path

VERSION = "0.7.0"

try:
    import numpy as np
    from PIL import Image, ImageDraw
except ImportError as e:  # doctor still answers without them
    np = None
    MISSING = str(e)
else:
    MISSING = None


def out(obj, code=0):
    print(json.dumps(obj, indent=2))
    sys.exit(code)


def fail(msg, **extra):
    out(dict(ok=False, error=msg, **extra), 1)


def need_deps():
    if MISSING:
        fail(f"missing dependency: {MISSING}; install with: python -m pip install numpy pillow")


def load_rgba(path):
    return np.array(Image.open(path).convert("RGBA")).astype(np.float32)


def resolve(path, root, briefDir=None):
    """A brief's paths are relative to --root (default: the current folder), then to the brief's own folder."""
    p = Path(path)
    if p.is_absolute():
        return p
    for base in (root, briefDir):
        if base and (Path(base) / p).exists():
            return Path(base) / p
    return Path(root or ".") / p


def hsv(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = rgb.max(-1)
    mn = rgb.min(-1)
    d = mx - mn
    h = np.zeros_like(mx)
    nz = d > 1e-6
    rm = nz & (mx == r)
    gm = nz & (mx == g) & ~rm
    bm = nz & ~rm & ~gm
    h[rm] = ((g - b)[rm] / d[rm]) % 6
    h[gm] = ((b - r)[gm] / d[gm]) + 2
    h[bm] = ((r - g)[bm] / d[bm]) + 4
    h = h / 6.0
    s = np.where(mx > 1e-6, d / np.maximum(mx, 1e-6), 0)
    return h, s, mx


# Colour selectors narrow a region to its lit pixels: "warm" (fire, lamps), "cool" (screens, cells), "any".
SELECTORS = {
    "warm": lambda h, s, v: ((h < 0.16) | (h > 0.95)) & (s > 0.40) & (v > 0.40),
    "cool": lambda h, s, v: (h > 0.45) & (h < 0.68) & (s > 0.30) & (v > 0.35),
    "bright": lambda h, s, v: v > 0.70,
    "any": lambda h, s, v: np.ones_like(h, dtype=bool),
}


class Palette:
    """Nearest-colour snap to a fixed set of RGB colours."""

    def __init__(self, colours):
        self.c = np.unique(np.asarray(colours, dtype=np.float32).reshape(-1, 3), axis=0)

    def snap(self, rgb):
        flat = rgb.reshape(-1, 3)
        res = np.empty_like(flat)
        for i in range(0, len(flat), 2048):
            chunk = flat[i:i + 2048]
            d = ((chunk[:, None, :] - self.c[None, :, :]) ** 2).sum(-1)
            res[i:i + 2048] = self.c[d.argmin(1)]
        return res.reshape(rgb.shape)


class Sprite:
    def __init__(self, brief, root, briefDir=None):
        self.brief = brief
        self.root = root
        self.briefDir = briefDir
        self.id = brief.get("id") or brief.get("cardId")
        if not self.id:
            raise ValueError("brief needs an 'id'")
        self.still = load_rgba(resolve(brief["still"], root, briefDir))
        self.h, self.w = self.still.shape[:2]
        self.opaque = self.still[..., 3] > 0
        h, s, v = hsv(self.still[..., :3] / 255.0)
        self.hsv = (h, s, v)
        self.extras = np.asarray(brief.get("extraColours", []), dtype=np.float32).reshape(-1, 3)
        stillCols = self.still[..., :3][self.opaque]
        self.fullPalette = Palette(np.concatenate([stillCols, self.extras]))
        self.palettes = {}
        for name in ("warm", "cool", "bright"):
            sel = SELECTORS[name](h, s, v) & self.opaque
            cols = self.still[..., :3][sel]
            self.palettes[name] = Palette(np.concatenate([cols, self.extras])) if len(cols) else self.fullPalette
        self.regions = {name: self.region_mask(r) for name, r in brief["regions"].items()}
        for name, r in brief["regions"].items():
            for other in r.get("exclude", []):
                self.regions[name] &= ~self.regions[other]

    def rect_mask(self, rects):
        m = np.zeros((self.h, self.w), dtype=bool)
        if rects == "all":
            m[:] = True
            return m
        for x0, y0, x1, y1 in rects:
            m[y0:y1, x0:x1] = True
        return m

    def region_mask(self, r):
        m = self.rect_mask(r.get("rects", []))
        if "poly" in r:
            pm = Image.new("L", (self.w, self.h), 0)
            ImageDraw.Draw(pm).polygon([tuple(p) for p in r["poly"]], fill=255)
            m |= np.array(pm) > 0
        if "maskImage" in r:
            m |= np.array(Image.open(resolve(r["maskImage"], self.root, self.briefDir)).convert("L")) > 127
        if "model" in r:
            m |= _model_region(self, r["model"])
        sel = r.get("select")
        if sel:
            m &= SELECTORS[sel](*self.hsv) & self.opaque
        elif not r.get("alpha", False):
            m &= self.opaque
        return m

    def palette_for(self, region):
        sel = self.brief["regions"][region].get("select")
        return self.palettes.get(sel, self.fullPalette)


# ---- effects: each takes (sprite, frame RGBA float, k, track, frameIndex) and edits the frame in place ----
# k is the track's curve value for this frame (1.0 when the track has no curve).

_CACHE = {}


def _seeded(s, t, make):
    key = (id(s), json.dumps(t, sort_keys=True))
    if key not in _CACHE:
        _CACHE[key] = make(random.Random(t.get("seed", 1)))
    return _CACHE[key]


def fx_pulse(s, f, k, t, i):
    """Push the region's lit pixels toward a hot colour, snapped to the region's ramp. Blink and chase are
    pulses with on/off curves on several regions."""
    if k <= 0:
        return
    m = s.regions[t["region"]]
    hot = np.asarray(t["hot"], dtype=np.float32)
    rgb = f[..., :3][m]
    lum = rgb.mean(-1, keepdims=True) / 255.0
    w = np.clip(k * t.get("strength", 0.8) * (0.4 + 0.6 * lum), 0, 1)
    f[..., :3][m] = s.palette_for(t["region"]).snap(rgb + (hot - rgb) * w)


def fx_spill(s, f, k, t, i):
    """Light cast on the surface around a source rect, falling off with distance (additive, not a flat tint)."""
    if k <= 0:
        return
    m = s.regions[t["region"]]
    x0, y0, x1, y1 = t["source"]
    yy, xx = np.mgrid[0:s.h, 0:s.w]
    dx = np.maximum(0, np.maximum(x0 - xx, xx - (x1 - 1)))
    dy = np.maximum(0, np.maximum(y0 - yy, yy - (y1 - 1)))
    fall = np.clip(1 - np.sqrt(dx * dx + dy * dy) / t.get("radius", 10), 0, 1)
    fall[~m] = 0
    sel = fall > 0
    w = (k * t.get("strength", 0.5) * fall[sel])[:, None]
    f[..., :3][sel] = s.fullPalette.snap(f[..., :3][sel] + np.asarray(t["tint"], dtype=np.float32) * w)


def fx_darken(s, f, k, t, i):
    """Power off: desaturate and darken the region (k = 1 fully off)."""
    if k <= 0:
        return
    m = s.regions[t["region"]] & (f[..., 3] > 0)
    rgb = f[..., :3][m]
    grey = rgb.mean(-1, keepdims=True)
    rgb = rgb + (grey - rgb) * (k * t.get("desat", 0.7))
    rgb = rgb * (1 - k * t.get("amount", 0.55))
    f[..., :3][m] = (s.palette_for(t["region"]) if t.get("ramp") else s.fullPalette).snap(rgb)


def fx_glint(s, f, k, t, i):
    """A bright diagonal band sweeping across the region; k is the band's position (0 before, 1 past)."""
    m = s.regions[t["region"]]
    ys, xs = np.nonzero(m)
    if not len(xs) or k <= 0 or k >= 1:
        return
    slope = t.get("slope", 1.0)
    proj = xs + ys * slope
    lo, hi = proj.min(), proj.max()
    width = t.get("width", 3)
    centre = lo - width + k * (hi - lo + 2 * width)
    w = np.clip(1 - np.abs(proj - centre) / width, 0, 1) * t.get("strength", 0.8)
    on = w > 0
    rgb = f[ys[on], xs[on], :3]
    hot = np.asarray(t["hot"], dtype=np.float32)
    f[ys[on], xs[on], :3] = s.palette_for(t["region"]).snap(rgb + (hot - rgb) * w[on][:, None])


def fx_sparks(s, f, k, t, i):
    """1 px sparks thrown from the source, falling back, colour from hot to ember by age."""
    def make(rnd):
        x0, y0, x1, y1 = t["source"]
        vy = t.get("vy", [-3.4, -1.6])
        return [(rnd.choice(t["bornFrames"]), rnd.uniform(x0, x1), rnd.uniform(y0, y1), rnd.uniform(-1.6, 1.6),
                 rnd.uniform(*vy), rnd.randint(3, 5)) for _ in range(t.get("count", 14))]
    zone = s.regions[t["region"]]
    cols = [np.asarray(c, dtype=np.float32) for c in t["colours"]]
    for born, sx, sy, vx, vy, life in _seeded(s, t, make):
        age = i - born
        if age < 0 or age >= life:
            continue
        x = sx + vx * age
        y = sy + vy * age + t.get("gravity", 0.45) * age * age
        xi, yi = int(round(x)), int(round(y))
        c = cols[min(len(cols) - 1, int(age * len(cols) / life))]
        for px, py, a in ((xi, yi, 1.0), (int(round(x - vx * 0.5)), int(round(y - vy * 0.5)), 0.5)):
            if 0 <= px < s.w and 0 <= py < s.h and zone[py, px]:
                if a >= 1.0:
                    f[py, px, :3] = c
                    f[py, px, 3] = 255
                elif f[py, px, 3] > 0:
                    f[py, px, :3] = s.fullPalette.snap((f[py, px, :3] * 0.5 + c * 0.5)[None, None])[0, 0]


def _noise1d(n, seed, cell, unit=False):
    """Smooth 1D value noise over n samples: in [0, 1] with unit, else in [-1, 1]."""
    knots = np.random.default_rng(seed).uniform(0 if unit else -1, 1, n // max(1, cell) + 3)
    x = np.arange(n) / max(1, cell)
    i0 = np.floor(x).astype(int)
    fr = x - i0
    fr = fr * fr * (3 - 2 * fr)
    return (knots[i0] * (1 - fr) + knots[i0 + 1] * fr).astype(np.float32)


def fx_dust(s, f, k, t, i):
    """A dust band at the base: soft clouds (a coarse random grid smoothly upscaled, drifting outward) thinning
    as k goes to 0, so dust reads as clouds rather than per-pixel static."""
    if k <= 0:
        return
    m = s.regions[t["region"]]
    rnd = np.random.default_rng(t.get("seed", 3))
    yy, xx = np.mgrid[0:s.h, 0:s.w]
    y0, y1 = t["band"]
    cell = t.get("cell", 6)
    gw, gh = s.w // cell + 3, s.h // cell + 3
    grid = rnd.random((gh, gw)).astype(np.float32)
    drift = (1 - k) * t.get("drift", 4)
    gx = (xx + np.where(xx < s.w / 2, drift, -drift)) / cell + 1
    gy = yy / cell + 1
    x0i, y0i = np.floor(gx).astype(int), np.floor(gy).astype(int)
    fx, fy = gx - x0i, gy - y0i
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    x0i, y0i = np.clip(x0i, 0, gw - 2), np.clip(y0i, 0, gh - 2)
    noise = (grid[y0i, x0i] * (1 - fx) * (1 - fy) + grid[y0i, x0i + 1] * fx * (1 - fy)
             + grid[y0i + 1, x0i] * (1 - fx) * fy + grid[y0i + 1, x0i + 1] * fx * fy)
    top = y1 - (y1 - y0) * k
    if t.get("lumpy"):
        # a cloud bank, not a stripe: the haze reaches a different height in every column
        top = y1 - (y1 - y0) * k * (0.45 + 0.55 * _noise1d(s.w, t.get("seed", 3) + 1, 9, unit=True))[None, :]
    depth = np.clip((yy - top) / np.maximum(1.0, (y1 - top)), 0, 1)
    density = np.clip((noise * 0.8 + depth * 0.6 - 0.45) * 2.2, 0, 1) * k
    cover = m & (yy >= top) & (density > 0.05)
    dust = np.asarray(t["colour"], dtype=np.float32)
    rgb = f[..., :3][cover]
    a = (density[cover] * t.get("opacity", 0.7))[:, None]
    f[..., :3][cover] = s.fullPalette.snap(rgb + (dust - rgb) * a)


def _grow_fill(s, part, t):
    """Ground grown into the part's hole from the texture around it (Efros-Leung): from the edge inward, each pixel
    copies the source pixel whose known 5x5 neighbourhood matches best, picked at random among the closest four
    (seeded) so it neither smears nor tiles. Sources are `growFrom` (a region) or the opaque pixels within
    `growRadius` (22) of the hole; never the part or the pixel ring touching it. Cached per part."""
    key = (t["part"], t.get("growFrom"), t.get("growRadius", 22), t.get("seed", 5))
    cache = s.__dict__.setdefault("_grown", {})
    if key in cache:
        return cache[key]
    src = s.still
    h, w = part.shape
    ring = part.copy()
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        ring |= np.roll(np.roll(part, dy, 0), dx, 1)
    if t.get("growFrom"):
        pool = s.regions[t["growFrom"]].copy()
    else:
        ys, xs = np.nonzero(part)
        r = t.get("growRadius", 22)
        pool = np.zeros(part.shape, bool)
        pool[max(0, ys.min() - r):ys.max() + r + 1, max(0, xs.min() - r):xs.max() + r + 1] = True
        pool &= src[..., 3] == 255
    pool &= ~ring
    pool[:2] = pool[-2:] = False
    pool[:, :2] = pool[:, -2:] = False
    sy, sx = np.nonzero(pool)
    out = src.copy()
    if not len(sy):
        cache[key] = out
        return out
    rnd = random.Random(t.get("seed", 5))
    known = ~part
    offs = [(dy, dx) for dy in range(-2, 3) for dx in range(-2, 3) if (dy, dx) != (0, 0)]
    while not known.all():
        grown = known.copy()
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            grown |= np.roll(np.roll(known, dy, 0), dx, 1)
        front = list(zip(*np.nonzero(part & ~known & grown)))
        front.sort(key=lambda q: -sum(1 for dy, dx in offs
                                      if 0 <= q[0] + dy < h and 0 <= q[1] + dx < w and known[q[0] + dy, q[1] + dx]))
        for y, x in front:
            idx = [(dy, dx) for dy, dx in offs if 0 <= y + dy < h and 0 <= x + dx < w and known[y + dy, x + dx]]
            want = np.array([out[y + dy, x + dx, :3] for dy, dx in idx], dtype=np.float32)
            have = np.stack([src[sy + dy, sx + dx, :3] for dy, dx in idx], 1)
            err = ((have - want[None]) ** 2).sum((1, 2))
            best = np.argsort(err)[:4]
            j = best[rnd.randrange(len(best))]
            out[y, x] = src[sy[j], sx[j]]
            known[y, x] = True
    cache[key] = out
    return out


def _behind(s, f, part, t):
    """What shows where a moving part used to be: a repainted plate image, transparent sky, the still, the nearest
    pixel on the row, or ground grown from the texture around it."""
    mode = t.get("behind", "plate" if t.get("plate") else "clear")
    if mode == "grow":
        f[part] = _grow_fill(s, part, t)[part]
    elif mode == "plate":
        plate = load_rgba(resolve(t["plate"], s.root, s.briefDir))
        f[part] = plate[part]
    elif mode == "clear":
        f[part] = 0
    elif mode == "nearest":
        # painted art with no plate: each vacated pixel takes the nearest non-part pixel on its row (6 px at most)
        src = s.still
        for y, x in zip(*np.nonzero(part)):
            for d in range(1, 7):
                hit = [q for q in (x - d, x + d) if 0 <= q < s.w and not part[y, q] and src[y, q, 3] > 0]
                if hit:
                    f[y, x] = src[y, hit[0]]
                    break


def _place(s, f, ys, xs, px, t):
    """Put moved part pixels down. With `soft: "over"` a semi-transparent pixel (a painted part's soft rim) is
    composited over what is already there, snapped to the region's ramp, instead of replacing it: a rim pixel at
    alpha 40 that lands on a wall must not punch a hole in the wall."""
    if t.get("soft") != "over":
        f[ys, xs] = px
        return
    a = px[:, 3:4] / 255.0
    under = f[ys, xs]
    ua = under[:, 3:4] / 255.0
    oa = a + ua * (1 - a)
    rgb = (px[:, :3] * a + under[:, :3] * ua * (1 - a)) / np.maximum(oa, 1e-6)
    out = np.concatenate([rgb, np.round(oa * 255)], axis=1)
    mixed = (a[:, 0] < 1) & (ua[:, 0] > 0)
    if mixed.any():
        out[mixed, :3] = s.palette_for(t["region"]).snap(out[mixed, :3])
    out[~mixed] = np.where(a[~mixed] > 0, px[~mixed], under[~mixed])
    f[ys, xs] = out


def _plane_matrix(plane, pivot):
    """The 2x2 matrix A that maps the part's own turning plane to the screen: a circle of radius 1 in that plane
    shows at pivot + A [cos p, sin p]. `plane` is [[ux, uy], [vx, vy]] (the screen images of the plane's two axes)
    or {"rim": [[x, y], ...]}: rim points evenly spaced around the turning circle, in turning order (fitted)."""
    if isinstance(plane, dict):
        rim = np.asarray(plane["rim"], dtype=float) - np.asarray(pivot, dtype=float)
        ph = 2 * math.pi * np.arange(len(rim)) / len(rim)
        sol = np.linalg.lstsq(np.stack([np.cos(ph), np.sin(ph)], 1), rim, rcond=None)[0]
        return sol.T
    return np.asarray(plane, dtype=float).T


def fx_rotate(s, f, k, t, i):
    """Cut a part out and rotate it about a pivot by k degrees (+ = clockwise on screen). Samples 4x4 per target
    pixel and takes the most common part colour, so no new colours and no rotation blur. With `plane` the part turns
    in a plane seen at an angle (a wheel face, a tilted gear): T = A R(k) A^-1 about the pivot, and + turns the
    plane's first axis toward its second (rim point j toward j + 1)."""
    part = s.regions[t["part"]]
    zone = s.regions[t["region"]]
    src = np.round(s.still).astype(np.uint8)
    _behind(s, f, part, t)
    px, py = t["pivot"]
    a = math.radians(k)
    ca, sa = math.cos(-a), math.sin(-a)
    if t.get("plane") is not None:
        A = _plane_matrix(t["plane"], t["pivot"])
        M = A @ np.array([[ca, -sa], [sa, ca]]) @ np.linalg.inv(A)
    else:
        M = None
    ys, xs = np.nonzero(zone)
    subs = [(j + 0.5) / 4 for j in range(4)]
    for x, y in zip(xs, ys):
        votes = {}
        n = 0
        for sy in subs:
            for sx in subs:
                dx, dy = x + sx - px, y + sy - py
                if M is None:
                    qx = int(math.floor(px + dx * ca - dy * sa))
                    qy = int(math.floor(py + dx * sa + dy * ca))
                else:
                    qx = int(math.floor(px + M[0, 0] * dx + M[0, 1] * dy))
                    qy = int(math.floor(py + M[1, 0] * dx + M[1, 1] * dy))
                if 0 <= qx < s.w and 0 <= qy < s.h and part[qy, qx]:
                    c = tuple(src[qy, qx])
                    votes[c] = votes.get(c, 0) + 1
                    n += 1
        if n >= 8:
            f[y, x] = max(votes.items(), key=lambda kv: kv[1])[0]


def fx_shift(s, f, k, t, i):
    """Move a part by whole pixels: offset = round(k * [dx, dy]). A recoil, a plunging drill, a bobbing auger.
    Behind defaults to "still" (the old pixels stay, which reads as a stretch for 1 to 2 px moves)."""
    part = s.regions[t["part"]]
    zone = s.regions[t["region"]]
    ox, oy = int(round(k * t["by"][0])), int(round(k * t["by"][1]))
    if ox == 0 and oy == 0:
        return
    src = s.still.copy()
    if t.get("behind", "still") != "still":
        _behind(s, f, part, t)
    ys, xs = np.nonzero(part)
    nx, ny = xs + ox, ys + oy
    ok = (nx >= 0) & (nx < s.w) & (ny >= 0) & (ny < s.h)
    nx, ny, xs, ys = nx[ok], ny[ok], xs[ok], ys[ok]
    inside = zone[ny, nx]
    _place(s, f, ny[inside], nx[inside], src[ys[inside], xs[inside]], t)


def fx_bend(s, f, k, t, i):
    """Sway a hanging part (cloth, a hide, a plant) about its anchor row: each row moves sideways by
    round(k * amp * depth ** power), depth 0 at the anchor and 1 at the far end, so the rail holds and the hem
    swings. `anchor` "top" (default) or "bottom" (rooted below). Behind defaults to "nearest"."""
    part = s.regions[t["part"]]
    zone = s.regions[t["region"]]
    ys, xs = np.nonzero(part)
    if not len(ys):
        return
    y0, y1 = ys.min(), ys.max()
    span = max(1, y1 - y0)
    depth = (ys - y0) / span if t.get("anchor", "top") == "top" else (y1 - ys) / span
    ox = np.round(k * t.get("amp", 2) * depth ** t.get("power", 1.5)).astype(int)
    if not ox.any():
        return
    src = s.still.copy()
    _behind(s, f, part, dict(t, behind=t.get("behind", "nearest")))
    nx = xs + ox
    ok = (nx >= 0) & (nx < s.w)
    ok[ok] = zone[ys[ok], nx[ok]]
    _place(s, f, ys[ok], nx[ok], src[ys[ok], xs[ok]], t)


def fx_brighten(s, f, k, t, i):
    """Brighten (k > 0) or dim (k < 0) the region's own pixels by multiplying them, warm-tinted, so painted
    texture keeps its contrast (pulse lerps toward one colour and flattens it, L-017). Snapped to the region's
    ramp. With `hotspot` [x, y] the gain falls off with distance to `radius` (down to `floor` of it), and `coreTint`
    takes over from `tint` toward the hotspot: a fire hottest at the back lights the walls around it."""
    if k == 0:
        return
    m = s.regions[t["region"]]
    tint = np.asarray(t.get("tint", [1.0, 0.8, 0.5]), dtype=np.float32)
    rgb = f[..., :3][m]
    w = np.ones((len(rgb), 1), dtype=np.float32)
    if "hotspot" in t:
        ys, xs = np.nonzero(m)
        d = np.hypot(xs - t["hotspot"][0], ys - t["hotspot"][1]) / t.get("radius", 8)
        floor = t.get("floor", 0.2)
        w = (floor + (1 - floor) * np.clip(1 - d, 0, 1))[:, None].astype(np.float32)
        if "coreTint" in t:
            core = np.asarray(t["coreTint"], dtype=np.float32)
            tint = tint + (core - tint) * np.clip(1 - d, 0, 1)[:, None] ** 2
    f[..., :3][m] = s.palette_for(t["region"]).snap(np.clip(rgb * (1 + k * t.get("gain", 0.6) * w * tint), 0, 255))


def fx_bands(s, f, k, t, i):
    """Soft brightness bands drifting along `dir` (cloth advancing over a loom, a belt on painted art): the
    pixels stay put and only a multiply moves, so texture and shading survive where `scroll` would need a
    periodic pattern. Band centres sit every `period` px along dir from `origin`, shifted by k * period, so k
    from 0 to 1 is one seamless cycle; a fractional shift spreads a band over two pixels (sub-pixel speed)."""
    m = s.regions[t["region"]]
    period = t["period"]
    dx, dy = t.get("dir", [1, 0])
    n = math.hypot(dx, dy)
    ox, oy = t.get("origin", [0, 0])
    ys, xs = np.nonzero(m)
    u = ((xs - ox) * dx + (ys - oy) * dy) / n - k * period
    d = np.abs((u + period / 2) % period - period / 2)
    w = np.clip(1 - d / t.get("width", 1.0), 0, 1)[:, None].astype(np.float32)
    if not w.any():
        return
    tint = np.asarray(t.get("tint", [1.0, 1.0, 1.0]), dtype=np.float32)
    rgb = f[..., :3][m]
    f[..., :3][m] = s.palette_for(t["region"]).snap(np.clip(rgb * (1 + t.get("gain", -0.2) * w * tint), 0, 255))


def fx_scroll(s, f, k, t, i):
    """Stripes or a belt creeping along: the region's pixels move by round(k * period) along `dir`, wrapping
    with the pattern's period, so the content never changes, only its phase."""
    m = s.regions[t["region"]]
    period = t["period"]
    off = int(round(k * period)) % period
    if off == 0:
        return
    dx, dy = t.get("dir", [1, 0])
    src = s.still.copy()
    ys, xs = np.nonzero(m)
    sx, sy = xs - dx * off, ys - dy * off
    for _ in range(4):
        bad = ~((sx >= 0) & (sx < s.w) & (sy >= 0) & (sy < s.h))
        bad[~bad] = ~m[sy[~bad], sx[~bad]]
        if not bad.any():
            break
        sx[bad] += dx * period
        sy[bad] += dy * period
    ok = (sx >= 0) & (sx < s.w) & (sy >= 0) & (sy < s.h)
    ok[ok] = m[sy[ok], sx[ok]]
    f[ys[ok], xs[ok]] = src[sy[ok], sx[ok]]


def fx_fill(s, f, k, t, i):
    """A level filling bottom to top (cells charging, a tank filling): region pixels above the level are dimmed,
    pixels at the level line get the hot colour. k = share full."""
    m = s.regions[t["region"]]
    ys, xs = np.nonzero(m)
    if not len(ys):
        return
    top, bot = ys.min(), ys.max() + 1
    level = bot - k * (bot - top)
    empty = ys < level
    rgb = f[ys[empty], xs[empty], :3]
    f[ys[empty], xs[empty], :3] = s.palette_for(t["region"]).snap(rgb * (1 - t.get("dim", 0.6)))
    if t.get("hot") and 0 < k < 1:
        line = (ys >= level) & (ys < level + 1)
        hot = np.asarray(t["hot"], dtype=np.float32)
        rgb = f[ys[line], xs[line], :3]
        f[ys[line], xs[line], :3] = s.palette_for(t["region"]).snap(rgb + (hot - rgb) * 0.8)


def fx_puffs(s, f, k, t, i):
    """Steam or smoke puffs from a vent: rise, drift, grow and thin out (dithered, binary alpha, two shades)."""
    def make(rnd):
        return [(born, t["source"][0] + rnd.uniform(-1, 1), t["source"][1], rnd.uniform(*t.get("vx", [0.3, 1.0])),
                 rnd.uniform(-2.2, -1.4), t.get("life", 6)) for born in t["bornFrames"]]
    zone = s.regions[t["region"]]
    light, mid = [np.asarray(c, dtype=np.float32) for c in t["colours"][:2]]
    hashN = np.random.default_rng(t.get("seed", 5)).random((s.h, s.w))
    yy, xx = np.mgrid[0:s.h, 0:s.w]
    for born, sx, sy, vx, vy, life in _seeded(s, t, make):
        age = i - born
        if age < 0 or age >= life:
            continue
        cx, cy = sx + vx * age, sy + vy * age * (1 - 0.06 * age)
        r = t.get("r0", 1.2) + t.get("grow", 0.55) * age
        keep = (1 - age / life) ** 0.6
        d = np.sqrt((xx + 0.5 - cx) ** 2 + (yy + 0.5 - cy) ** 2)
        cover = zone & (d <= r) & (hashN < keep + 0.15 * (1 - d / r))
        shade = ((xx + 0.5 - cx) + (yy + 0.5 - cy)) > 0
        f[cover & ~shade, :3] = light
        f[cover & shade, :3] = mid
        f[cover, 3] = 255


def fx_buildup(s, f, k, t, i):
    """Construction reveal from the ground up (k = share built, 1 = done): above a ragged build line the sprite is
    cut away except a dotted outline of its silhouette; the line glows as a weld seam and throws sparks. Put it
    last in the track list so it cuts what the other tracks drew."""
    if k >= 1:
        return
    ys, xs = np.nonzero(s.opaque)
    yTop, yBot = int(ys.min()), int(ys.max()) + 1
    rnd = np.random.default_rng(t.get("seed", 9))
    jitter = rnd.integers(0, t.get("jitter", 2) + 1, s.w)
    line = np.round(yBot - k * (yBot - yTop)).astype(int) - jitter
    yy, xx = np.mgrid[0:s.h, 0:s.w]
    above = yy < line[None, :]
    pad = np.pad(s.opaque, 1)
    edge = s.opaque & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    ghost = above & edge & (((xx + yy + i) % 3) == 0)
    f[above & ~ghost] = 0
    if ghost.any():
        f[ghost, :3] = np.asarray(t["ghost"], dtype=np.float32)
        f[ghost, 3] = 255
    weld = [np.asarray(c, dtype=np.float32) for c in t["weld"]]
    seam = s.opaque & (yy == line[None, :])
    f[seam & ((xx % 2) == 0), :3] = weld[0]
    f[seam & ((xx % 2) == 1), :3] = weld[1 % len(weld)]
    f[seam, 3] = 255
    fr = random.Random(t.get("seed", 9) * 100 + i)
    cols = np.nonzero(s.opaque.any(0))[0]
    for _ in range(t.get("sparks", 6)):
        x = int(fr.choice(cols))
        y = int(line[x]) - fr.randint(1, 4)
        if 0 <= y < s.h:
            f[y, x, :3] = weld[fr.randrange(len(weld))]
            f[y, x, 3] = 255


# Colours of the construction machines `assemble` draws (crane rigging, drones, trolleys, weld seam).
MACHINE = {"dark": [38, 40, 46], "mid": [96, 100, 108], "light": [170, 172, 176], "accent": [232, 178, 40],
           "lamp": [230, 52, 40], "cable": [124, 128, 136]}
WELD = [[255, 250, 220], [255, 214, 110], [255, 150, 40]]
DUST = [[150, 140, 125], [178, 168, 150]]


def _assemble_parts(s, t):
    """Each step's part mask, exclusive: a pixel belongs to the first step (in list order) whose part holds it."""
    key = ("asm", id(s), json.dumps(t["steps"], sort_keys=True))
    if key not in _CACHE:
        taken = np.zeros((s.h, s.w), dtype=bool)
        parts = []
        for st in t["steps"]:
            m = s.regions[st["part"]] & ~taken
            taken |= m
            ys, xs = np.nonzero(m)
            bb = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1) if len(xs) else (0, 0, 0, 0)
            parts.append((st, m, bb))
        _CACHE[key] = (parts, taken)
    return _CACHE[key]


def _put(f, s, x, y, c, behind=False):
    if 0 <= x < s.w and 0 <= y < s.h and (not behind or f[y, x, 3] == 0):
        f[y, x, :3] = c
        f[y, x, 3] = 255


def _paste(f, s, src, m, ox, oy, clip=None):
    """Copy the masked pixels of src into f moved by (ox, oy); clip = (x0, y0, x1, y1) limits where they land."""
    ys, xs = np.nonzero(m)
    nx, ny = xs + ox, ys + oy
    ok = (nx >= 0) & (nx < s.w) & (ny >= 0) & (ny < s.h)
    if clip:
        ok &= (nx >= clip[0]) & (nx < clip[2]) & (ny >= clip[1]) & (ny < clip[3])
    f[ny[ok], nx[ok]] = src[ys[ok], xs[ok]]


def _drone(f, s, M, cx, y, i):
    """A 13 x 3 px quadcopter: rotor row (spinning: alternates every frame), arms with a yellow hub, body with a
    blinking nav lamp. y is the body row."""
    for dx in ((-6, -5, -4, 4, 5, 6) if i % 2 == 0 else (-5, -4, -3, 3, 4, 5)):
        _put(f, s, cx + dx, y - 2, M["light"])
    for dx in range(-5, 6):
        _put(f, s, cx + dx, y - 1, M["mid"])
    for dx in (-5, 5):
        _put(f, s, cx + dx, y - 1, M["dark"])
    for dx in (-1, 0, 1):
        _put(f, s, cx + dx, y - 1, M["accent"])
    for dx in (-2, -1, 0, 1, 2):
        _put(f, s, cx + dx, y, M["dark"])
    if i % 4 < 2:
        _put(f, s, cx + 2, y, M["lamp"])


def _trail(f, s, M, pts):
    """A drone's motion trail: its body centre at earlier times, a solid dot then dithered dots, drawn only on
    empty pixels so it never paints over the building. pts = [(x, y), ...] newest first."""
    for n, (x, y) in enumerate(pts):
        x, y = int(round(x)), int(round(y))
        if n == 0 or (x + y) % 2 == 0:
            _put(f, s, x, y, M["cable"] if n == 0 else M["mid"], behind=True)


def _ease(p):
    """Slow in, slow out, never stalled: half linear, half smoothstep."""
    p = min(1.0, max(0.0, p))
    return 0.5 * p + 0.5 * p * p * (3 - 2 * p)


def _weld_front(st, bb, p):
    """The weld front at progress p: (axis, front) where front[k] is the seam position for row k (dir right/left,
    axis "x") or column k (dir up/down, axis "y") of the part's box, ragged by `ragged` px of smooth noise and
    travelling past both ends so p = 0 shows nothing and p = 1 all."""
    x0, y0, x1, y1 = bb
    d = st.get("dir", "up")
    amp = st.get("ragged", 2)
    pe = _ease(p)
    if d in ("right", "left"):
        off = np.round(_noise1d(y1 - y0, st.get("seed", 5) + 17, 3) * amp).astype(int)
        line = (x0 - amp) + pe * (x1 - x0 + 2 * amp) if d == "right" else (x1 + amp) - pe * (x1 - x0 + 2 * amp)
        return "x", np.round(line).astype(int) + off
    off = np.round(_noise1d(x1 - x0, st.get("seed", 5) + 17, 4) * amp).astype(int)
    line = (y1 + amp) - pe * (y1 - y0 + 2 * amp) if d == "up" else (y0 - amp) + pe * (y1 - y0 + 2 * amp)
    return "y", np.round(line).astype(int) + off


def _torch(st, m, bb, p, t):
    """Where the welding drone's torch touches the seam at progress p and time t: (x, y). Along a vertical seam
    (dir right/left) it rides the front's top; along a horizontal seam it glides back and forth (cosine
    ping-pong, `speed` px per frame), so it never jumps."""
    x0, y0, x1, y1 = bb
    axis, front = _weld_front(st, bb, p)
    if axis == "x":
        x = int(min(x1 - 1, max(x0, front[0])))
        col = np.nonzero(m[:, x])[0]
        return x, int(col.min()) if len(col) else y0
    w = max(1, x1 - x0 - 4)
    u = (t - st["at"][0]) * st.get("speed", 4) / w
    x = int(round(x0 + 2 + w * (0.5 - 0.5 * math.cos(math.pi * u))))
    return x, int(front[min(len(front) - 1, max(0, x - x0))])


def _drones_at(st, m, bb, t, ground):
    """Body positions [(x, y)] of the drones serving a step at time t (fractional for trails): carriers while it
    flies in, the welding drone while it welds, and both as they leave for 3 frames after."""
    a, b = st["at"]
    how = st["how"]
    if how not in ("drone", "weld") or t < a or t >= b + 4:
        return []
    x0, y0, x1, y1 = bb
    w = x1 - x0
    n = st.get("drones", 2 if w >= 24 else 1) if how == "drone" else 1
    bob = round(math.sin(t * 1.9 + x0) * 0.8)
    if t >= b:
        j = t - b + 1
        if how == "weld":
            tx, ty = _torch(st, m, bb, 1.0, b)
            return [(tx + 5 * j, ty - 5 - 6 * j)]
        return [(x0 + w * (d + 1) / (n + 1) + (5 * j if d >= n / 2 else -5 * j), y0 - 4 - 6 * j) for d in range(n)]
    p = (t - a) / max(1, b - a)
    if how == "weld":
        tx, ty = _torch(st, m, bb, p, t)
        return [(tx, ty - 5 + bob)]
    e = p * p * (3 - 2 * p)
    fx_, fy_ = st.get("from", [-24, -(y1 + 8)])
    ox, oy = (1 - e) * fx_, (1 - e) * fy_
    return [(x0 + ox + w * (d + 1) // (n + 1), y0 + oy - 4 + bob) for d in range(n)]


def _dust_sources(parts, j, ground):
    """Where the machines kick up dust at frame j: [(x, y, vx)]. A trolley's rear wheel while it rolls, the welding
    torch when it works within 16 px of the ground, a drone's downwash as its load comes down near the ground,
    and a touchdown puff at both bottom corners when a crane, drone or trolley load sets down there."""
    src = []
    for st, m, bb in parts:
        a, b = st["at"]
        x0, y0, x1, y1 = bb
        how = st["how"]
        if not m.any() or j < a or j > b:
            continue
        p = (j - a) / max(1, b - a)
        if j == b:
            if how in ("crane", "drone", "trolley") and y1 >= ground - 4:
                src += [(x0 + 1, y1 - 1, -0.7), (x1 - 2, y1 - 1, 0.7)]
            continue
        if how == "trolley":
            fx_ = st.get("from", [-(x1 + 4), 0])[0]
            ox = int(round((1 - p) * fx_))
            rear = (x1 - 2 + ox) if fx_ > 0 else (x0 + 1 + ox)
            src.append((rear, y1 - 1, 0.6 if fx_ > 0 else -0.6))
        elif how == "weld":
            tx, ty = _torch(st, m, bb, p, j)
            if ty >= ground - 16:
                src.append((tx, ty, 0.5 if j % 2 else -0.5))
        elif how == "drone" and p > 0.55:
            e = p * p * (3 - 2 * p)
            fx_, fy_ = st.get("from", [-24, -(y1 + 8)])
            ox, oy = (1 - e) * fx_, (1 - e) * fy_
            if y1 + oy >= ground - 12:
                src += [(x0 + ox + 2, ground - 1, -0.8), (x1 + ox - 3, ground - 1, 0.8)]
        elif how == "crane" and p > 0.8 and y1 >= ground - 4:
            src += [(x0 + 1, y1 - 1, -0.5), (x1 - 2, y1 - 1, 0.5)]
    return src


def _dust_puffs(f, s, parts, i, ground, cols, end, total=None):
    """Draw the dust the machines kicked up in frames before and at i: each source spawns a small cloud that drifts
    outward and up, grows and thins (dithered, two shades) over 7 frames. Only during assembly and just after."""
    hashN = np.random.default_rng(13).random((s.h, s.w))
    yy, xx = np.mgrid[0:s.h, 0:s.w]
    light, mid = np.asarray(cols[-1], dtype=np.float32), np.asarray(cols[0], dtype=np.float32)
    life = 7
    for born in range(max(0, i - life + 1), min(i, end) + 1):
        age = i - born
        if total and born + life > total - 1:
            # a puff must be gone by the last (rest) frame: shorten its life to fit
            if age >= total - 1 - born:
                continue
            keepScale = life / max(1, total - 1 - born)
        else:
            keepScale = 1.0
        for x, y, vx in _dust_sources(parts, born, ground):
            cx, cy = x + 0.5 + vx * age * 1.4, y + 0.5 - 0.45 * age
            r = 1.0 + 0.6 * age
            keep = max(0.0, 1 - age * keepScale / life) ** 0.8
            box = (slice(max(0, int(cy - r - 1)), min(s.h, int(cy + r + 2))),
                   slice(max(0, int(cx - r - 1)), min(s.w, int(cx + r + 2))))
            d = np.sqrt((xx[box] + 0.5 - cx) ** 2 + (yy[box] + 0.5 - cy) ** 2)
            # a solid blob with a ragged rim; past half its life it breaks into an even checker, then is gone
            cover = d <= r * (0.7 + 0.3 * hashN[box])
            if keep < 0.6:
                cover &= ((xx[box] + yy[box] + born) % 2) == 0
            if keep < 0.25:
                cover &= hashN[box] < 0.5
            shade = (yy[box] + 0.5 - cy) > -0.5
            sub = f[box]
            sub[cover & shade, :3] = mid
            sub[cover & ~shade, :3] = light
            sub[cover, 3] = 255


def fx_assemble(s, f, k, t, i):
    """Realistic construction, ending on the still: the still is split into parts (steps, each a region) and each
    part arrives its own way between frames `at` [start, end]:
      crane      lowered on a cable from off-frame, spreader bar and slings, the hook rises away after
      drone      carried on tethers by 1 or 2 quadcopters, which fly off after
      trolley    rolled in from the side on a low cart (part lifted 2 px), the cart backs out behind
      telescope  extends out of its own base (dir up|down|left|right), like a mast or a stack
      hinge      swings open about a pivot from `angle` degrees to 0 (an arm unfolding)
      weld       built on site: revealed along dir behind a ragged hot seam (`ragged` px), a welding drone gliding
                 along it with its torch on the seam, sparks at the torch
    Drones leave short motion trails. Machines kick up dust (`dust` colours, false turns it off) where they work
    near the ground. Before its start a part is absent (transparent); after its end it is in place. Pixels in no
    step stay from frame 0 (pxw.py assemble reports them). Put it last so it carries the other tracks' pixels."""
    M = dict(MACHINE, **t.get("machine", {}))
    M = {kk: np.asarray(v, dtype=np.float32) for kk, v in M.items()}
    weld = [np.asarray(c, dtype=np.float32) for c in t.get("weld", WELD)]
    parts, union = _assemble_parts(s, t)
    ys_, _ = np.nonzero(s.opaque)
    ground = int(ys_.max()) + 1 if len(ys_) else s.h
    end = max(st["at"][1] for st, _, _ in parts)
    src = f.copy()
    f[union] = 0
    if i < end:
        f[~s.opaque] = 0  # what earlier tracks drew outside the silhouette waits until the building stands
    moving, after = [], []
    for st, m, bb in parts:
        a, b = st["at"]
        if i < a or not m.any():
            continue
        if i >= b:
            f[m] = src[m]
            if i - b < 4:
                after.append((st, m, bb, i - b + 1))
        else:
            moving.append((st, m, bb, (i - a) / max(1, b - a)))
    for st, m, bb, j in after:
        x0, y0, x1, y1 = bb
        cx = (x0 + x1) // 2
        how = st["how"]
        if how == "crane":
            top = y0 - 3 - 9 * j
            for dx in range(-min(6, (x1 - x0) // 3), min(6, (x1 - x0) // 3) + 1):
                _put(f, s, cx + dx, top, M["accent"])
            for y in range(0, top):
                _put(f, s, cx, y, M["cable"])
        elif how == "trolley":
            sign = 1 if st.get("from", [-40, 0])[0] > 0 else -1
            ox = sign * 12 * j
            for x in range(x0 + 1 + ox, x1 - 1 + ox):
                _put(f, s, x, y1 - 2, M["mid"], behind=True)
                _put(f, s, x, y1 - 1, M["dark"] if (x + i) % 4 else M["light"], behind=True)
    for st, m, bb, p in moving:
        x0, y0, x1, y1 = bb
        w, h = x1 - x0, y1 - y0
        how = st["how"]
        cx = (x0 + x1) // 2
        if how == "crane":
            e = 1 - (1 - p) ** 2
            fx_, fy_ = st.get("from", [0, -(y1 + 4)])
            ox, oy = int(round((1 - e) * fx_)), int(round((1 - e) * fy_))
            _paste(f, s, src, m, ox, oy)
            top, cx = y0 + oy, cx + ox
            bw = min(6, w // 3)
            for dx in range(-bw, bw + 1):
                _put(f, s, cx + dx, top - 3, M["accent"])
            for r, frac in ((top - 2, 0.5), (top - 1, 1.0)):
                _put(f, s, cx - bw - int(round(frac * max(0, (w // 2 - 2 - bw)))), r, M["cable"])
                _put(f, s, cx + bw + int(round(frac * max(0, (w // 2 - 2 - bw)))), r, M["cable"])
            for dx in (-1, 0, 1):
                _put(f, s, cx + dx, top - 4, M["dark"])
            for y in range(0, top - 4):
                _put(f, s, cx, y, M["cable"])
        elif how == "drone":
            e = p * p * (3 - 2 * p)
            fx_, fy_ = st.get("from", [-24, -(y1 + 8)])
            ox, oy = int(round((1 - e) * fx_)), int(round((1 - e) * fy_))
            _paste(f, s, src, m, ox, oy)
            for dcx, dy in _drones_at(st, m, bb, i, ground):
                for y in range(int(dy) + 1, y0 + oy):
                    _put(f, s, int(dcx), y, M["cable"])
        elif how == "trolley":
            fx_ = st.get("from", [-(x1 + 4), 0])[0]
            ox = int(round((1 - p) * fx_))
            for x in range(x0 + 1 + ox, x1 - 1 + ox):
                _put(f, s, x, y1 - 2, M["mid"])
                _put(f, s, x, y1 - 1, M["dark"] if (x + i) % 4 else M["light"])
            _paste(f, s, src, m, ox, -2)
        elif how == "telescope":
            d = st.get("dir", "up")
            ext = {"up": (0, h), "down": (0, -h), "left": (w, 0), "right": (-w, 0)}[d]
            ox, oy = int(round((1 - p) * ext[0])), int(round((1 - p) * ext[1]))
            _paste(f, s, src, m, ox, oy, clip=bb)
        elif how == "hinge":
            e = 1 - (1 - p) ** 2
            px, py = st["pivot"]
            ang = math.radians((1 - e) * st.get("angle", -60))
            ca, sa = math.cos(-ang), math.sin(-ang)
            r = int(math.hypot(max(abs(x0 - px), abs(x1 - px)), max(abs(y0 - py), abs(y1 - py)))) + 1
            subs = [(q + 0.5) / 3 for q in range(3)]
            for y in range(max(0, py - r), min(s.h, py + r + 1)):
                for x in range(max(0, px - r), min(s.w, px + r + 1)):
                    votes = {}
                    for sy in subs:
                        for sx in subs:
                            dx, dy = x + sx - px, y + sy - py
                            qx = int(math.floor(px + dx * ca - dy * sa))
                            qy = int(math.floor(py + dx * sa + dy * ca))
                            if 0 <= qx < s.w and 0 <= qy < s.h and m[qy, qx]:
                                c = tuple(src[qy, qx])
                                votes[c] = votes.get(c, 0) + 1
                    if sum(votes.values()) >= 5:
                        f[y, x] = max(votes.items(), key=lambda kv: kv[1])[0]
        elif how == "weld":
            axis, front = _weld_front(st, bb, p)
            yy, xx = np.mgrid[y0:y1, x0:x1]
            if axis == "x":
                fr = front[:, None]
                done = (xx < fr) if st.get("dir") == "right" else (xx >= fr)
                seam = xx == fr
            else:
                fr = front[None, :]
                done = (yy >= fr) if st.get("dir", "up") == "up" else (yy < fr)
                seam = yy == fr
            mb = m[y0:y1, x0:x1]
            done &= mb
            seam &= mb
            box = f[y0:y1, x0:x1]
            box[done] = src[y0:y1, x0:x1][done]
            box[seam & ((xx + yy + i) % 2 == 0), :3] = weld[0]
            box[seam & ((xx + yy + i) % 2 == 1), :3] = weld[1 % len(weld)]
            box[seam, 3] = 255
            tx, ty = _torch(st, m, bb, p, i)
            fr_ = random.Random(st.get("seed", 5) * 100 + i)
            for _ in range(st.get("sparks", 4)):
                _put(f, s, tx + fr_.randint(-2, 2), ty - fr_.randint(0, 2), weld[fr_.randrange(len(weld))])
            _put(f, s, tx, ty, weld[0])
    # drones on top: bodies, the welding drone's torch arm, motion trails
    for st, m, bb in parts:
        if st["how"] not in ("drone", "weld"):
            continue
        now = _drones_at(st, m, bb, i, ground)
        for n, (dx, dy) in enumerate(now):
            back = [_drones_at(st, m, bb, i - q, ground) for q in (0.5, 1.0, 1.5, 2.0)]
            _trail(f, s, M, [(b_[n][0], b_[n][1]) for b_ in back if len(b_) > n])
        for dx, dy in now:
            dx, dy = int(round(dx)), int(round(dy))
            if st["how"] == "weld" and i < st["at"][1]:
                tx, ty = _torch(st, m, bb, (i - st["at"][0]) / max(1, st["at"][1] - st["at"][0]), i)
                for y in range(dy + 1, ty):
                    _put(f, s, tx, y, M["mid"])
            _drone(f, s, M, dx, dy, i)
    if t.get("dust", True) is not False:
        _dust_puffs(f, s, parts, i, ground, t.get("dust") if isinstance(t.get("dust"), list) else DUST, end,
                    t.get("frames"))


# Natural construction (`assemble` plan with "vocabulary": "natural"): a timber-framed, daubed, roofed building raised
# on site from its ground diamond. Timeline keys and their defaults for a 30-frame strip; other lengths scale them.
SITE_TIMELINE = {"stakes": [0, 10], "footing": [2, 6], "posts": [5, 10], "timber": [7, 13], "infill": [10, 17],
                 "gable": [14, 18], "rafters": [15, 19], "roof": [19, 27], "ladder": [9, 27]}


def _site_timeline(t):
    n = t["siteFrames"]
    tl = {kk: [int(round(v * (n - 1) / 29)) for v in vv] for kk, vv in SITE_TIMELINE.items()}
    given = dict(t.get("timeline", {}))
    if "thatch" in given:
        given.setdefault("roof", given.pop("thatch"))
    tl.update(given)
    tl.setdefault("footing_gone", n - 1)
    tl.setdefault("frame_gone", n - 1)
    return tl


def _hash01(a, b, seed):
    v = (a * 73856093) ^ (b * 19349663) ^ (seed * 83492791)
    return (v % 1000003) / 1000003.0


def _ramp(f, f0, f1):
    """0 before f0, 1 at f1 and after."""
    if f1 <= f0:
        return 1.0 if f >= f0 else 0.0
    return float(min(1.0, max(0.0, (f - f0) / (f1 - f0))))


def _line(s, p0, p1, width=1):
    img = Image.new("L", (s.w, s.h), 0)
    ImageDraw.Draw(img).line([tuple(p0), tuple(p1)], fill=1, width=width)
    return np.asarray(img).astype(bool)


def _site_geometry(s, t):
    """Parts of the still (roof, loose lumber, wall timber, wall infill, gable), height above the near ground line,
    position up the roof slope (0 eave, 1 ridge), panel and fine noise, and site colours sampled from the still."""
    key = ("site", id(s), json.dumps(t, sort_keys=True))
    if key in _CACHE:
        return _CACHE[key]
    yy, xx = np.mgrid[0:s.h, 0:s.w]
    g = t["groundBase"]
    L = np.array([g["left"]["x"], g["left"]["y"]], float)
    F = np.array([g["front"]["x"], g["front"]["y"]], float)
    R = np.array([g["right"]["x"], g["right"]["y"]], float)
    B = L + R - F
    wallH = t["wallHeight"]
    groundY = np.where(xx <= F[0], L[1] + (xx - L[0]) * (F[1] - L[1]) / (F[0] - L[0]),
                       F[1] + (xx - F[0]) * (R[1] - F[1]) / (R[0] - F[0]))
    height = np.clip(groundY - yy, 0, None)
    still = np.round(s.still).astype(np.uint8)
    rgb = still[..., :3].astype(float)
    roof = s.regions[t["roof"]] & s.opaque
    lumber = s.regions[t["lumber"]] & s.opaque if t.get("lumber") else np.zeros_like(roof)
    walls = s.opaque & ~roof & ~lumber
    val = rgb.max(axis=2) / 255
    sat = (rgb.max(axis=2) - rgb.min(axis=2)) / np.maximum(rgb.max(axis=2), 1)
    timber = walls & ((val < t.get("timberValue", 0.55)) | ((sat > 0.5) & (val < 0.75)))
    infill = walls & ~timber
    e0, e1 = (np.array(p, float) for p in t["eave"])
    r0, r1 = (np.array(p, float) for p in t["ridge"])

    def dist(p0, p1):
        d = p1 - p0
        nrm = np.array([-d[1], d[0]]) / np.hypot(*d)
        return np.abs((xx - p0[0]) * nrm[0] + (yy - p0[1]) * nrm[1])

    de, dr = dist(e0, e1), dist(r0, r1)

    def sample(mask, q):
        """The q-quantile colour by brightness; the whole still's when the part is (nearly) empty, never invented."""
        px = rgb[mask] if mask.sum() > 4 else rgb[s.opaque]
        return np.asarray(px[np.argsort(px.mean(axis=1))[int(q * (len(px) - 1))]], np.float32)

    stone = s.opaque & (sat < 0.22) & (val > 0.35) & (val < 0.8)
    seed = t.get("seed", 7)
    geo = dict(L=L, F=F, R=R, B=B, up=np.array([0, -wallH], float), wallH=wallH, height=height, roof=roof,
               lumber=lumber, walls=walls, timber=timber, infill=infill, gable=walls & (height > wallH + 1),
               slope=de / np.maximum(de + dr, 1e-6), e0=e0, e1=e1, r0=r0, r1=r1,
               blk=_hash01(xx // 3, yy // 3, seed), fine=_hash01(xx, yy, seed + 1), xx=xx, yy=yy,
               cols=dict(timber=sample(timber, 0.25), timber_lit=sample(timber, 0.75), string=sample(infill, 0.6),
                         stone=sample(stone, 0.85), stone_dark=sample(stone, 0.15)))
    _CACHE[key] = geo
    return geo


def _site_built(G, T, f):
    """Pixels of the still standing at frame f: loose lumber from the start, wall timbers rising, infill course by
    course, the gable's timbers then its infill, the roof from the eave up to the ridge with a ragged course edge."""
    h, blk = G["height"], G["blk"]
    wallH, gable, timber, infill = G["wallH"], G["gable"], G["timber"], G["infill"]
    m = G["lumber"].copy()
    m |= timber & ~gable & (h <= _ramp(f, *T["timber"]) * (wallH + 1) + blk * 2 - 1)
    m |= infill & ~gable & (h <= _ramp(f, *T["infill"]) * (wallH + 2) + blk * 3 - 1.5)
    gh = h[gable].max() if gable.any() else wallH
    m |= gable & timber & (h <= wallH + _ramp(f, *T["gable"]) * (gh - wallH + 1))
    m |= gable & (h <= wallH + _ramp(f, T["gable"][0] + 1, T["gable"][1] + 2) * (gh - wallH + 2) - blk * 2)
    m |= G["roof"] & (G["slope"] <= _ramp(f, *T["roof"]) * 1.2 - 0.04 - G["fine"] * 0.06 - blk * 0.04)
    return m


def _site_items(s, G, T, t, f):
    """Temporary site elements at frame f as (mask, colour), drawn under built pixels: corner stakes and string on
    the ground diamond, a fieldstone footing laid near edges first, corner posts and wall plates, the ridge pole,
    rafters and laths, a ladder."""
    L, F, R, B, up, C = G["L"], G["F"], G["R"], G["B"], G["up"], G["cols"]
    xx, yy = G["xx"], G["yy"]
    items = []
    if T["stakes"][0] <= f < T["stakes"][1]:
        n = _ramp(f, T["stakes"][0], T["stakes"][0] + 2)
        for j, c in enumerate([L, F, R, B]):
            if n * 4 >= j + 1 or f >= T["stakes"][0] + 2:
                items.append((_line(s, c, c + [0, -3]), C["timber"]))
        if f >= T["stakes"][0] + 1:
            for a, b in [(L, F), (F, R), (R, B), (B, L)]:
                items.append((_line(s, a, b) & ~_line(s, a, a), C["string"]))
    p = _ramp(f, *T["footing"])
    if p > 0 and f < T["footing_gone"]:
        for j, (a, b) in enumerate([(L, F), (F, R), (R, B), (B, L)]):
            share = float(np.clip(4 * p - j, 0, 1))
            if share <= 0:
                continue
            end = a + (b - a) * share
            mk = _line(s, a, end, 2) | _line(s, a + [0, -1], end + [0, -1], 2) | _line(s, a + [0, -2], end + [0, -2], 1)
            items.append((mk, C["stone_dark"]))
            items.append((mk & ((xx // 2 + yy) % 3 != 0) & (yy % 2 == (xx // 2) % 2), C["stone"]))
    p = _ramp(f, *T["posts"])
    if p > 0 and f < T["frame_gone"]:
        for c in [B, L, R, F]:
            items.append((_line(s, c + [0, -1], c + up * p, 2 if (c == F).all() else 1), C["timber"]))
        if p >= 1:
            q = _ramp(f, T["posts"][1], T["posts"][1] + 2)
            for a, b in [(B + up, L + up), (B + up, R + up), (L + up, F + up), (F + up, R + up)]:
                items.append((_line(s, a, a + (b - a) * q), C["timber_lit"]))
    p = _ramp(f, *T["rafters"])
    if p > 0 and f < T["frame_gone"]:
        e0, e1, r0, r1 = G["e0"], G["e1"], G["r0"], G["r1"]
        items.append((_line(s, r0, r0 + (r1 - r0) * p, 2), C["timber_lit"]))
        n = t.get("rafters", 7)
        for j in range(n):
            if p * n >= j + 1:
                u = j / (n - 1)
                items.append((_line(s, e0 + (e1 - e0) * u, r0 + (r1 - r0) * u), C["timber"]))
        if p >= 1:
            for u in (0.3, 0.6):
                items.append((_line(s, e0 + (r0 - e0) * u, e1 + (r1 - e1) * u), C["timber_lit"]))
    if t.get("ladder") and T["ladder"][0] <= f < T["ladder"][1]:
        lb, lt = (np.array(p_, float) for p_ in t["ladder"])
        for off in (0, 3):
            items.append((_line(s, lb + [off, 0], lt + [off, 0]), C["timber_lit"]))
        for j in range(1, 6):
            a = lb + (lt - lb) * j / 6
            items.append((_line(s, a, a + [3, 0]), C["timber"]))
    return items


def fx_site(s, f, k, t, i):
    """Natural construction ending on the still, for a timber-framed, daubed, roofed building seen from above at an
    angle: stakes and string on the ground diamond (`groundBase` left, front, right corners), a fieldstone footing,
    corner posts and wall plates `wallHeight` px tall, the still's own wall timbers then its infill rising course by
    course, the gable, the ridge pole, rafters and laths, the roof (`roof` region) laid from the `eave` line up to
    the `ridge` line, a `ladder` that leaves before the end. The `lumber` region (a plank pile) stands from frame 0.
    Site elements take colours sampled from the still, so a frame adds no colour. Frames 0 to `siteFrames` - 1;
    the last of them is the still. Made by `pxw.py assemble` with a natural plan; put it last."""
    n = t["siteFrames"]
    if i >= n - 1:
        return
    G = _site_geometry(s, t)
    T = _site_timeline(t)
    src = f.copy()
    f[s.opaque] = 0
    f[~s.opaque] = s.still[~s.opaque]
    for mk, col in _site_items(s, G, T, t, i):
        f[mk, :3] = col
        f[mk, 3] = 255
    b = _site_built(G, T, i) & s.opaque
    f[b] = src[b]


def fx_arc(s, f, k, t, i):
    """Electric arcs: jagged 1 px bolts along each of `paths` ([[x0, y0, x1, y1], ...]), a new shape every frame
    (midpoint displacement, `jag` px), core colour then glow pixels beside it. k is the share of paths lit (0 off,
    1 all); `flicker` (default 0.25) drops a lit path at random per frame so it crackles."""
    if k <= 0:
        return
    zone = s.regions[t["region"]]
    core, glow = [np.asarray(c, dtype=np.float32) for c in t["colours"][:2]]
    rnd = random.Random(t.get("seed", 21) * 1000 + i)
    paths = t["paths"]
    lit = paths[:max(1, int(math.ceil(k * len(paths))))]
    for x0, y0, x1, y1 in lit:
        if rnd.random() < t.get("flicker", 0.25):
            continue
        pts = [(float(x0), float(y0)), (float(x1), float(y1))]
        jag = t.get("jag", 2.5)
        while max(abs(b[0] - a[0]) + abs(b[1] - a[1]) for a, b in zip(pts, pts[1:])) > 3:
            nxt = [pts[0]]
            for a, b in zip(pts, pts[1:]):
                dx, dy = b[0] - a[0], b[1] - a[1]
                ln = math.hypot(dx, dy) or 1.0
                o = rnd.uniform(-jag, jag) * min(1.0, ln / 8)
                nxt += [((a[0] + b[0]) / 2 - dy / ln * o, (a[1] + b[1]) / 2 + dx / ln * o), b]
            pts = nxt
        for a, b in zip(pts, pts[1:]):
            steps = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) + 1
            for q in range(steps + 1):
                x = int(round(a[0] + (b[0] - a[0]) * q / steps))
                y = int(round(a[1] + (b[1] - a[1]) * q / steps))
                if 0 <= x < s.w and 0 <= y < s.h and zone[y, x]:
                    f[y, x, :3] = core
                    f[y, x, 3] = 255
                    if rnd.random() < 0.3:
                        gx, gy = x + rnd.choice((-1, 1)), y + rnd.choice((-1, 0, 1))
                        if 0 <= gx < s.w and 0 <= gy < s.h and zone[gy, gx]:
                            f[gy, gx, :3] = glow
                            f[gy, gx, 3] = 255


def _along(path, k):
    """Point at k (0..1) along a polyline, by segment: k = j / (len - 1) is exactly point j."""
    u = min(1.0, max(0.0, k)) * (len(path) - 1)
    j = min(len(path) - 2, int(u))
    fr = u - j
    return path[j][0] + (path[j + 1][0] - path[j][0]) * fr, path[j][1] + (path[j + 1][1] - path[j][1]) * fr


def fx_drone(s, f, k, t, i):
    """A work drone (the assemble quadcopter) at k along `path` ([[x, y], ...] body positions, by segment), bobbing
    and leaving a motion trail; k < 0 hides it. With `torch` [x, y] and the frame in `torchFrames` it reaches a
    torch arm down to that point, which glows white-hot (point a sparks track's source there)."""
    if k < 0:
        return
    M = {kk: np.asarray(v, dtype=np.float32) for kk, v in dict(MACHINE, **t.get("machine", {})).items()}
    x, y = _along(t["path"], k)
    x, y = int(round(x)), int(round(y + math.sin(i * 1.9) * 0.8))
    curve = t.get("curve")
    if curve and i > 0 and curve[i - 1] >= 0 and curve[i - 1] != k:
        px, py = _along(t["path"], curve[i - 1])
        _trail(f, s, M, [(x + (px - x) * q, y + (py - y) * q) for q in (0.35, 0.7, 1.0)])
    torch = t.get("torch")
    if torch and i in t.get("torchFrames", []):
        for yy in range(y + 1, torch[1]):
            _put(f, s, torch[0], yy, M["mid"])
        _put(f, s, torch[0], torch[1], np.asarray(t.get("weld", WELD)[0], dtype=np.float32))
    _drone(f, s, M, x, y, i)


def fx_cart(s, f, k, t, i):
    """A ground cart rolling a crate along `y` (the wheel row) from x `from` to `to` as k goes 0 to 1 (k < 0 or
    > 1 hides it): `size` [w, h] crate in the accent colour with dark edges on a 2 px chassis with turning
    wheels."""
    if k < 0 or k > 1:
        return
    M = {kk: np.asarray(v, dtype=np.float32) for kk, v in dict(MACHINE, **t.get("machine", {})).items()}
    cw, ch = t.get("size", [8, 4])
    x0 = int(round(t["from"] + (t["to"] - t["from"]) * k))
    y = t["y"]
    for x in range(x0, x0 + cw + 2):
        _put(f, s, x, y - 1, M["mid"])
        _put(f, s, x, y, M["dark"] if (x + i) % 3 else M["light"])
    for yy in range(y - 1 - ch, y - 1):
        for x in range(x0 + 1, x0 + 1 + cw):
            edge = yy == y - 1 - ch or x in (x0 + 1, x0 + cw)
            _put(f, s, x, yy, M["dark"] if edge else M["accent"])


def fx_external(s, f, k, t, i):
    """Frames made elsewhere (PixelLab, a hand edit): copy frame i's pixels inside the region from an external
    sheet of the still's frame size, snapped to the palette. Everything outside the region stays the still.
    Alpha is hardened at 128 unless `soft: "keep"`, which takes the sheet's alpha as it is: smoke, steam or a
    painted soft rim over clear sky would otherwise turn into a hard-edged cutout."""
    key = ("ext", resolve(t["sheet"], s.root, s.briefDir).as_posix())
    if key not in _CACHE:
        _CACHE[key] = load_rgba(Path(key[1]))
    sheet = _CACHE[key]
    n = sheet.shape[1] // s.w
    j = t.get("map", list(range(n)))[i] if t.get("map") else i
    if j is None or j >= n:
        return
    ext = sheet[:, j * s.w:(j + 1) * s.w]
    m = s.regions[t["region"]]
    if t.get("soft") == "keep":
        f[m, 3] = ext[m, 3]
        vis = m & (ext[..., 3] > 0)
    else:
        f[m, 3] = np.where(ext[m, 3] > 127, 255, 0)
        vis = m & (ext[..., 3] > 127)
    f[vis, :3] = s.palette_for(t["region"]).snap(ext[vis, :3][None])[0]


# ---- model_rotate: a painted part turned by a 3D render's ID and position passes ----
# A render folder holds sprite.json (id_colours, pos_extent, optional rings.<part>.arms and a loop entry with
# rotate_axis) and, per frame (in the folder or its frames/ subfolder): id_NNN.png (flat part colours),
# pos_NNN.tif (16-bit object-space coordinates of the visible surface, (L / (2 * extent)) + 0.5) and optionally
# beauty_NNN.png (its alpha is the silhouette).

def _render_files(folder):
    folder = Path(folder)
    sub = folder / "frames" if (folder / "frames").is_dir() else folder
    files = {k: sorted(sub.glob(f"{k}_*.{ext}")) for k, ext in (("id", "png"), ("pos", "tif"), ("beauty", "png"))}
    meta = json.loads((folder / "sprite.json").read_text(encoding="utf-8"))
    if not files["id"]:
        raise ValueError(f"no id_*.png frames in {sub}")
    return meta, files


def _id_mask(path, meta, part, colour=None):
    """Pixels of `part` in an ID frame: `colour` (sRGB 0-255) if given, else sprite.json id_colours (linear, as
    Blender writes an emission colour), converted to sRGB, within 0.12."""
    idimg = np.asarray(Image.open(path).convert("RGB")).astype(float) / 255
    if colour is not None:
        srgb = np.asarray(colour, dtype=float) / 255
    else:
        c = meta.get("id_colours", {}).get(part)
        if c is None:
            raise ValueError(f"sprite.json has no id_colours.{part}")
        srgb = np.array([x * 12.92 if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055 for x in c])
    return np.abs(idimg - srgb).max(-1) < 0.12


def _load_pos(path, extent):
    try:
        import tifffile
    except ImportError:
        raise ValueError("model_rotate reads 16-bit pos_*.tif with tifffile (Pillow cuts 16-bit RGBA to 8 bit): "
                         "python -m pip install tifffile")
    a = tifffile.imread(str(path)).astype(float) / 65535.0
    return (a[..., :3] - 0.5) * 2 * extent


def _shift(m, dy, dx, fill):
    out = np.full_like(m, fill)
    h, w = m.shape[:2]
    out[max(0, dy):h + min(0, dy), max(0, dx):w + min(0, dx)] = m[max(0, -dy):h + min(0, -dy), max(0, -dx):w + min(0, -dx)]
    return out


def _dilate(m, n, square=False):
    """n steps of a 3x3 cross (or square) binary dilation; outside the image counts as empty."""
    offs = [(0, 1), (0, -1), (1, 0), (-1, 0)] + ([(1, 1), (1, -1), (-1, 1), (-1, -1)] if square else [])
    for _ in range(n):
        g = m.copy()
        for dy, dx in offs:
            g |= _shift(m, dy, dx, False)
        m = g
    return m


def _erode(m, n):
    return ~_dilate(~np.pad(m, n), n)[n:-n, n:-n] if n else m


def _blur(a, sigma):
    """Separable Gaussian (radius 4 sigma, mirrored edges) of a 2D float array."""
    r = max(1, int(4 * sigma + 0.5))
    x = np.arange(-r, r + 1)
    k = np.exp(-0.5 * (x / sigma) ** 2)
    k /= k.sum()
    p = np.pad(a, r, mode="symmetric")
    p = sum(k[j] * p[:, j:j + a.shape[1]] for j in range(2 * r + 1))
    return sum(k[j] * p[j:j + a.shape[0]] for j in range(2 * r + 1))


def _max3(img):
    """3x3 maximum per channel (edges repeated)."""
    p = np.pad(img, ((1, 1), (1, 1), (0, 0)), mode="edge")
    h, w = img.shape[:2]
    return np.max([p[dy:dy + h, dx:dx + w] for dy in range(3) for dx in range(3)], axis=0)


class _Near:
    """Nearest point within `tol` (exact), on a hash grid of `tol` cells: numpy only, no KD-tree needed."""

    def __init__(self, P, tol):
        self.P, self.tol = P, tol
        k = np.floor(P / tol).astype(np.int64)
        self.lo = k.min(0) - 1
        k -= self.lo
        self.dims = k.max(0) + 2
        lin = (k[:, 0] * self.dims[1] + k[:, 1]) * self.dims[2] + k[:, 2]
        self.order = np.argsort(lin, kind="stable")
        self.lin = lin[self.order]
        self.maxc = int(np.unique(lin, return_counts=True)[1].max()) if len(lin) else 0

    def query(self, Q):
        best = np.full(len(Q), np.inf)
        bi = np.zeros(len(Q), dtype=np.int64)
        kq = np.floor(Q / self.tol).astype(np.int64) - self.lo
        for off in [(a, b, c) for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1)]:
            kk = kq + np.asarray(off)
            valid = ((kk >= 0) & (kk < self.dims)).all(1)
            lin = (kk[:, 0] * self.dims[1] + kk[:, 1]) * self.dims[2] + kk[:, 2]
            start = np.searchsorted(self.lin, lin, "left")
            end = np.searchsorted(self.lin, lin, "right")
            for j in range(self.maxc):
                idx = start + j
                ok = valid & (idx < end)
                if not ok.any():
                    break
                pi = self.order[idx[ok]]
                d = np.sqrt(((self.P[pi] - Q[ok]) ** 2).sum(1))
                rows = np.nonzero(ok)[0]
                better = d < best[rows]
                best[rows[better]] = d[better]
                bi[rows[better]] = pi[better]
        best[best > self.tol] = np.inf
        return best, bi


def _rotate_about(L, ax, ang):
    u, v = [j for j in range(3) if j != ax]
    c, s_ = np.cos(ang), np.sin(ang)
    out = L.copy()
    out[..., u] = L[..., u] * c - L[..., v] * s_
    out[..., v] = L[..., u] * s_ + L[..., v] * c
    return out


def _fold_colour(Lq, ax, nSym, near, cols, offset):
    """Colour for body points Lq: fold each into the canonical sector [offset, offset + 2pi/n) of the part's n-fold
    symmetry and look it up among frame 0's visible part pixels; a point hidden there is tried one, two, ...
    sectors further on. Every frame then shows the same symmetric part, so the loop closes after one interval."""
    per = 2 * np.pi / nSym
    u, v = [j for j in range(3) if j != ax]
    k0 = np.floor((np.arctan2(Lq[:, v], Lq[:, u]) - offset) / per)
    canon = _rotate_about(Lq, ax, -k0 * per)
    res = np.full((len(Lq), 3), np.nan)
    todo = np.arange(len(Lq))
    for step in [0] + [st for j in range(1, nSym) for st in (j, -j)][:nSym - 1]:
        if not len(todo):
            break
        d, idx = near.query(_rotate_about(canon[todo], ax, step * per))
        hit = np.isfinite(d)
        res[todo[hit]] = cols[idx[hit]]
        todo = todo[~hit]
    return res


def _downscale(rgb, alpha, w, h):
    """Premultiplied Lanczos to (w, h): soft edges keep their own colour instead of picking up black."""
    pre = np.dstack([rgb * alpha[..., None], alpha])
    small = np.stack([np.asarray(Image.fromarray(pre[..., c].astype(np.float32), "F").resize((w, h), Image.LANCZOS))
                      for c in range(4)], -1)
    small = np.clip(small, 0, 1)
    al = small[..., 3]
    col = np.where(al[..., None] > 1e-4, small[..., :3] / np.maximum(al[..., None], 1e-4), 0)
    res = np.dstack([np.clip(col, 0, 1), al])
    res[al < 0.03] = 0
    return np.round(res * 255).astype(np.float32)


def _load_rgb01(path, size):
    im = Image.open(path)
    alpha = np.asarray(im.convert("RGBA").resize(size, Image.LANCZOS))[..., 3].astype(float) / 255 \
        if im.mode in ("RGBA", "LA", "PA") else None
    im = im.convert("RGB")
    if im.size != size:
        im = im.resize(size, Image.LANCZOS)
    return np.asarray(im).astype(float) / 255, alpha


def _model_region(s, r):
    """A region from the render's ID pass: every still pixel the part covers in any frame, grown by `grow` still
    pixels (4) so the Lanczos footprint of the moving edge stays inside."""
    meta, files = _render_files(resolve(r["frames"], s.root, s.briefDir))
    union = None
    for p in files["id"]:
        m = _id_mask(p, meta, r["part"], r.get("idColour"))
        union = m if union is None else union | m
    small = np.asarray(Image.fromarray(union.astype(np.uint8) * 255).resize((s.w, s.h), Image.BOX)) > 0
    return _dilate(small, r.get("grow", 4), square=True)


def _model_frames(s, t):
    """All frames of a model_rotate track at still size (cached). Hi-res frames go to <outdir>/<id>-<part>-hires/."""
    key = ("model", id(s), json.dumps(t, sort_keys=True))
    if key in _CACHE:
        return _CACHE[key]
    meta, files = _render_files(resolve(t["frames"], s.root, s.briefDir))
    part = t["part"]
    if len(files["pos"]) != len(files["id"]):
        raise ValueError(f"model_rotate: {len(files['id'])} id frames but {len(files['pos'])} pos frames")
    size = Image.open(files["id"][0]).size
    axis = t.get("axis") or next((e["rotate_axis"] for e in meta.get("loop", []) if "rotate_axis" in e), None)
    if axis not in ("X", "Y", "Z"):
        raise ValueError("model_rotate needs `axis` (X, Y or Z) or a loop entry with rotate_axis in sprite.json")
    ax = "XYZ".index(axis)
    nSym = int(t.get("symmetry") or meta.get("rings", {}).get(part, {}).get("arms") or 1)
    tol = float(t.get("tol", 0.03))
    ext = float(t.get("posExtent", meta.get("pos_extent", 1.0)))
    offset = math.radians(t["sectorOffset"]) if "sectorOffset" in t else math.pi / nSym
    f0, a0 = _load_rgb01(resolve(t["painted"], s.root, s.briefDir), size)
    plate, _ = _load_rgb01(resolve(t["plate"], s.root, s.briefDir), size)
    if files["beauty"]:
        alphas = [np.asarray(Image.open(p).convert("RGBA"))[..., 3].astype(float) / 255 for p in files["beauty"]]
    else:
        alphas = [a0 if a0 is not None else np.ones(size[::-1])] * len(files["id"])
    masks = [_id_mask(p, meta, part, t.get("idColour")) for p in files["id"]]
    m0 = _erode(masks[0], 1)
    P0 = _load_pos(files["pos"][0], ext)
    near = _Near(P0[m0], tol)
    cols0 = f0[m0]
    hires = None
    if t.get("hires", True) and getattr(s, "outdir", None):
        hires = Path(s.outdir) / f"{s.id}-{part}-hires"
        hires.mkdir(parents=True, exist_ok=True)
    ref = _downscale(f0, alphas[0], s.w, s.h)
    frames, unmatched = [], []
    for i, mi in enumerate(masks):
        q = np.nonzero(mi)
        col = _fold_colour(_load_pos(files["pos"][i], ext)[q], ax, nSym, near, cols0, offset)
        miss = np.isnan(col[:, 0])
        unmatched.append(int(miss.sum()))
        body = np.zeros_like(f0)
        have = np.zeros(mi.shape, bool)
        body[q[0][~miss], q[1][~miss]] = col[~miss]
        have[q[0][~miss], q[1][~miss]] = True
        # a point hidden in every sector of frame 0 takes the nearest painted part colour, never the plate (L-043)
        want = mi & ~have
        while want.any() and have.any():
            grew = False
            for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                src = _shift(have, dy, dx, False) & want
                if src.any():
                    body[src] = _shift(body, dy, dx, 0.0)[src]
                    have |= src
                    want &= ~src
                    grew = True
            if not grew:
                break
        touched = _dilate(masks[0] | mi, 2)
        frame = f0.copy()
        frame[touched] = plate[touched]
        soft = np.where(have, 1.0, np.clip(_blur(have.astype(float), 0.7), 0, 1))[..., None]
        frame = frame * (1 - soft) + np.where(have[..., None], body, _max3(body)) * soft
        al = np.where(_dilate(touched, 3), alphas[i], alphas[0])
        if hires is not None:
            Image.fromarray(np.round(np.dstack([np.clip(frame, 0, 1), al]) * 255).astype(np.uint8), "RGBA") \
                .save(hires / f"f{i:02d}.png")
        frames.append(_downscale(frame, al, s.w, s.h))
    _CACHE[key] = (frames, ref)
    s.__dict__.setdefault("modelStats", {})[part] = {"symmetry": nSym, "axis": axis, "tol": tol,
                                                      "unmatched_px": unmatched}
    return _CACHE[key]


def fx_model_rotate(s, f, k, t, i):
    """A painted part turned by a 3D render: per frame, each part pixel takes the colour its body point (from the pos
    pass) has in the painted frame 0, folded into one sector of the part's `symmetry`; gaps show the `plate`
    (painted without the part). Made at the render's size, downscaled premultiplied, and written only where it
    differs from the downscaled painted frame 0, inside the region, snapped to the still's palette."""
    frames, ref = _model_frames(s, t)
    j = t["map"][i] if t.get("map") else i % len(frames)
    if j is None:
        return
    small = frames[j]
    m = s.regions[t["region"]] & (small != ref).any(-1)
    f[m, 3] = small[m, 3]
    vis = m & (small[..., 3] > 0)
    f[vis, :3] = s.palette_for(t["region"]).snap(small[vis, :3][None])[0]


EFFECTS = {"pulse": fx_pulse, "spill": fx_spill, "darken": fx_darken, "glint": fx_glint, "sparks": fx_sparks,
           "dust": fx_dust, "rotate": fx_rotate, "shift": fx_shift, "scroll": fx_scroll, "fill": fx_fill,
           "puffs": fx_puffs, "buildup": fx_buildup, "assemble": fx_assemble, "external": fx_external,
           "arc": fx_arc, "drone": fx_drone, "cart": fx_cart, "bend": fx_bend, "brighten": fx_brighten, "bands": fx_bands,
           "model_rotate": fx_model_rotate, "site": fx_site}


def animations(brief):
    """{name: animation}. A brief lists them under "animations"; older briefs use top-level "use" and "place"."""
    if "animations" in brief:
        return brief["animations"]
    return {k: brief[k] for k in ("use", "place") if isinstance(brief.get(k), dict)}


def rest_index(name, anim):
    rest = anim.get("rest", "last" if name == "place" else "first")
    return {"first": 0, "last": anim["frames"] - 1, "none": None}[rest]


def build_frames(s, anim):
    frames = []
    for i in range(anim["frames"]):
        f = s.still.copy()
        for t in anim["tracks"]:
            curve = t.get("curve")
            k = curve[i] if curve else 1.0
            EFFECTS[t["effect"]](s, f, k, t, i)
        frames.append(np.clip(np.round(f), 0, 255).astype(np.uint8))
    return frames


# ---- gates ----

def gates(s, anim, frames, restIndex):
    still = np.round(s.still).astype(np.uint8)
    union = np.zeros((s.h, s.w), dtype=bool)
    alphaOk = np.zeros((s.h, s.w), dtype=bool)
    for t in anim["tracks"]:
        for key in ("region", "part"):
            if key in t and not (key == "part" and t["effect"] == "model_rotate"):  # a model part, not a region
                union |= s.regions[t[key]]
                if s.brief["regions"][t[key]].get("alpha"):
                    alphaOk |= s.regions[t[key]]
    allowed = {tuple(c) for c in still[..., :3][s.opaque].reshape(-1, 3)}
    allowed |= {tuple(int(v) for v in c) for c in s.extras}
    for t in anim["tracks"]:
        for key in ("colours", "weld"):
            for c in t.get(key, []):
                allowed.add(tuple(int(v) for v in c))
        for key in ("ghost", "colour"):
            if key in t:
                allowed.add(tuple(int(v) for v in t[key]))
        if t["effect"] in ("assemble", "drone", "cart"):
            for c in list(dict(MACHINE, **t.get("machine", {})).values()) + t.get("weld", WELD):
                allowed.add(tuple(int(v) for v in c))
        if t["effect"] == "assemble" and t.get("dust", True) is not False:
            for c in t.get("dust") if isinstance(t.get("dust"), list) else DUST:
                allowed.add(tuple(int(v) for v in c))
    res = {"rest_frame": restIndex,
           "rest_frame_identical": None if restIndex is None else bool((frames[restIndex] == still).all())}
    outside = alphaBad = 0
    newCols = set()
    changedShare, lumDelta = [], []
    focal = s.regions[anim.get("focal") or anim["tracks"][0]["region"]]
    opaqueCount = max(1, int(s.opaque.sum()))
    for f in frames:
        diff = (f != still).any(-1)
        outside += int((diff & ~union).sum())
        alphaBad += int(((f[..., 3] != still[..., 3]) & ~alphaOk).sum())
        vis = f[..., 3] > 0
        newCols |= {tuple(c) for c in f[..., :3][vis].reshape(-1, 3)} - allowed
        changedShare.append(round(float(diff.sum()) / opaqueCount, 4))
        lumDelta.append(round(float(np.abs(f[..., :3][focal].astype(float).mean(-1)
                                           - still[..., :3][focal].astype(float).mean(-1)).mean()), 1) if focal.any() else 0.0)
    th = {"share": 0.08, "luma": 40}
    th.update(s.brief.get("noticeable", {}))
    th.update(anim.get("noticeable", {}))
    res.update(changed_outside_mask=outside, alpha_changed_outside_alpha_regions=alphaBad, new_colours=len(newCols),
               changed_share_per_frame=changedShare, focal_mean_abs_luma_delta=lumDelta, noticeable_thresholds=th,
               noticeable=bool(max(changedShare) >= th["share"] or max(lumDelta) >= th["luma"]))
    if restIndex is None and len(frames) > 2:
        # a loop has no rest frame; its seam (last to first) must be no bigger a jump than the largest step inside
        steps = [int((frames[j] != frames[j + 1]).any(-1).sum()) for j in range(len(frames) - 1)]
        res["loop_seam_changed"] = int((frames[-1] != frames[0]).any(-1).sum())
        res["loop_seam_ok"] = res["loop_seam_changed"] <= max(steps)
    res["pass"] = bool(res["rest_frame_identical"] is not False and outside == 0 and alphaBad == 0 and not newCols
                       and res["noticeable"] and res.get("loop_seam_ok", True))
    return res


# ---- output ----

def contact_sheet(frames, per=5, z=3):
    fh, fw = frames[0].shape[:2]
    rows = (len(frames) + per - 1) // per
    c = Image.new("RGBA", (per * (fw * z + 6) + 6, rows * (fh * z + 6) + 6), (34, 34, 42, 255))
    for i, f in enumerate(frames):
        im = Image.fromarray(f, "RGBA").resize((fw * z, fh * z), Image.NEAREST)
        c.alpha_composite(im, (6 + (i % per) * (fw * z + 6), 6 + (i // per) * (fh * z + 6)))
    return c


def write_outputs(s, frames, outdir, name, restIndex, fps):
    (outdir / name).mkdir(parents=True, exist_ok=True)
    paths = []
    for i, f in enumerate(frames):
        p = outdir / name / f"f{i:02d}.png"
        Image.fromarray(f, "RGBA").save(p)
        paths.append(p)
    sheet = Image.new("RGBA", (s.w * len(frames), s.h))
    for i, f in enumerate(frames):
        sheet.paste(Image.fromarray(f, "RGBA"), (i * s.w, 0))
    sheetPath = outdir / f"{name}.png"
    sheet.save(sheetPath)
    contact_sheet(frames).save(outdir / f"{name}.contact.png")
    # 4x preview on a dark ground beside the still, holding the rest frame for 0.75 s between plays. Animated
    # PNG, not GIF: GIF's 256-colour limit bands many-colour stills and would misreport the animation.
    z = 4
    stillImg = Image.fromarray(np.round(s.still).astype(np.uint8), "RGBA").resize((s.w * z, s.h * z), Image.NEAREST)
    seq = []
    for f in frames:
        canvas = Image.new("RGBA", (s.w * z * 2 + 24, s.h * z + 16), (34, 34, 42, 255))
        canvas.alpha_composite(stillImg, (8, 8))
        canvas.alpha_composite(Image.fromarray(f, "RGBA").resize((s.w * z, s.h * z), Image.NEAREST), (s.w * z + 16, 8))
        seq.append(canvas.convert("RGB"))
    if restIndex is not None:
        seq += [seq[restIndex]] * 9
    previewPath = outdir / f"{name}.preview.png"
    seq[0].save(previewPath, save_all=True, append_images=seq[1:], duration=round(1000 / fps), loop=0)
    return paths, sheetPath, previewPath


def find_aw():
    env = os.environ.get("PIXELWRIGHT_AW") or os.environ.get("SPRITEWRIGHT_AW")
    if env and Path(env).is_file():
        return Path(env)
    found = []
    for base in (os.environ.get("CLAUDE_CONFIG_DIR"), Path.home() / ".claude"):
        home = Path(base) / "plugins" if base else None
        if home and home.is_dir():
            found = sorted(home.glob("**/artwright/scripts/aw.py"), key=lambda p: p.stat().st_mtime)
            if found:
                break
    return found[-1] if found else None


def aw_frames(paths):
    aw = find_aw()
    if not aw:
        return {"skipped": "artwright's aw.py not found (set PIXELWRIGHT_AW)"}
    r = subprocess.run([sys.executable, str(aw), "pixel", "--frames", *map(str, paths)], capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except ValueError:
        return {"raw": (r.stdout + r.stderr).strip()[-2000:]}


# ---- commands ----

def cmd_frames(a):
    need_deps()
    briefPath = Path(a.brief)
    brief = json.loads(briefPath.read_text(encoding="utf-8"))
    try:
        s = Sprite(brief, a.root, briefPath.parent)
    except (OSError, KeyError, ValueError) as e:
        fail(f"brief or still unreadable: {e}")
    outdir = Path(a.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    s.outdir = outdir
    report = {"id": s.id, "version": VERSION}
    for name, anim in animations(brief).items():
        if a.only and name != a.only:
            continue
        unknown = [t["effect"] for t in anim["tracks"] if t["effect"] not in EFFECTS]
        if unknown:
            fail(f"{name}: unknown effect(s) {unknown}; known: {sorted(EFFECTS)}")
        try:
            frames = build_frames(s, anim)
        except (OSError, KeyError, ValueError) as e:
            fail(f"{name}: {e}")
        sheetName = f"{s.id}-{name}-{len(frames)}f"
        restIndex = rest_index(name, anim)
        paths, sheetPath, previewPath = write_outputs(s, frames, outdir, sheetName, restIndex, anim.get("fps", 12))
        g = gates(s, anim, frames, restIndex)
        g.update(frames=len(frames), sheet=sheetPath.as_posix(), preview=previewPath.as_posix(),
                 aw_pixel_frames=aw_frames(paths) if not a.no_aw else {"skipped": "--no-aw"})
        if getattr(s, "modelStats", None):
            g["model"] = s.modelStats
        report[name] = g
    (outdir / f"{s.id}.gates.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    names = [k for k in report if isinstance(report[k], dict)]
    summary = {k: {kk: report[k][kk] for kk in ("pass", "frames", "rest_frame_identical", "changed_outside_mask",
                                               "new_colours", "noticeable", "sheet")} for k in names}
    ok = all(report[k]["pass"] for k in names)
    out(dict(ok=ok, id=s.id, gates=(outdir / f"{s.id}.gates.json").as_posix(), animations=summary), 0 if ok else 1)


def cmd_grid(a):
    need_deps()
    im = Image.open(a.image).convert("RGBA")
    w, h = im.size
    z, step, pad = a.zoom, a.step, 24
    bg = Image.new("RGBA", (w * z + pad, h * z + pad), (30, 30, 36, 255))
    bg.alpha_composite(im.resize((w * z, h * z), Image.NEAREST), (pad, pad))
    d = ImageDraw.Draw(bg)
    for x in range(0, w + 1, step):
        major = x % (step * 2) == 0
        d.line([(pad + x * z, pad), (pad + x * z, pad + h * z)], fill=(255, 0, 255, 140 if major else 60))
        if major:
            d.text((pad + x * z + 2, 4), str(x), fill=(255, 255, 255, 255))
    for y in range(0, h + 1, step):
        major = y % (step * 2) == 0
        d.line([(pad, pad + y * z), (pad + w * z, pad + y * z)], fill=(255, 0, 255, 140 if major else 60))
        if major:
            d.text((2, pad + y * z + 2), str(y), fill=(255, 255, 255, 255))
    bg.save(a.out)
    out(dict(ok=True, out=a.out, size=[w, h], zoom=z))


def cmd_mask(a):
    need_deps()
    briefPath = Path(a.brief)
    s = Sprite(json.loads(briefPath.read_text(encoding="utf-8")), a.root, briefPath.parent)
    z = a.zoom
    base = Image.fromarray(np.round(s.still).astype(np.uint8), "RGBA").resize((s.w * z, s.h * z), Image.NEAREST)
    canvas = Image.new("RGBA", base.size, (30, 30, 36, 255))
    canvas.alpha_composite(base)
    hues = [(255, 60, 60), (60, 200, 255), (255, 210, 40), (120, 255, 120), (230, 90, 255), (255, 140, 40)]
    counts = {}
    d = ImageDraw.Draw(canvas)
    for n, (name, m) in enumerate(s.regions.items()):
        counts[name] = int(m.sum())
        tint = Image.new("RGBA", (s.w, s.h), hues[n % len(hues)] + (0,))
        tint.putalpha(Image.fromarray((m * 110).astype(np.uint8), "L"))
        canvas.alpha_composite(tint.resize(base.size, Image.NEAREST))
        ys, xs = np.nonzero(m)
        if len(xs):
            d.text((int(xs.min()) * z + 2, int(ys.min()) * z + 2), name, fill=hues[n % len(hues)] + (255,))
    canvas.save(a.out)
    empty = [k for k, v in counts.items() if v == 0]
    out(dict(ok=not empty, out=a.out, pixels_per_region=counts, empty_regions=empty), 0 if not empty else 1)


def cmd_buildup(a):
    brief = json.loads(Path(a.brief).read_text(encoding="utf-8"))
    anims = brief.get("animations", brief)
    anim = anims[a.anim]
    n, old = a.frames, anim["frames"]
    for t in anim["tracks"]:
        if "curve" in t:
            t["curve"] = [t["curve"][0]] * n + t["curve"]
        if "bornFrames" in t:
            t["bornFrames"] = [x + n for x in t["bornFrames"]]
    weld = [[255, 250, 220], [255, 214, 110], [255, 150, 40]]
    ghost = [90, 190, 225]
    brief["regions"]["build"] = {"rects": "all", "alpha": True}
    reveal = [round(0.04 + 0.92 * i / (n - 1), 3) for i in range(n)]
    anim["tracks"].append({"effect": "buildup", "region": "build", "weld": weld, "ghost": ghost, "sparks": 7,
                           "jitter": 2, "seed": 9, "curve": reveal + [1] * old})
    anim["frames"] = old + n
    anim["rest"] = "last"
    Path(a.out).write_text(json.dumps(brief, indent=2), encoding="utf-8")
    out(dict(ok=True, out=a.out, anim=a.anim, frames=anim["frames"], buildup_frames=n))


def cmd_assemble(a):
    """Prefix an animation with realistic construction frames from a plan: {"frames": N, "regions": {...},
    "steps": [{"part", "how", "at": [start, end], ...}], "machine": {...}, "dropTracks": [index, ...]}
    (dropTracks removes the animation's own tracks whose motion the assembly replaces, e.g. an arm parking). Step frames count from 0, the first
    construction frame. Reports pixels no step covers (they would stand there from frame 0)."""
    need_deps()
    briefPath = Path(a.brief)
    brief = json.loads(briefPath.read_text(encoding="utf-8"))
    plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
    if plan.get("vocabulary") == "natural":
        return _assemble_natural(a, brief, briefPath, plan)
    anims = brief.get("animations", brief)
    anim = anims[a.anim]
    n, old = plan["frames"], anim["frames"]
    anim["tracks"] = [t for j, t in enumerate(anim["tracks"]) if j not in plan.get("dropTracks", [])]
    dustCol = None
    for t in anim["tracks"]:
        if "curve" in t:
            if t["effect"] == "dust":
                # the settling haze builds up while the machines work instead of standing there from frame 0
                # (held at full strength it was swept in by the deck weld as a hard band)
                c0 = t["curve"][0]
                t["curve"] = [round(c0 * _ease((j + 1) / n) ** 1.5, 3) for j in range(n)] + t["curve"]
                t["lumpy"] = True
                dustCol = t.get("colour")
            else:
                t["curve"] = [t["curve"][0]] * n + t["curve"]
        if "bornFrames" in t:
            t["bornFrames"] = [x + n for x in t["bornFrames"]]
    brief["regions"].update(plan.get("regions", {}))
    brief["regions"]["build"] = {"rects": "all", "alpha": True}
    track = {"effect": "assemble", "region": "build", "steps": plan["steps"], "frames": old + n}
    if dustCol:
        track["dust"] = [dustCol, [min(255, int(v * 1.18)) for v in dustCol]]
    for key in ("machine", "weld", "dust"):
        if key in plan:
            track[key] = plan[key]
    anim["tracks"].append(track)
    anim["frames"] = old + n
    anim["rest"] = "last"
    try:
        s = Sprite(brief, a.root, briefPath.parent)
    except (OSError, KeyError, ValueError) as e:
        fail(f"brief, plan or still unreadable: {e}")
    late = [st["part"] for st in plan["steps"] if st["at"][1] > n]
    parts, union = _assemble_parts(s, track)
    empty = [st["part"] for st, m, bb in parts if not m.any()]
    loose = int((s.opaque & ~union).sum())
    Path(a.out).write_text(json.dumps(brief, indent=2), encoding="utf-8")
    ok = not empty and not late and (loose == 0 or plan.get("allowUncovered"))
    out(dict(ok=bool(ok), out=a.out, anim=a.anim, frames=anim["frames"], assemble_frames=n, uncovered_pixels=loose,
             empty_parts=empty, steps_ending_after_assembly=late), 0 if ok else 1)


SITE_KEYS = ("roof", "lumber", "groundBase", "wallHeight", "timberValue", "eave", "ridge", "ladder", "rafters",
             "timeline", "seed")


def _assemble_natural(a, brief, briefPath, plan):
    """A natural plan: {"vocabulary": "natural", "frames": N, "regions": {roof, lumber}, "roof": name, "lumber": name,
    "groundBase", "wallHeight", "eave", "ridge", "ladder", "rafters", "timeline", "timberValue", "seed", "fps"}.
    Prefixes the animation (created when the brief has none by that name) with a `site` track."""
    for key in ("roof", "groundBase", "wallHeight", "eave", "ridge"):
        if key not in plan:
            fail(f"natural plan needs '{key}'")
    if "animations" not in brief and not any(isinstance(brief.get(kk), dict) for kk in ("use", "place")):
        brief["animations"] = {}
    anims = brief.get("animations", brief)
    anim = anims.setdefault(a.anim, {"frames": 0, "tracks": [], "fps": plan.get("fps", 12)})
    n, old = plan["frames"], anim["frames"]
    for t in anim["tracks"]:
        if "curve" in t:
            t["curve"] = [t["curve"][0]] * n + t["curve"]
        if "bornFrames" in t:
            t["bornFrames"] = [x + n for x in t["bornFrames"]]
    brief["regions"].update(plan.get("regions", {}))
    brief["regions"]["build"] = {"rects": "all", "alpha": True}
    track = {"effect": "site", "region": "build", "siteFrames": n, "frames": old + n}
    track.update({kk: plan[kk] for kk in SITE_KEYS if kk in plan})
    anim["tracks"].append(track)
    anim["frames"] = old + n
    anim["rest"] = "last"
    anim.setdefault("focal", "build")
    try:
        s = Sprite(brief, a.root, briefPath.parent)
    except (OSError, KeyError, ValueError) as e:
        fail(f"brief, plan or still unreadable: {e}")
    G = _site_geometry(s, track)
    T = _site_timeline(track)
    late = sorted(kk for kk, v in T.items() if (v if isinstance(v, int) else v[1]) > n - 1)
    parts = {kk: int(G[kk].sum()) for kk in ("roof", "lumber", "timber", "infill", "gable")}
    frames = build_frames(s, {"frames": n, "tracks": [track]})
    idle = [j for j in range(n - 1) if (frames[j] == frames[j + 1]).all()]
    Path(a.out).write_text(json.dumps(brief, indent=2), encoding="utf-8")
    ok = parts["roof"] > 0 and parts["timber"] + parts["infill"] > 0 and not late
    out(dict(ok=bool(ok), out=a.out, anim=a.anim, frames=anim["frames"], assemble_frames=n, vocabulary="natural",
             parts=parts, idle_frames=idle, timeline_ends_after_assembly=late,
             colours={kk: [int(v) for v in c] for kk, c in G["cols"].items()}), 0 if ok else 1)


def cmd_contact(a):
    need_deps()
    sheet = np.array(Image.open(a.sheet).convert("RGBA"))
    fw = sheet.shape[1] // a.frames
    frames = [sheet[:, i * fw:(i + 1) * fw] for i in range(a.frames)]
    contact_sheet(frames, a.per, a.zoom).save(a.out)
    out(dict(ok=True, out=a.out, frames=a.frames, frame_size=[fw, sheet.shape[0]]))


def cmd_pack(a):
    need_deps()
    ims = [Image.open(p).convert("RGBA") for p in a.frames]
    sizes = {im.size for im in ims}
    if len(sizes) != 1:
        fail(f"frames differ in size: {sorted(sizes)}")
    w, h = ims[0].size
    sheet = Image.new("RGBA", (w * len(ims), h))
    for i, im in enumerate(ims):
        sheet.paste(im, (i * w, 0))
    sheet.save(a.out)
    out(dict(ok=True, out=a.out, frames=len(ims), frame_size=[w, h]))


def cmd_doctor(a):
    aw = find_aw()
    out(dict(ok=MISSING is None, version=VERSION, python=sys.version.split()[0],
             numpy=None if MISSING else np.__version__, pillow=None if MISSING else Image.__version__,
             missing=MISSING, aw=aw.as_posix() if aw else None, effects=sorted(EFFECTS)), 0 if MISSING is None else 1)


# ---- make: real pixel art from a render ----

# PICO-8's 16 colours (CC0). Any other palette comes from a file or from reference sprites; nothing is fetched.
PALETTES = {"pico-8": ["000000", "1d2b53", "7e2553", "008751", "ab5236", "5f574f", "c2c3c7", "fff1e8",
                       "ff004d", "ffa300", "ffec27", "00e436", "29adff", "83769c", "ff77a8", "ffccaa"]}
BAYER = {2: [[0, 2], [3, 1]],
         4: [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]}
BAYER[8] = [[4 * BAYER[4][y % 4][x % 4] + BAYER[2][y // 4][x // 4] for x in range(8)] for y in range(8)]


def load_u8(path):
    return np.array(Image.open(path).convert("RGBA"))


def save_u8(a, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(a.astype(np.uint8), "RGBA").save(path)


def oklab(rgb):
    """sRGB 0-255 (..., 3) to OKLab, where distance follows how different two colours look."""
    c = np.asarray(rgb, dtype=np.float64) / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    lms = c @ np.array([[0.4122214708, 0.2119034982, 0.0883024619], [0.5363325363, 0.6806995451, 0.2817188376],
                        [0.0514459929, 0.1073969566, 0.6299787005]])
    lms = np.cbrt(lms)
    return lms @ np.array([[0.2104542553, 1.9779984951, 0.0259040371], [0.7936177850, -2.4285922050, 0.7827717662],
                           [-0.0040720468, 0.4505937099, -0.8086757660]])


def _hex(c):
    return "%02x%02x%02x" % tuple(int(v) for v in c[:3])


def parse_rgb(text):
    t = text.strip().lstrip("#")
    if "," in t:
        return [int(v) for v in t.split(",")[:3]]
    return [int(t[i:i + 2], 16) for i in (0, 2, 4)]


def opaque_colours(a):
    px = a[a[..., 3] > 0][:, :3]
    return np.unique(px, axis=0) if len(px) else np.zeros((0, 3), np.uint8)


def load_palette(spec, root="."):
    """A built-in name, a .hex/.txt file (one hex colour per line), a GIMP .gpl, or from:<png>[,<png>...] (every
    opaque colour of reference sprites, so a new sprite matches a set)."""
    if spec in PALETTES:
        return np.array([parse_rgb(h) for h in PALETTES[spec]], np.uint8)
    if spec.startswith("from:"):
        cols = [opaque_colours(load_u8(resolve(p, root))) for p in spec[5:].split(",")]
        return np.unique(np.concatenate(cols), axis=0)
    p = resolve(spec, root)
    if not p.is_file():
        fail(f"palette not found: {spec} (built-in: {', '.join(sorted(PALETTES))})")
    cols = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith((";", "GIMP", "Name:", "Columns:")) or (line[0] == "#" and not
                                                                               _is_hex(line.split()[0][1:])):
            continue
        parts = line.split()
        if len(parts) >= 3 and all(v.isdigit() for v in parts[:3]):
            cols.append([int(v) for v in parts[:3]])
        elif len(parts[0].lstrip("#")) in (6, 8):
            h = parts[0].lstrip("#")
            cols.append(parse_rgb(h[2:] if len(h) == 8 else h))  # Paint.NET's AARRGGBB
    if not cols:
        fail(f"no colours in palette file: {spec}")
    return np.unique(np.array(cols, np.uint8), axis=0)


def _is_hex(t):
    return len(t) in (6, 8) and all(ch in "0123456789abcdefABCDEF" for ch in t)


def write_gpl(pal, path, name):
    lines = ["GIMP Palette", f"Name: {name}", "Columns: 8", "#"]
    lines += ["%3d %3d %3d\t%s" % (c[0], c[1], c[2], _hex(c)) for c in pal]
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


# grid detection: a fixing step, so pixelwright works without artwright. Colour changes between neighbouring
# columns (and rows) gather on the block edges; the period whose phase sum is most coherent is the pixel size.

def _edge_energy(a, axis, tol=24):
    """Colour change across each column (axis 1) or row edge; steps under tol are noise and count for nothing."""
    f = a.astype(np.int16)
    d = np.abs(np.diff(f, axis=axis)).max(axis=2)
    d = np.where(d > tol, np.minimum(d, 64), 0)
    return d.sum(axis=1 - axis).astype(np.float64)  # index i: the edge before pixel i + 1


def _coherence(e, s):
    pos = np.arange(1, len(e) + 1, dtype=np.float64)
    z = (e * np.exp(2j * np.pi * pos / s)).sum()
    tot = e.sum()
    return (abs(z) / tot if tot else 0.0), (np.angle(z) * s / (2 * np.pi)) % s


def detect_scale(e, smax):
    """(scale, offset, coherence) for one axis. Divisors of the true size are as coherent as the size itself and
    multiples are not, so the largest scale near the best coherence wins."""
    if e.sum() == 0 or smax < 2:
        return 1.0, 0.0, 0.0
    cands = []
    s = 2.0
    while s <= smax:
        cands.append(s)
        s *= 1.01
    cs = [(s, *_coherence(e, s)) for s in cands]
    best = max(c for _, c, _ in cs)
    if best < 0.5:
        return 1.0, 0.0, best
    s0 = max(s for s, c, _ in cs if c >= 0.85 * best)
    s0 = max((t for t in cs if abs(t[0] - s0) <= 0.1 * s0), key=lambda t: t[1])[0]  # the peak, not its shoulder
    fine = [(s, *_coherence(e, s)) for s in np.linspace(s0 * 0.98, s0 * 1.02, 81)]
    s, c, o = max(fine, key=lambda t: t[1])
    ci, oi = _coherence(e, float(round(s)))
    if ci >= 0.98 * c:  # an integer scale that fits as well wins
        s, c, o = float(round(s)), ci, oi
    if s - o < 1e-3:
        o = 0.0
    return float(s), float(o), float(c)


def _blocks(n, s, o):
    """Start and end of every block that is at least half inside 0..n."""
    i0 = int(math.floor(-o / s)) - 1
    res = []
    i = i0
    while o + i * s < n:
        a0, a1 = o + i * s, o + (i + 1) * s
        if min(a1, n) - max(a0, 0) >= s / 2:
            res.append((a0, a1))
        i += 1
    return res


def snap_grid(a, scale=None, offset=None, smax=64):
    """One pixel per block: the most common colour (5 bits a channel, alpha above or below half) in the block's
    inner 60%, averaged inside that winning bin. Never a plain average, which makes blend colours."""
    h, w = a.shape[:2]
    if scale:
        sx = sy = float(scale)
        ox, oy = (offset or (0, 0))
        cx = cy = None
    else:
        sx, ox, cx = detect_scale(_edge_energy(a, 1), min(smax, w / 4))
        sy, oy, cy = detect_scale(_edge_energy(a, 0), min(smax, h / 4))
        if sx > 1 and sy > 1 and abs(sx - sy) / max(sx, sy) < 0.03:
            sx = sy = (sx + sy) / 2
        elif sx == 1 or sy == 1:  # one axis found nothing: trust the other for both
            sx = sy = max(sx, sy)
            ox = ox if cx and cx >= 0.5 else oy
            oy = oy if cy and cy >= 0.5 else ox
    if sx <= 1 and sy <= 1:
        return a.copy(), dict(scale=[1, 1], offset=[0, 0], native=[w, h], uniform_blocks=1.0, detected=not scale)
    xs, ys = _blocks(w, sx, ox), _blocks(h, sy, oy)
    o = np.zeros((len(ys), len(xs), 4), np.uint8)
    uniform = 0
    for j, (y0, y1) in enumerate(ys):
        m = (y1 - y0) * 0.2
        r0, r1 = max(0, int(round(y0 + m))), min(h, max(int(round(y1 - m)), int(round(y0 + m)) + 1))
        for i, (x0, x1) in enumerate(xs):
            m = (x1 - x0) * 0.2
            c0, c1 = max(0, int(round(x0 + m))), min(w, max(int(round(x1 - m)), int(round(x0 + m)) + 1))
            px = a[r0:r1, c0:c1].reshape(-1, 4).astype(np.int32)
            key = ((px[:, 0] >> 3) << 11) | ((px[:, 1] >> 3) << 6) | ((px[:, 2] >> 3) << 1) | (px[:, 3] >= 128)
            vals, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
            win = inv.reshape(-1) == int(np.argmax(cnt))
            o[j, i] = np.round(px[win].mean(axis=0)).astype(np.uint8)
            uniform += len(vals) == 1
    rnd = lambda v: round(v, 3)
    return o, dict(scale=[rnd(sx), rnd(sy)], offset=[rnd(ox), rnd(oy)], native=[len(xs), len(ys)],
                   uniform_blocks=round(uniform / max(1, len(xs) * len(ys)), 3), detected=not scale,
                   coherence=[None if cx is None else rnd(cx), None if cy is None else rnd(cy)])


def remove_background(a, colour="auto", tol=40):
    """Clear the background: pixels connected to the border whose colour is within tol (OKLab x 255) of the
    background colour (auto: the most common border colour)."""
    h, w = a.shape[:2]
    b = a.copy()
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    if colour == "auto":
        if (border[:, 3] < 128).mean() > 0.5:
            return b, dict(colour=None, cleared=0, note="border already transparent")
        vals, cnt = np.unique(border[:, :3], axis=0, return_counts=True)
        bg = vals[int(np.argmax(cnt))]
    else:
        bg = np.array(parse_rgb(colour), np.uint8)
    dist = np.linalg.norm(oklab(a[..., :3]) - oklab(bg), axis=2) * 255
    near = (dist <= tol) | (a[..., 3] < 128)
    seen = np.zeros((h, w), bool)
    stack = [(y, x) for y in range(h) for x in (0, w - 1)] + [(y, x) for x in range(w) for y in (0, h - 1)]
    while stack:
        y, x = stack.pop()
        if seen[y, x] or not near[y, x]:
            continue
        seen[y, x] = True
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w and not seen[yy, xx]:
                stack.append((yy, xx))
    b[seen] = 0
    return b, dict(colour=[int(v) for v in bg], cleared=int((seen & (a[..., 3] >= 128)).sum()))


def median_cut(px, n):
    """Deterministic median cut: split the box with the widest channel range at that channel's mean value (a count
    median keeps halving a big flat area into twins) until n boxes, then merge colours that look the same."""
    boxes = [px.astype(np.int32)]
    while len(boxes) < n:
        spans = [(int((b.max(0) - b.min(0)).max()) if len(b) > 1 else -1) for b in boxes]
        k = int(np.argmax(spans))
        if spans[k] <= 0:
            break
        b = boxes.pop(k)
        ch = int(np.argmax(b.max(0) - b.min(0)))
        lo = b[:, ch] <= b[:, ch].mean()
        if lo.all() or not lo.any():
            lo = b[:, ch] <= np.median(b[:, ch])
        boxes[k:k] = [b[lo], b[~lo]]
    cols = [(np.round(b.mean(0)).astype(np.uint8), len(b)) for b in boxes if len(b)]
    cols.sort(key=lambda t: -t[1])
    keep = []
    for c, _ in cols:  # the more common of two near-twins stays
        if all(np.linalg.norm(oklab(c) - oklab(k)) >= 0.03 for k in keep):
            keep.append(c)
    return np.unique(np.array(keep, np.uint8), axis=0)


def quantise(a, pal, dither=None):
    """Every opaque pixel to its nearest palette colour in OKLab. Ordered (Bayer) dithering nudges each pixel by its
    matrix cell before the match, so flats stay flat and gradients get a regular pattern."""
    h, w = a.shape[:2]
    rgb = a[..., :3].astype(np.float64)
    if dither:
        n = int(str(dither).replace("bayer", "") or 4)
        if n not in BAYER:
            fail(f"dither must be bayer2, bayer4 or bayer8, not {dither}")
        m = (np.array(BAYER[n], np.float64) + 0.5) / (n * n) - 0.5
        spread = 255.0 / max(2, round(len(pal) ** (1 / 3)))
        rgb = np.clip(rgb + np.tile(m, (h // n + 1, w // n + 1))[:h, :w, None] * spread, 0, 255)
    flat, plab = rgb.reshape(-1, 3), oklab(pal)
    idx = np.empty(len(flat), np.int64)
    for i in range(0, len(flat), 65536):
        lab = oklab(flat[i:i + 65536])
        idx[i:i + 65536] = np.argmin(((lab[:, None, :] - plab[None]) ** 2).sum(-1), axis=1)
    b = a.copy()
    b[..., :3] = pal[idx].reshape(h, w, 3)
    b[a[..., 3] == 0] = 0
    return b


N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
N4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _key(a):
    return (a[..., 0].astype(np.int64) << 24) | (a[..., 1].astype(np.int64) << 16) | (a[..., 2].astype(np.int64) << 8) \
        | a[..., 3]


def _nb(k, dy, dx, fill=-1):
    """k shifted so that out[y, x] = k[y + dy, x + dx], with fill outside."""
    h, w = k.shape
    o = np.full_like(k, fill)
    o[max(0, -dy):h - max(0, dy), max(0, -dx):w - max(0, dx)] = k[max(0, dy):h - max(0, -dy) or h,
                                                                   max(0, dx):w - max(0, -dx) or w]
    return o


def _majority(k, y, x, skip=()):
    cnt = {}
    for dy, dx in N8:
        yy, xx = y + dy, x + dx
        if 0 <= yy < k.shape[0] and 0 <= xx < k.shape[1]:
            v = int(k[yy, xx])
            if v & 255 and v not in skip:
                cnt[v] = cnt.get(v, 0) + 1
    return max(sorted(cnt), key=lambda v: cnt[v]) if cnt else None


def _unkey(v):
    return [(v >> 24) & 255, (v >> 16) & 255, (v >> 8) & 255, v & 255]


def remove_orphans(a):
    """An opaque pixel with no same-colour 8-neighbour takes its neighbours' most common colour (a lone speck with
    no opaque neighbour is cleared)."""
    k = _key(a)
    alone = (a[..., 3] > 0)
    for dy, dx in N8:
        alone &= _nb(k, dy, dx) != k
    b = a.copy()
    for y, x in zip(*np.nonzero(alone)):
        v = _majority(k, y, x)
        b[y, x] = _unkey(v) if v is not None else 0
    return b, int(alone.sum())


def _edge(a):
    """Opaque pixels that touch transparency (or the frame edge) on a side, and which sides."""
    op = a[..., 3] > 0
    sides = {}
    for dy, dx in N4:
        sides[(dy, dx)] = op & (_nb(op.astype(np.int8), dy, dx, 0) == 0)
    return op, sides


def thin_outline(a, colour=None):
    """A doubled outline (two pixels of the outline colour from the edge inward) loses its inner pixel, which takes
    the most common non-outline neighbour colour."""
    op, sides = _edge(a)
    if not op.any():
        return a.copy(), 0
    edge = np.zeros_like(op)
    for m in sides.values():
        edge |= m
    if colour is None:
        cols = opaque_colours(a)
        colour = cols[int(np.argmin(oklab(cols)[:, 0]))]
    k = _key(a)
    ok = int(_key(np.array([*colour[:3], 255], np.uint8)))
    isout = k == ok
    inner = isout & op & ~edge
    hit = np.zeros_like(op)
    for (dy, dx), m in sides.items():
        hit |= inner & (_nb((isout & m).astype(np.int8), dy, dx, 0) == 1)
    b = a.copy()
    n = 0
    for y, x in zip(*np.nonzero(hit)):
        v = _majority(k, y, x, skip=(ok,))
        if v is not None:
            b[y, x] = _unkey(v)
            n += 1
    return b, n


def outline(a, mode, pal, light="top-left"):
    """Outline the sprite's edge pixels. A colour: that colour. auto: the darkest palette colour. selective: each
    edge pixel becomes a darker palette shade of its own colour, less dark on the sides facing the light."""
    op, sides = _edge(a)
    edge = np.zeros_like(op)
    for m in sides.values():
        edge |= m
    b = a.copy()
    if mode not in ("auto", "selective"):
        b[edge, :3] = parse_rgb(mode)
        return b, int(edge.sum())
    plab = oklab(pal)
    if mode == "auto":
        b[edge, :3] = pal[int(np.argmin(plab[:, 0]))]
        return b, int(edge.sum())
    lit = {"top-left": [(-1, 0), (0, -1)], "top-right": [(-1, 0), (0, 1)], "top": [(-1, 0)], "none": []}[light]
    facing = np.zeros_like(op)
    for d in lit:
        facing |= sides[d]
    for y, x in zip(*np.nonzero(edge)):
        lab = oklab(a[y, x, :3])
        drop = 0.08 if facing[y, x] else 0.22
        target = lab - np.array([drop, 0, 0])
        darker = plab[:, 0] < lab[0] - 0.03
        if not darker.any():
            continue
        d = ((plab - target) ** 2).sum(1) + np.where(darker, 0, 1e9)
        b[y, x, :3] = pal[int(np.argmin(d))]
    return b, int(edge.sum())


def tight_crop(a, pad=0, size=None, anchor="bottom"):
    op = a[..., 3] > 0
    if not op.any():
        fail("nothing opaque to crop")
    ys, xs = np.nonzero(op)
    c = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = c.shape[:2]
    if size == "pow2":
        side = 1 << int(math.ceil(math.log2(max(w, h) + 2 * pad)))
        W = H = side
    elif size:
        W, H = (int(v) for v in str(size).lower().split("x"))
    else:
        W, H = w + 2 * pad, h + 2 * pad
    if w + 2 * pad > W or h + 2 * pad > H:
        fail(f"sprite is {w}x{h} (+{pad} pad); it does not fit {W}x{H}")
    x0 = (W - w) // 2
    y0 = H - pad - h if anchor == "bottom" else (H - h) // 2
    o = np.zeros((H, W, 4), np.uint8)
    o[y0:y0 + h, x0:x0 + w] = c
    return o, dict(sprite=[w, h], canvas=[W, H], at=[x0, y0])


def make_tile(a, band=None):
    """A wrapping tile: near the edges each pixel comes from the copy rolled by half a tile (whose edges continue
    each other), in the middle from the original, crossing over through a Bayer pattern so no colour is new."""
    h, w = a.shape[:2]
    band = band or max(1, min(w, h) // 4)
    r = np.roll(a, (h // 2, w // 2), axis=(0, 1))
    yy, xx = np.mgrid[0:h, 0:w]
    near = np.maximum(np.clip(1 - np.minimum(xx + 0.5, w - xx - 0.5) / band, 0, 1),
                      np.clip(1 - np.minimum(yy + 0.5, h - yy - 0.5) / band, 0, 1))
    m = (np.array(BAYER[4], np.float64) + 0.5) / 16
    thr = np.tile(m, (h // 4 + 1, w // 4 + 1))[:h, :w]
    return np.where((near > thr)[..., None], r, a)


def seam_ratio(a):
    """Mean colour step across the wrap edges over the mean step between neighbouring pixels inside."""
    f = a.astype(np.float64)
    inside = np.concatenate([np.abs(np.diff(f, axis=1)).ravel(), np.abs(np.diff(f, axis=0)).ravel()]).mean()
    wrap = np.concatenate([np.abs(f[:, 0] - f[:, -1]).ravel(), np.abs(f[0] - f[-1]).ravel()]).mean()
    return round(float(wrap / inside), 3) if inside else (0.0 if wrap == 0 else float("inf"))


def preview(a, z=4):
    return Image.fromarray(a, "RGBA").resize((a.shape[1] * z, a.shape[0] * z), Image.NEAREST)


def aw_pixel(path, budget=None, tile=False):
    aw = find_aw()
    if not aw:
        return {"skipped": "artwright's aw.py not found (set PIXELWRIGHT_AW)"}
    # make output is native size: on a sprite of a few pixels aw's grid search can fit a false lattice (L-048)
    cmd = [sys.executable, str(aw), "pixel", str(path), "--scale", "1"] \
        + (["--budget", str(budget)] if budget else []) + (["--tile"] if tile else [])
    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except ValueError:
        return {"raw": (r.stdout + r.stderr).strip()[-2000:]}


def run_make(rec, root, outdir, use_aw=True):
    """snap, bg, palette, clean, crop, tile, in that order; each step is optional and recorded."""
    rid = rec.get("id") or Path(rec["input"]).stem
    a = load_u8(resolve(rec["input"], root))
    steps = {"input": dict(size=[a.shape[1], a.shape[0]], colours=int(len(opaque_colours(a))))}
    sn = rec.get("snap", {"scale": "auto"})
    if sn is not False:
        sc = sn.get("scale", "auto")
        a, steps["snap"] = snap_grid(a, None if sc == "auto" else sc, sn.get("offset"), sn.get("max", 64))
    bg = rec.get("background", "auto")
    if bg not in (False, None, "none"):
        a, steps["background"] = remove_background(a, bg if isinstance(bg, str) else bg.get("colour", "auto"),
                                                   40 if isinstance(bg, str) else bg.get("tol", 40))
    pal = None
    p = rec.get("palette")
    if p:
        if isinstance(p, (int, str)):
            p = {"colours": p} if isinstance(p, int) else {"name": p}
        if p.get("colours"):
            px = a[a[..., 3] > 0][:, :3]
            if len(px) == 0:
                fail("nothing opaque to take colours from")
            pal = median_cut(px, int(p["colours"]))
        else:
            pal = load_palette(p["name"], root)
        a = quantise(a, pal, rec.get("dither"))
        steps["palette"] = dict(colours=int(len(pal)), used=int(len(opaque_colours(a))), dither=rec.get("dither"))
    cl = rec.get("clean", {"alpha": 128, "orphans": True})
    if cl is not False:
        cl = cl or {}
        a = binary_alpha(a, cl.get("alpha", 128))
        st = {}
        if cl.get("orphans"):
            a, st["orphans_fixed"] = remove_orphans(a)
        if cl.get("thin"):
            a, st["doubles_thinned"] = thin_outline(a)
        if cl.get("outline"):
            a, st["outlined"] = outline(a, cl["outline"], pal if pal is not None else opaque_colours(a),
                                        cl.get("light", "top-left"))
        steps["clean"] = st
    cr = rec.get("crop")
    if cr:
        a, steps["crop"] = tight_crop(a, cr.get("pad", 0), cr.get("size"), cr.get("anchor", "bottom"))
    if rec.get("tile"):
        tl = rec["tile"] if isinstance(rec["tile"], dict) else {}
        a = make_tile(a, tl.get("band"))
        steps["tile"] = dict(band=tl.get("band") or max(1, min(a.shape[:2]) // 4))
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    pngPath, prevPath = outdir / f"{rid}.png", outdir / f"{rid}.x4.png"
    save_u8(a, pngPath)
    preview(a).save(prevPath)
    used = opaque_colours(a)
    write_gpl(used, outdir / f"{rid}.gpl", rid)
    budget = rec.get("budget") or (len(pal) if pal is not None else None)
    g = {"alpha_binary": bool(np.isin(a[..., 3], (0, 255)).all()), "colours": int(len(used))}
    if pal is not None:
        allowed = pal
        if cl and cl.get("outline") not in (None, "auto", "selective"):
            allowed = np.vstack([pal, np.array([parse_rgb(cl["outline"])], np.uint8)])
        g["colours_outside_palette"] = int((~(_key(np.c_[used, np.full(len(used), 255)])[:, None]
                                             == _key(np.c_[allowed, np.full(len(allowed), 255)])[None]).any(1)).sum())
    if budget:
        g["within_budget"] = len(used) <= int(budget)
    if cr and cr.get("size"):
        g["size_ok"] = [a.shape[1], a.shape[0]] == steps["crop"]["canvas"]
    if rec.get("tile"):
        g["seam_ratio"] = seam_ratio(a)
        g["seam_ok"] = g["seam_ratio"] <= 1.5
    if use_aw:
        aw = aw_pixel(pngPath, budget, bool(rec.get("tile")))
        item = (aw.get("items") or [aw])[0]
        g["aw_pixel"] = {k: item.get(k) for k in ("clean_pixel_art", "problems", "near_duplicate_colour_pairs",
                                                  "orphans", "skipped", "raw") if k in item} or aw
    ok = g["alpha_binary"] and g.get("colours_outside_palette", 0) == 0 and g.get("within_budget", True) \
        and g.get("size_ok", True) and g.get("seam_ok", True) and g.get("aw_pixel", {}).get("clean_pixel_art") is not False
    res = dict(ok=bool(ok), id=rid, out=pngPath.as_posix(), preview=prevPath.as_posix(),
               size=[a.shape[1], a.shape[0]], steps=steps, gates=g)
    (outdir / f"{rid}.make.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    return res


def binary_alpha(a, thr=128):
    b = a.copy()
    keep = b[..., 3] >= thr
    b[..., 3] = np.where(keep, 255, 0)
    b[~keep] = 0
    return b


def cmd_make(a):
    need_deps()
    rec = json.loads(Path(a.recipe).read_text(encoding="utf-8"))
    recs = rec if isinstance(rec, list) else rec.get("sprites", [rec])
    res = [run_make(r, a.root, a.outdir, not a.no_aw) for r in recs]
    if len(res) == 1:
        out(res[0], 0 if res[0]["ok"] else 1)
    out(dict(ok=all(r["ok"] for r in res), sprites=res), 0 if all(r["ok"] for r in res) else 1)


def cmd_snap(a):
    need_deps()
    off = [float(v) for v in a.offset.split(",")] if a.offset else None
    img, info = snap_grid(load_u8(a.input), a.scale, off, a.max)
    save_u8(img, a.out)
    out(dict(ok=True, out=a.out, **info))


def cmd_bg(a):
    need_deps()
    img, info = remove_background(load_u8(a.input), a.colour, a.tol)
    save_u8(img, a.out)
    out(dict(ok=True, out=a.out, **info))


def cmd_palette(a):
    need_deps()
    img = load_u8(a.input)
    if bool(a.palette) == bool(a.colours):
        out(dict(ok=False, error="give exactly one of --palette and --colours"), 2)
    if a.colours:
        px = img[img[..., 3] > 0][:, :3]
        if not len(px):
            fail("nothing opaque to take colours from")
        pal = median_cut(px, a.colours)
    else:
        pal = load_palette(a.palette)
    q = quantise(img, pal, a.dither)
    save_u8(q, a.out)
    if a.gpl:
        write_gpl(pal, a.gpl, Path(a.out).stem)
    out(dict(ok=True, out=a.out, palette=[_hex(c) for c in pal], used=int(len(opaque_colours(q))),
             before=int(len(opaque_colours(img)))))


def cmd_clean(a):
    need_deps()
    img = binary_alpha(load_u8(a.input), a.alpha)
    info = {}
    if a.orphans:
        img, info["orphans_fixed"] = remove_orphans(img)
    if a.thin:
        img, info["doubles_thinned"] = thin_outline(img)
    if a.outline:
        img, info["outlined"] = outline(img, a.outline, opaque_colours(img), a.light)
    save_u8(img, a.out)
    out(dict(ok=True, out=a.out, colours=int(len(opaque_colours(img))), **info))


def cmd_crop(a):
    need_deps()
    img, info = tight_crop(load_u8(a.input), a.pad, a.size, a.anchor)
    save_u8(img, a.out)
    out(dict(ok=True, out=a.out, **info))


def cmd_tile(a):
    need_deps()
    img = load_u8(a.input)
    before = seam_ratio(img)
    t = make_tile(img, a.band)
    save_u8(t, a.out)
    old = set(map(tuple, opaque_colours(img).tolist()))
    new = sum(tuple(c) not in old for c in opaque_colours(t).tolist())
    out(dict(ok=new == 0, out=a.out, seam_ratio_before=before, seam_ratio=seam_ratio(t), new_colours=new),
        0 if new == 0 else 1)


def cmd_palettes(a):
    out(dict(ok=True, palettes={k: len(v) for k, v in PALETTES.items()},
             files="any .hex, .txt or .gpl file, or from:<png>[,<png>...] for every colour of reference sprites"))


# ---- review page ----

def review_items(root, decided):
    """Animation sections from every <id>.gates.json under root; a brief's optional "take" names a newer take."""
    items = []
    for gp in sorted(root.rglob("*.gates.json")):
        rep = json.loads(gp.read_text(encoding="utf-8"))
        rid = rep.get("id") or rep.get("cardId")  # gates files from before 0.1.0 say cardId
        folder = gp.parent.relative_to(root).as_posix()
        briefs = [json.loads(p.read_text(encoding="utf-8")) for p in gp.parent.parent.glob("brief*.json")]
        motion = next((b.get("motion", "") for b in briefs if (b.get("id") or b.get("cardId")) == rid), "")
        take = gp.parent.name.split("-", 1)[1] if "-" in gp.parent.name else ""
        for name, g in rep.items():
            if not isinstance(g, dict):
                continue
            if "changed_share_per_frame" not in g:
                continue
            key = f"{rid}/{name}" + (f"-{take}" if take else "")
            if key in decided:
                continue
            sheet = Path(g["sheet"]).stem
            base = gp.parent.parent / "out" / f"{sheet}.png"
            if take and base.is_file() and base.read_bytes() == (gp.parent / f"{sheet}.png").read_bytes():
                continue  # this take left that animation unchanged
            frames = g.get("frames") or len(g["changed_share_per_frame"])
            contact = f"{sheet}.contact.png" if (gp.parent / f"{sheet}.contact.png").is_file() else f"{name}-contact.png"
            items.append(dict(key=key, title=rid, subtitle=f"{name} ({frames} frames)"
                              + (f", take {take}" if take else ""), text=[motion], kind="anim",
                              images=[f"{folder}/{sheet}.preview.png", f"{folder}/{contact}"],
                              gate=(f"gates {'PASS' if g['pass'] else 'FAIL'}: rest frame identical "
                                    f"{g['rest_frame_identical']}, outside-mask changes {g['changed_outside_mask']}, "
                                    f"new colours {g['new_colours']}, peak changed "
                                    f"{max(g['changed_share_per_frame']):.0%} of pixels, peak focal brightness "
                                    f"change {max(g['focal_mean_abs_luma_delta'])}")))
    return items


def review_page(root, extraPath, picksPath):
    try:
        picks = json.loads(picksPath.read_text(encoding="utf-8"))["items"]
    except (OSError, ValueError, KeyError):
        picks = {}
    decided = {k for k, v in picks.items() if v.get("pick") and v["pick"] != "redo"}
    items = []
    if extraPath and extraPath.is_file():
        items += [x for x in json.loads(extraPath.read_text(encoding="utf-8")) if x["key"] not in decided]
    items += review_items(root, decided)
    rows = []
    for it in items:
        if it.get("heading"):
            rows.append(f"<h1>{html.escape(it['heading'])}</h1>")
        texts = "".join(f"<p class=motion>{html.escape(t)}</p>" for t in it.get("text", []) if t)
        # "display": "full" shows paintings (loading screens, illustrations) at their own resolution, smoothly
        # scaled to the page width, instead of a sprite's 3x pixel zoom
        full = " full" if it.get("display") == "full" else ""
        if it.get("kind") == "choose":
            buttons = "".join(f'<button class="cand{full}" data-v="{html.escape(c["value"])}"><img src="{html.escape(c["src"])}" '
                              f'alt="{html.escape(c["value"])}"></button>' for c in it["choices"])
            body = f'<div class=btns>{buttons}<button data-v=redo>None fit</button>'
        elif it.get("kind") == "info":
            imgs = "".join(f'<img class="anim{full}" src="{html.escape(p)}" alt="{html.escape(it["title"])}">'
                           for p in it.get("images", []))
            body = f'{imgs}<div class=btns>'
        else:
            imgs = "".join(f'<img class="anim{full}" src="{html.escape(p)}" alt="{html.escape(it["title"])}">'
                           for p in it.get("images", []))
            yes = "Approve" if it.get("kind") == "approve" else "Keep"
            body = (f'{imgs}<p class=gate>{html.escape(it.get("gate", ""))}</p><div class=btns>'
                    f'<button data-v=keep>{yes}</button><button data-v=redo>Redo</button><button data-v=drop>Drop</button>')
        rows.append(f"""<section class=item data-key="{html.escape(it['key'])}">
<h2>{html.escape(it['title'])} <span>{html.escape(it.get('subtitle', ''))}</span></h2>{texts}
{body}<input class=note placeholder="note (what to change)"></div></section>""")
    if not rows:
        rows.append("<p>Nothing left to review.</p>")
    return f"""<!doctype html><html><head><meta charset=utf-8><title>Sprite review</title>
<style>
body{{background:#1b1b22;color:#ddd;font:15px system-ui,sans-serif;margin:0 auto;max-width:1100px;padding:16px}}
h1{{font-size:20px}} h2{{font-size:17px;margin:0 0 4px}} h2 span{{color:#9ab;font-weight:normal;font-size:14px}}
.item{{background:#24242d;border:2px solid #333;border-radius:8px;padding:12px;margin:14px 0}}
.item.keep{{border-color:#3a6}} .item.redo{{border-color:#c90}} .item.drop{{border-color:#a33}}
.anim{{image-rendering:pixelated;display:block;max-width:100%;margin:6px 0}}
.motion,.gate{{color:#aaa;font-size:13px}} .btns{{display:flex;gap:8px;align-items:center;flex-wrap:wrap}}
button{{background:#333;color:#eee;border:1px solid #555;border-radius:5px;padding:6px 14px;cursor:pointer;font-size:14px}}
.cand img{{image-rendering:pixelated;zoom:3;display:block}} .cand{{padding:4px}}
.cand.full img{{image-rendering:auto;zoom:1;max-width:100%}} .cand.full{{flex-basis:100%}}
.anim.full{{image-rendering:auto}}
button.on{{background:#4a7;border-color:#4a7;color:#000}}
.note{{flex:1;min-width:200px;background:#111;color:#eee;border:1px solid #555;padding:6px}}
#status{{position:sticky;top:0;background:#1b1b22;padding:6px 0;color:#9c9}}
</style></head><body>
<p>Previews show the still (left) and the animation (right) at 4x, pausing on the rest frame. Click for each item;
Redo takes a note. Every click saves. Say "done" in the chat when finished.</p>
<div id=status>loading</div>
{''.join(rows)}
<script>
let state = {{}};
const status = t => document.getElementById("status").textContent = t;
function save() {{
  fetch("picks", {{method: "POST", headers: {{"Content-Type": "application/json"}}, body: JSON.stringify(state)}})
    .then(r => status(r.ok ? "saved " + new Date().toLocaleTimeString() : "save failed"))
    .catch(e => status("save failed: " + e.message));
}}
function paint(sec) {{
  const s = state[sec.dataset.key] || {{}};
  sec.classList.remove("keep", "redo", "drop");
  if (s.pick) sec.classList.add(["redo", "drop"].includes(s.pick) ? s.pick : "keep");
  sec.querySelectorAll("button").forEach(b => b.classList.toggle("on", b.dataset.v === s.pick));
  sec.querySelector(".note").value = s.note || "";
}}
document.querySelectorAll(".item").forEach(sec => {{
  sec.querySelectorAll("button").forEach(b => b.onclick = () => {{
    const s = state[sec.dataset.key] = state[sec.dataset.key] || {{}}; s.pick = b.dataset.v; paint(sec); save(); }});
  sec.querySelector(".note").onchange = e => {{
    const s = state[sec.dataset.key] = state[sec.dataset.key] || {{}}; s.note = e.target.value; save(); }};
}});
fetch("picks.json", {{cache: "no-store"}}).then(r => r.ok ? r.json() : null).catch(() => null).then(d => {{
  state = (d && d.items) || {{}}; document.querySelectorAll(".item").forEach(paint);
  status(d ? "loaded saved picks" : "click to pick; every click saves");
}});
</script></body></html>"""


def cmd_review(a):
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
    root = Path(a.dir).resolve()
    picksPath = root / "picks.json"
    extraPath = Path(a.extra).resolve() if a.extra else root / "review-extra.json"

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kw):
            super().__init__(*args, directory=str(root), **kw)

        def do_GET(self):
            if self.path.split("?")[0] in ("/", "/index.html"):
                body = review_page(root, extraPath, picksPath).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            super().do_GET()

        def do_POST(self):
            if self.path.split("?")[0] != "/picks":
                self.send_error(404)
                return
            data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            # keep picks for items no longer on the page (decided earlier)
            try:
                old = json.loads(picksPath.read_text(encoding="utf-8"))["items"]
            except (OSError, ValueError, KeyError):
                old = {}
            old.update(data)
            picksPath.write_text(json.dumps({"updated": dt.datetime.now().isoformat(timespec="seconds"),
                                             "items": old}, indent=2), encoding="utf-8")
            self.send_response(204)
            self.end_headers()

        def log_message(self, *args):
            pass

    if a.print_page:
        print(review_page(root, extraPath, picksPath))
        return
    class Server(ThreadingHTTPServer):
        # http.server reuses addresses, which on Windows lets a second server bind a busy port silently and
        # the human is served whichever page answers first (L-025)
        allow_reuse_address = False

        def server_bind(self):
            if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            super().server_bind()

    try:
        server = Server(("127.0.0.1", a.port), Handler)
    except OSError as e:
        fail(f"port {a.port} is in use; stop the server on it or pick another port", detail=str(e))
    print(json.dumps(dict(ok=True, url=f"http://127.0.0.1:{a.port}/", picks=picksPath.as_posix())), flush=True)
    server.serve_forever()


def main(argv=None):
    p = argparse.ArgumentParser(prog="pxw.py", description=__doc__.split("\n")[0])
    p.add_argument("--version", action="version", version=VERSION)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("make")
    c.add_argument("recipe")
    c.add_argument("outdir")
    c.add_argument("--root", default=".")
    c.add_argument("--no-aw", action="store_true")
    c.set_defaults(fn=cmd_make)
    c = sub.add_parser("snap")
    c.add_argument("input")
    c.add_argument("out")
    c.add_argument("--scale", type=float)
    c.add_argument("--offset", help="X,Y of the first block edge, with --scale")
    c.add_argument("--max", type=int, default=64)
    c.set_defaults(fn=cmd_snap)
    c = sub.add_parser("bg")
    c.add_argument("input")
    c.add_argument("out")
    c.add_argument("--colour", default="auto")
    c.add_argument("--tol", type=float, default=40)
    c.set_defaults(fn=cmd_bg)
    c = sub.add_parser("palette")
    c.add_argument("input")
    c.add_argument("out")
    c.add_argument("--palette")
    c.add_argument("--colours", type=int)
    c.add_argument("--dither", choices=["bayer2", "bayer4", "bayer8"])
    c.add_argument("--gpl")
    c.set_defaults(fn=cmd_palette)
    c = sub.add_parser("clean")
    c.add_argument("input")
    c.add_argument("out")
    c.add_argument("--alpha", type=int, default=128)
    c.add_argument("--orphans", action="store_true")
    c.add_argument("--thin", action="store_true")
    c.add_argument("--outline", help="auto, selective or R,G,B")
    c.add_argument("--light", default="top-left", choices=["top-left", "top-right", "top", "none"])
    c.set_defaults(fn=cmd_clean)
    c = sub.add_parser("crop")
    c.add_argument("input")
    c.add_argument("out")
    c.add_argument("--pad", type=int, default=0)
    c.add_argument("--size", help="pow2 or WxH")
    c.add_argument("--anchor", default="bottom", choices=["bottom", "centre"])
    c.set_defaults(fn=cmd_crop)
    c = sub.add_parser("tile")
    c.add_argument("input")
    c.add_argument("out")
    c.add_argument("--band", type=int)
    c.set_defaults(fn=cmd_tile)
    c = sub.add_parser("palettes")
    c.set_defaults(fn=cmd_palettes)
    c = sub.add_parser("frames")
    c.add_argument("brief")
    c.add_argument("outdir")
    c.add_argument("--root", default=".")
    c.add_argument("--only")
    c.add_argument("--no-aw", action="store_true")
    c.set_defaults(fn=cmd_frames)
    c = sub.add_parser("grid")
    c.add_argument("image")
    c.add_argument("out")
    c.add_argument("--zoom", type=int, default=8)
    c.add_argument("--step", type=int, default=8)
    c.set_defaults(fn=cmd_grid)
    c = sub.add_parser("mask")
    c.add_argument("brief")
    c.add_argument("out")
    c.add_argument("--root", default=".")
    c.add_argument("--zoom", type=int, default=4)
    c.set_defaults(fn=cmd_mask)
    c = sub.add_parser("buildup")
    c.add_argument("brief")
    c.add_argument("out")
    c.add_argument("--anim", default="place")
    c.add_argument("--frames", type=int, default=6)
    c.set_defaults(fn=cmd_buildup)
    c = sub.add_parser("assemble")
    c.add_argument("brief")
    c.add_argument("out")
    c.add_argument("--plan", required=True)
    c.add_argument("--anim", default="place")
    c.add_argument("--root", default=".")
    c.set_defaults(fn=cmd_assemble)
    c = sub.add_parser("contact")
    c.add_argument("sheet")
    c.add_argument("out")
    c.add_argument("--frames", type=int, required=True)
    c.add_argument("--per", type=int, default=5)
    c.add_argument("--zoom", type=int, default=3)
    c.set_defaults(fn=cmd_contact)
    c = sub.add_parser("pack")
    c.add_argument("out")
    c.add_argument("frames", nargs="+")
    c.set_defaults(fn=cmd_pack)
    c = sub.add_parser("review")
    c.add_argument("dir")
    c.add_argument("--port", type=int, default=8765)
    c.add_argument("--extra")
    c.add_argument("--print-page", action="store_true", help="print the page HTML and exit (for tests)")
    c.set_defaults(fn=cmd_review)
    c = sub.add_parser("doctor")
    c.set_defaults(fn=cmd_doctor)
    a = p.parse_args(argv)
    try:
        a.fn(a)
    except OSError as e:  # a missing or unreadable input: one JSON object, not a traceback
        fail(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
