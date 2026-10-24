# Make recipe and commands

Back to [SKILL.md](../SKILL.md).

## Recipe

A JSON object per sprite, a list of them, or `{"sprites": [...]}`. Paths are relative to `--root` (default: the
current folder). Steps run in this order and each is optional.

| Key | Default | Meaning |
|---|---|---|
| `id` | the input's file name | output names `<id>.png`, `.x4.png`, `.gpl`, `.make.json` |
| `input` | required | the render, PixelLab frame or drawing |
| `snap` | `{"scale": "auto"}` | `{"scale": 5.35, "offset": [3, 3]}` to force; `false` skips (native art) |
| `background` | `"auto"` | the most common border colour, flood-filled from the border within `tol` 40 (OKLab x 255); `"R,G,B"`, `{"colour": ..., "tol": N}`, or `"none"`. Skipped when the border is already transparent |
| `palette` | none | `"pico-8"`, a `.hex`/`.txt`/`.gpl` file, `"from:a.png,b.png"`, an integer N, or `{"name": ...}` / `{"colours": N}` |
| `dither` | none | `"bayer2"`, `"bayer4"` or `"bayer8"`, applied while quantising |
| `clean` | `{"alpha": 128, "orphans": true}` | an object you write replaces the default, so list `"orphans": true` to keep that step; `alpha` threshold (always applied unless `clean` is `false`), `orphans`, `thin`, `outline` (`auto`, `selective`, `"R,G,B"`), `light` (`top-left`, `top-right`, `top`, `none`) |
| `crop` | none | `{"pad": 1, "size": "pow2" or "WxH", "anchor": "bottom" or "centre"}` |
| `tile` | none | `true` or `{"band": N}` (default band: a quarter of the shorter side) |
| `budget` | the palette's size | unique colour cap for the gate |

## Commands

Each step is also a command, for a quick try or a step the recipe does not cover:

```
pxw.py snap <in> <out> [--scale S] [--offset X,Y] [--max 64]
pxw.py bg <in> <out> [--colour auto|R,G,B] [--tol 40]
pxw.py palette <in> <out> (--palette P | --colours N) [--dither bayer4] [--gpl pal.gpl]
pxw.py clean <in> <out> [--alpha 128] [--orphans] [--thin] [--outline auto|selective|R,G,B] [--light top-left]
pxw.py crop <in> <out> [--pad N] [--size pow2|WxH] [--anchor bottom|centre]
pxw.py tile <in> <out> [--band N]
pxw.py palettes
```

## How each step works

- **snap**: colour steps over 24 between neighbouring columns (and rows) are summed per edge. For each candidate
  scale from 2 to 64 (1% steps) the edge positions are summed as phases; the true pixel size and its divisors
  line up (coherence near 1) and its multiples do not, so the largest scale near the best coherence wins, refined
  to 0.05%, and an integer that fits as well is taken exactly. Below coherence 0.5 there is no grid (scale 1).
  Each block keeps its inner 60% and takes the most common colour at 5 bits a channel, averaged inside that bin:
  the block's own colour, not a blend of its neighbours.
- **palette**: nearest colour in OKLab (distance follows how different colours look). Median cut is
  deterministic. Ordered dither adds the Bayer cell's offset before the match.
- **clean**: `orphans` gives a pixel with no same-colour 8-neighbour its neighbours' most common colour; a lone
  speck is cleared. `thin` removes the inner pixel of a two-pixel run of the outline colour (default the darkest
  colour) where it meets transparency. `outline` recolours the edge pixels (opaque, touching transparency on a
  side); selective picks, for each, the palette colour nearest to its own colour darkened by 0.08 (lit side) or
  0.22 (shadow side) in OKLab lightness.
- **crop**: tight to opaque pixels, centred across, bottom-anchored by default so sprites share a baseline.
- **tile**: the copy rolled by half a tile has edges that continue each other; pixels near the edge come from it,
  pixels in the middle from the original, crossing over through a Bayer pattern, so no colour is new.

## Built-in palettes

Only `pico-8` (CC0) ships. Lospec palettes have their own licences; download the `.hex` from the palette's page
yourself and pass the file. `pxw.py` makes no network calls.
