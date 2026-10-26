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
| `background` | `"auto"` | the most common border colour, flood-filled from the border within `tol` 40 (OKLab x 255); `"R,G,B"`, `{"colour": ..., "tol": N, "holes": N}`, or `"none"`. `holes` also clears enclosed patches of the background of N+ pixels (inside a ring or a handle, between an arm and the body; off by default, since a window that shows the sky may be meant). Skipped when the border is already transparent |
| `fog` | none | `{"colour": "R,G,B", "amount": 0.4}`: blend toward the air colour before the palette step, which locks the result again; a far-layer or background variant (about 0.4 for a middle layer, 0.8 for the far one) |
| `palette` | none | `"pico-8"`, a `.hex`/`.txt`/`.gpl` file, `"from:a.png,b.png"`, an integer N, or `{"name": ...}` / `{"colours": N}` |
| `dither` | none | `"bayer2"`, `"bayer4"` or `"bayer8"`, applied while quantising; or `{"pattern": "bayer4", "space": "linear", "max_step": 0.12}`: `linear` mixes each pixel's two nearest colours in the share that keeps its light (the default `srgb` nudge brightens: mid grey comes out 75% white on black and white instead of about 22%), `max_step` leaves pixels undithered where the pair differ by more than that OKLab lightness, so dither only joins neighbouring ramp steps |
| `clean` | `{"alpha": 128, "orphans": true}` | an object you write replaces the default, so list `"orphans": true` to keep that step; `alpha` threshold (always applied unless `clean` is `false`), `orphans`, `thin`, `outline` (`auto`, `selective`, `"R,G,B"`), `light` (`top-left`, `top-right`, `top`, `none`), `corners` (`true` for the darkest colour, or `"R,G,B"`: pixel-perfect lines, after the outline) |
| `crop` | none | `{"pad": 1, "size": "pow2" or "WxH", "anchor": "bottom" or "centre"}` |
| `tile` | none | `true` or `{"band": N}` (default band: a quarter of the shorter side) |
| `budget` | the palette's size | unique colour cap for the gate |

## Commands

Each step is also a command, for a quick try or a step the recipe does not cover:

```
pxw.py snap <in> <out> [--scale S] [--offset X,Y] [--max 64]
pxw.py bg <in> <out> [--colour auto|R,G,B] [--tol 40] [--holes N]
pxw.py palette <in> <out> (--palette P | --colours N) [--dither bayer4] [--dither-space linear] [--max-step 0.12] [--gpl pal.gpl]
pxw.py clean <in> <out> [--alpha 128] [--orphans] [--thin] [--corners] [--outline auto|selective|R,G,B] [--light top-left]
pxw.py swap <in.png|frames/> <out.png|out/> (--map map.json | --from a.gpl --to b.gpl)
pxw.py crop <in> <out> [--pad N] [--size pow2|WxH] [--anchor bottom|centre]
pxw.py tile <in> <out> [--band N]
pxw.py palettes
```

## How each step works

- **snap**: colour steps over 24 between neighbouring columns (and rows) are summed per edge. For each candidate
  scale from 2 to 64 (1% steps) the edge positions are summed as phases; the true pixel size and its divisors
  line up (coherence near 1) and its multiples do not, so the largest scale near the best coherence wins, refined
  to 0.05%, and an integer that fits as well is taken exactly. A few edges line up with some period by chance, so
  fewer than 8 edge positions, or a best coherence under 0.5 or 2.8/sqrt(edges) (random edges reach about
  2.6/sqrt(edges) one time in 20), means no grid (scale 1). One axis with no grid takes the other's scale only when
  that one rests on 16 or more edges.
  Each block keeps its inner 60% and takes the most common colour at 5 bits a channel, averaged inside that bin:
  the block's own colour, not a blend of its neighbours.
- **palette**: nearest colour in OKLab (distance follows how different colours look). Median cut is
  deterministic. Ordered dither adds the Bayer cell's offset before the match (`srgb`), or picks between the two
  nearest colours by the Bayer threshold against the pixel's position between them in linear light (`linear`).
  An ordered pattern is seen as the average of its light, so its mean belongs in linear light.
- **clean**: `orphans` gives a pixel with no same-colour 8-neighbour its neighbours' most common colour; a lone
  speck is cleared. `thin` removes the inner pixel of a two-pixel run of the outline colour (default the darkest
  colour) where it meets transparency. `outline` recolours the edge pixels (opaque, touching transparency on a
  side); selective picks, for each, the palette colour nearest to its own colour darkened by 0.08 (lit side) or
  0.22 (shadow side) in OKLab lightness. `corners` removes the redundant pixel of each stair step in a one-pixel
  line (an L of three pixels whose arms step on in opposite directions): it takes the colour on its outer
  diagonal, so the line stays 8-connected, its ends stay and real corners (arms at right angles) stay.
- **swap**: exact colour-to-colour replacement on opaque pixels of one PNG or every PNG in a folder (sheet frames),
  by a JSON map or by index between two palette files (file order). Exits 1 and lists any opaque colour the map
  leaves out. Two colours mapped to one merge those parts; to recolour one part alone, give it its own colour first.
  Uses: enemy tiers, team colours, night tiles.
- **crop**: tight to opaque pixels, centred across, bottom-anchored by default so sprites share a baseline.
- **tile**: the copy rolled by half a tile has edges that continue each other; pixels near the edge come from it,
  pixels in the middle from the original, crossing over through a Bayer pattern, so no colour is new.

## Rules from the books (2026-10-25)

- Detail under about 2 px at sprite size aliases when snapped: take it out of the brief or the render first, or
  choose a larger native size (Computer Graphics: Principles and Practice, 3rd ed., section 25.4).
- Draw a line and the fill it borders from one mask, never two separate rasterisations, or gaps and overlaps
  appear along the edge (Gambetta, Computer Graphics from Scratch, "Filled Triangles").
- Dither only between neighbouring, low-contrast ramp steps; never between far-apart colours, on small sprites or
  on parts that will animate (Azzi, Pixel Logic, pp. 111-120).

## Built-in palettes

Only `pico-8` (CC0) ships. Lospec palettes have their own licences; download the `.hex` from the palette's page
yourself and pass the file. `pxw.py` makes no network calls.
