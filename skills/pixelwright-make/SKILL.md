---
name: pixelwright-make
description: "Turn an AI render, PixelLab output or a hand drawing into real pixel art, or tidy pixel art that is almost there. pxw.py snaps the image to its true pixel grid (detects scale, including fractional, and offset; one pixel per block by mode, never by averaging), clears a flat background, locks colours to a palette (PICO-8, a .hex or .gpl file, or every colour of the set's existing sprites) or extracts N colours, ordered dither, palette swaps, binary alpha, stray pixels fixed, doubled outlines thinned, an outline or selective outline added, a tight crop to a power of two or engine size, wrapping tiles, and gates the result (palette, budget, alpha, size, seam, then artwright's aw.py pixel). Use on 'make this real pixel art', 'fix the grid', 'snap this AI sprite', 'reduce to 16 colours', 'use the PICO-8 palette', 'match my other sprites' palette', 'add an outline', 'make this tile seamless', 'crop to 32x32'. Rendering is comfyui-gen; animating a still is pixelwright-animate; judging pixel art is artwright-pixel."
---

# pixelwright-make

An image model paints something that looks like pixel art: thousands of colours, a block size that wanders, soft
edges, a background. This skill makes it real: one pixel per block, a locked palette, hard alpha, clean edges, the
size the engine wants. It fixes; artwright-pixel judges. Never copy artwright's checks here.

Script: `../pixelwright/scripts/pxw.py` (Python 3.9+, numpy, Pillow). Every command prints one JSON object and exits
1 when its gates fail (a usage error prints argparse's text and exits 2). Recipe schema and command details: [references/recipe.md](references/recipe.md).

## Step 0: ready

1. Read the plugin's `evergreen.json`; past `next_due` or a `contradiction`: say so in one line, refresh after.
2. `pxw.py doctor` must say `ok: true`; `aw` is artwright's `aw.py`. Without it the `aw_pixel` gate is skipped:
   say so, and look harder at the preview yourself.
3. Know three things before starting (ask only what the request does not say): the **native size** (32x32 icon,
   16 px tiles, a 64 px character), the **palette** (a name, a file, or "match these sprites"), and the **colour
   budget** (default: the palette's size; artwright suggests 12 at 32x32 and 16 at 64x64). The smallest feature
   that must read (an eye, a key's teeth) sets the native size; tiles agree on one size before any are made, since
   a 32 px tile is four times the work of a 16.
4. Know the game's backgrounds (light, dark, busy) when an outline is wanted, and whether the sprite will move.

## Step 1: measure what came in

`aw.py pixel <render.png>` when artwright is installed: a raw render shows a scale, low lattice alignment and
thousands of colours. Then `pxw.py snap <render.png> snapped.png` alone and read `scale`, `native` and
`coherence` (absent when no grid is found):

- `native` should be close to the size you expected. A scale of 1 on a render means no grid was found (coherence
  under 0.5): the image is painted, not pixel art. Do not snap it; downscale the render to the native size in the
  pipeline that made it (comfyui-gen's `make_sprite.py`), then run palette and clean only.
- A wrong `native` (half or double): pass `--scale` (render width / native width) and check again.
- `uniform_blocks` far under 1 on a clean upscale means the offset is wrong; give `--offset`.

## Step 2: write the recipe and make

One JSON per sprite (or `{"sprites": [...]}` for a set); every step is optional and runs in this order:
snap, background, palette, clean, crop, tile.

```json
{"id": "potion", "input": "render.png", "palette": "from:../sprites/chest.png,../sprites/key.png",
 "clean": {"orphans": true, "thin": true, "outline": "selective", "light": "top-left"},
 "crop": {"pad": 1, "size": "32x32", "anchor": "bottom"}, "budget": 16}
```

```
pxw.py make recipe.json out --root <folder the recipe's paths are relative to>
```

It writes `out/<id>.png` (the sprite), `<id>.x4.png` (nearest-neighbour preview), `<id>.gpl` (the colours it
uses, for Aseprite or GIMP) and `<id>.make.json` (every step's numbers and the gates).

Choosing:

- **Palette**: a set's own colours (`from:`) beat a named palette when the sprite joins an existing set. A named
  palette (`pico-8` or a file) for a fresh style. `{"colours": N}` extracts N by median cut when nothing is fixed.
- **Dither**: off, unless the human asks or a large gradient bands, and off for any sprite that will be animated
  (the pattern crawls); `{"pattern": "bayer4", "space": "linear", "max_step": 0.12}` keeps the light and mixes only
  neighbouring steps (ordered only; error diffusion reads as noise).
- **Outline**: `selective` (a darker shade of each edge pixel's own colour, lighter on the lit side) suits dark or
  neutral backgrounds; on light or busy ones it breaks up, so use `auto` (the darkest palette colour all round); a
  colour forces one; `selective` with `"light": "none"` gives a coloured outline. A render that already has an
  outline: `thin` first, and no new outline. `"corners": true` makes its lines pixel-perfect.
- **Background with holes**: a ring, a handle or a gap between arm and body keeps the background colour inside;
  `{"background": {"holes": 4}}` clears those too (a window meant to show sky: leave it off).
- **Far layers**: `"fog": {"colour": <the sky>, "amount": 0.4}` (middle) or 0.8 (far), with the palette step on.
- **Orphans**: on for renders (they are noise). Off for hand-made art, where a lone pixel may be an eye or a glint.
- **Tiles**: `"tile": true` (or `{"band": N}`) for a wrapping ground tile; the gate checks the seam.

## Step 3: gates

`make.json` `gates` must all hold, and the command exits 0:

| Gate | Rule |
|---|---|
| `alpha_binary` | every alpha is 0 or 255 |
| `colours_outside_palette` | 0 (an explicit outline colour counts as allowed) |
| `within_budget` | unique colours at or under `budget` |
| `size_ok` | the canvas is the size asked for |
| `seam_ok` | tiles: the step across the wrap edge is at most 1.5x the mean step inside |
| `aw_pixel.clean_pixel_art` | artwright's verdict (integer scale, alignment, uniform blocks, no blend pixels, budget, alpha); `problems` says why not |

A gate that fails twice on the same sprite stops the work: report the gate JSON, do not loosen the budget to pass.

## Step 4: look

Read `<id>.x4.png` before a human sees it, then critique with artwright-pixel (silhouette, value, palette roles,
clusters, outlines, light, in that order). Typical repairs: a detail lost in the snap (an eye, a highlight) means
the render's detail is finer than the grid: render with bigger shapes or choose a larger native size; a muddy
palette means too few colours for the value range: first share ramp ends between materials (one highlight for two
greens, skin and wood meeting in one shadow), then raise the budget by 2 to 4 rather than dithering. One fix at a
time, then `make` again.

## Hand-offs

- Animating the finished still: pixelwright-animate (its `still` is `out/<id>.png`).
- Recolour variants (enemy tiers, team colours, night tiles): `pxw.py swap out/<id>.png v.png --map map.json`.
  A mirrored copy also mirrors the light: re-light it, or accept it knowingly.
- Editing by hand: the user's Aseprite (`aseprite --batch in.png --palette out/<id>.gpl --color-mode indexed
  --save-as x.aseprite`) or an Aseprite MCP server.
- Engine import (point filter, no compression, integer pixels per unit): the engine plugin, named, not configured.
- Other fixers: Pixel Snapper, unfake, proper-pixel-art (artwright-pixel's references). Use one when the human
  already has it; compare with `aw.py pixel` and keep whichever scores cleaner.

## Guards

- Never overwrite the user's art; outputs go to a new folder.
- Never smooth-resize pixel art; every scale in this skill is nearest-neighbour.
- Never answer "is this AI-made" from the pixels.

## Maintenance

Evergreen unit at the plugin root: `evergreen.json`, [RESEARCH.md](../../RESEARCH.md),
[CHANGELOG.md](../../CHANGELOG.md), [LEARNINGS.md](../../LEARNINGS.md), [TESTS.md](../../TESTS.md),
[MAINTENANCE.md](../../MAINTENANCE.md). Write a learning when corrected, when the same error happens twice, or when
a workaround is found.
