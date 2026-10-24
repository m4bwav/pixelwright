---
name: pixelwright
description: "Start here for pixel art and 2D sprite work an agent should make or animate, when no sibling clearly owns the request: picks the route, checks pxw.py is ready, and hands over. pixelwright-make turns an AI render, PixelLab output or a drawing into real pixel art (grid snap, palette lock, outline, crop, tiles, gates); pixelwright-animate animates an existing still in code inside region masks (glows, sparks, parts, construction, sheets, a review page). A new sprite from scratch is rendered with comfyui-gen (or PixelLab) first, then made real here. Use on 'make me a pixel art sprite of', 'pixel art for my game', 'turn this into pixel art and animate it', 'sprite pipeline', 'pixelwright', 'spritewright' (the old name). Measuring and critiquing pixel art is artwright-pixel; engine import is the engine plugin. Also 'refresh pixelwright', 'is pixelwright stale'."
---

# pixelwright

Pixel art an agent can trust: code makes the pixels, gates prove them, a human picks. Two jobs, one script.

Script: `scripts/pxw.py` (Python 3.9+, numpy and Pillow only; Windows, macOS, Linux). Every command prints one
JSON object; exit 1 means a check failed, 2 a usage error. `pxw.py doctor` first: it must say `ok: true`
(missing packages: `python -m pip install numpy pillow`). `aw` in its output is artwright's `aw.py`, the judge.

## Route

| The request | Go to |
|---|---|
| A new sprite, icon, tile or item from a description | render it (comfyui-gen, or PixelLab when the human pays for it), then pixelwright-make |
| A render or drawing that should become clean pixel art, a palette, an outline, a tile, a size | [pixelwright-make](../pixelwright-make/SKILL.md) |
| An existing still that should move (use, placement, idle loop), a sprite sheet, a review page | [pixelwright-animate](../pixelwright-animate/SKILL.md) |
| Both: "make this a sprite and animate it" | make first; its `out/<id>.png` is the animation's `still` |
| "Is this good pixel art", "what is wrong with this sprite" | artwright-pixel (measures and critiques; never fixes) |
| Importing into Unity, Godot or Roblox | the engine plugin; pixelwright names the rules, it does not configure the engine |

Painted sprites (soft edges, brush texture, thousands of colours on purpose) are not pixel art: do not snap or
quantise them. pixelwright-animate handles painted stills; artwright's `aw.py sprite` judges them.

## Shared rules

- The human's art is never overwritten. Outputs go to a new folder; a shipped still is replaced only on their say-so.
- Everything is nearest-neighbour. Never smooth-resize pixel art, never judge it from a smoothed preview.
- A gate that fails twice for the same sprite stops the work: report the JSON, never loosen a threshold to pass.
- A sprite set shares one palette and one pixel density; take the palette from the set (`from:`) when one exists.
- Paid generators (PixelLab) need the human's yes first, naming what and what it costs; keys come from the
  environment (`PIXELLAB_API_KEY`), never a file.

## Upgrading from spritewright

spritewright was this plugin's name until 0.6.0. `sw.py` still runs (a shim in pixelwright-animate) for one release;
`SPRITEWRIGHT_AW` is still read beside `PIXELWRIGHT_AW`. Briefs, sheets and gates files are unchanged.

## Maintenance

Evergreen unit at the plugin root: `evergreen.json`, [RESEARCH.md](../../RESEARCH.md),
[CHANGELOG.md](../../CHANGELOG.md), [LEARNINGS.md](../../LEARNINGS.md), [TESTS.md](../../TESTS.md),
[MAINTENANCE.md](../../MAINTENANCE.md). On 'refresh pixelwright': follow MAINTENANCE.md.
