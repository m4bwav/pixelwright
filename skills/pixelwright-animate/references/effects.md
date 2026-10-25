# Effects

Checked 2026-10-23 against `sw.py` 0.5.0 (`pxw.py` since 0.6.0). Every track: `effect`, `region`, optional `curve` (one value per frame;
missing = 1.0 every frame). Tracks run in order on a copy of the still, so a later track sees an earlier one's
pixels. Colours in parameters are `[r, g, b]`. Output colours are snapped to the region's ramp (its `select`
pixels plus `extraColours`) or the full still palette, so no stray colour appears.

| Effect | What it does | k means | Parameters |
|---|---|---|---|
| `pulse` | pushes lit pixels toward a hot colour (glow, flare, blink, chase) | strength now | `hot`, `strength` (0.8) |
| `spill` | additive light on the surface around a source box, falling off | strength now | `source` box, `tint`, `radius` (10), `strength` (0.5) |
| `darken` | desaturate and darken (power off) | 1 = fully off | `amount` (0.55), `desat` (0.7), `ramp` (snap to region ramp) |
| `glint` | bright diagonal band sweeping across | band position 0 to 1 | `hot`, `width` (3), `slope` (1), `strength` |
| `sparks` | 1 px sparks from a source, arcing and cooling | unused | `source` box, `bornFrames`, `colours` (hot to ember), `count`, `vy`, `gravity`, `seed` |
| `dust` | soft cloud band at the base, thinning | density | `band` [y0, y1], `colour`, `opacity`, `cell`, `drift`, `seed`, `lumpy` (a different height per column; `assemble` sets it) |
| `puffs` | steam or smoke puffs rising, growing, thinning (2 shades, binary alpha) | unused | `source` [x, y], `bornFrames`, `colours` [light, mid], `life`, `vx`, `r0`, `grow`, `seed` |
| `brighten` | multiplies the region's own pixels brighter (or dimmer at k < 0), warm-tinted, so painted texture keeps its contrast; use instead of `pulse` on painted art (L-017) | gain now (negative dims) | `gain` (0.6), `tint` per-channel weights (`[1, 0.8, 0.5]`); `hotspot` [x, y] with `radius` (8) and `floor` (0.2) makes the light come from one point and fall off (a fire hottest at the back lights the walls and floor less with distance, L-023), `coreTint` (e.g. `[1, 1, 1]`) whitens toward the hotspot |
| `shift` | moves a part by whole pixels (recoil, drill, bob) | offset = k * `by` | `part` region, `by` [dx, dy], `behind` (`still`, `clear`, `plate`, `nearest`, `grow`), `soft` (`over`: a moved semi-transparent rim pixel is composited over what is behind it instead of replacing it, so it cannot punch a hole in a wall; also on `bend`) |
| `rotate` | rotates a part about a pivot, majority-vote sampling | degrees | `part`, `pivot` [x, y], `behind`, `plate`, `plane` (0.5.0: a part turning in a plane seen at an angle, `[[ux, uy], [vx, vy]]` or `{"rim": [[x, y], ...]}`; T = A R A^-1 about the pivot) |
| `model_rotate` | turns a painted part with a 3D render's ID and position passes: each part pixel takes the colour its body point has in the painted frame 0, folded into one sector of the part's symmetry; gaps show the plate; made at the render's size and downscaled | unused (frame i is render frame i, or `map`) | `frames` (render folder), `part` (model part name), `painted`, `plate`, `symmetry`, `axis`, `tol`, `hires`; see [Model rotate](#model-rotate) |
| `bend` | sways a hanging part about its anchor row: each row moves sideways by k * `amp` * depth^`power`, so the rail holds and the hem swings (cloth, hides, plants) | sway now, -1 to 1 | `part` region, `amp` px (2), `power` (1.5), `anchor` (`top` or `bottom`), `behind` (`nearest`) |
| `bands` | soft darker (or lighter) lines drifting along `dir`: cloth travelling over a loom, a belt or a stream on painted art, where `scroll` would need a periodic texture; the pixels stay put and only a multiply moves, at sub-pixel speed | phase 0 to 1 (one period) | `period` px, `dir` [dx, dy], `origin` [x, y] (continue a band from one region into the next), `width` px (1), `gain` (-0.2), `tint` |
| `scroll` | stripes or a belt creep along, wrapping with the period | phase 0 to 1 | `period` px, `dir` [dx, dy] |
| `fill` | a level rising bottom to top; empty part dimmed, hot level line | share full | `dim` (0.6), `hot` |
| `buildup` | construction reveal from the ground: weld seam, dotted outline above | share built | `weld` colours, `ghost` colour, `sparks`, `jitter`, `seed` |
| `assemble` | realistic construction ending on the still: parts arrive by crane, drone, trolley, telescope, hinge or on-site weld; drones leave motion trails; machines kick up dust where they work near the ground | unused (frames come from each step's `at`) | `steps` [{`part`, `how`, `at` [start, end], `from`, `dir`, `pivot`, `angle`, `drones`, weld: `ragged` (2 px), `speed` (4 px/frame), `seed`}], `machine` colours, `weld`, `dust` (2 colours, or false); made by `pxw.py assemble` |
| `site` | natural construction ending on the still, for a timber-framed, daubed, roofed building seen from above at an angle: stakes and string on the ground diamond, a fieldstone footing, corner posts and wall plates, the still's wall timbers then its infill rising course by course, the gable, ridge pole, rafters and laths, the roof laid from the eave up to the ridge, a ladder; site elements take colours sampled from the still (0 new colours) | unused (frames 0 to `siteFrames` - 1; the last is the still) | `roof` and `lumber` (region names), `groundBase` {left, front, right: {x, y}}, `wallHeight` px, `eave` and `ridge` [[x, y], [x, y]], `ladder` [foot, top], `rafters` (7), `timberValue` (0.55), `timeline` {stakes, footing, posts, timber, infill, gable, rafters, roof, ladder: [start, end]; defaults scale from 30 frames}, `seed`; made by `pxw.py assemble` with `"vocabulary": "natural"` |
| `arc` | electric arcs: jagged 1 px bolts along paths, a new shape every frame, glow pixels beside them | share of paths lit | `paths` [[x0, y0, x1, y1], ...] (lit in list order), `colours` [core, glow], `jag` (2.5), `flicker` (0.25), `seed` |
| `drone` | a work drone flying a path, bobbing, with a motion trail; optional torch arm to a weld point | position along `path` by segment (k < 0 hides) | `path` [[x, y], ...], `torch` [x, y], `torchFrames`, `machine` (give it colours the still lacks), `weld` |
| `cart` | a ground cart rolling a crate | position from `from` to `to` (k < 0 or > 1 hides) | `from`, `to` (x), `y` (wheel row), `size` [w, h], `machine` |
| `external` | pastes frames made elsewhere, inside the region only | unused | `sheet` (frame size = still), `map` (frame index list) |

`shift` and `rotate` use `region` as the zone the moved part may land in; include the travel. `behind: nearest` (the default for
`bend`) fills a vacated pixel from the nearest non-part pixel on its row, for painted art with no plate. `behind: plate`
needs `plate`, a repainted still (an inpaint of what is behind the part) of the same size. `behind: grow` (0.4.3)
grows ground into the hole from the texture around it (neighbourhood-matched, seeded by `seed`), from `growFrom` (a
region: the ground only) or the opaque pixels within `growRadius` (22) of it; the choice for painted ground under a
lifted object (L-031). For 1 to 2 px moves
`behind: still` (the default for `shift`) reads as a stretch and needs no plate.

Particle effects (`sparks`, `puffs`) need a region with `"alpha": true` when they draw into empty sky.

Seeds make every run byte-identical; change `seed` for a different scatter.

## Patterns

- **Deck plates, not one stripe.** A full-width pad welded in 3 frames reads as a flat sweep (Mark: "too exactly
  even"). Split it into 2 or 3 plates (`<pad>0..2`), each its own `weld` step, starts one frame apart, `at` 4 frames.
- **Machines working on a building need their own colour.** Grey drones on a grey building vanish; give a `drone`
  or `cart` in a use animation a `machine` livery the still lacks (cyan: dark [20,40,60], mid [70,170,210]).
- **Sparks come from a tool, not from nowhere.** Put a `drone` with a `torch` at the sparks' `source` so the
  sparks have a visible cause (Mark: "sparks are randomly placed").
- **Charge reads as electricity, not sparks.** For a railgun or coil: `arc` rungs across the rails lit bottom to
  top, a cool `spill` on the barrel, one long `arc` up the channel on the shot frame (guard_post).

- Blink or chase: one `pulse` track per lamp, curves offset by a frame or two.
- Power-on (placement): `darken` on each emissive region with curves 1 to 0 in a believable order (control room,
  work lights, the machine), one dip back up for a flicker; `dust` at the base settling; the last frame is the
  still. Then `pxw.py buildup` for the construction frames in front.
- Natural construction (a medieval or village building, painted or pixel, seen from above at an angle):
  `pxw.py assemble <brief> <out> --plan plan.json` with `"vocabulary": "natural"`. The plan gives a `roof` polygon
  region, an optional `lumber` region (a plank pile that stands from frame 0), the `groundBase` diamond's left,
  front and right corners, `wallHeight` (px from the near ground line to the wall plate), and the `eave` and
  `ridge` lines; everything else in the silhouette is wall, split into timber (dark, or saturated and mid) and
  infill. Height is measured up from the near ground line, so the walls rise from the diamond. The command
  reports each part's pixels, the site colours it sampled and `idle_frames`; 30 frames at 12 fps read well. Check
  the timber split at zoom first: a light timber frame lands in infill and rises with it.
- Construction (placement, before the power-on): `pxw.py assemble <brief> <out> --plan plan.json`. Split the
  silhouette into parts the way a real site would: weld the deck or pad first (`weld`, `dir: right`), roll
  ground-level prefabs in (`trolley`), lower big prefab modules on the crane (`crane`), fly small boxes and tanks
  in (`drone`), extend stacks and masts out of their base (`telescope`), swing arms and booms open (`hinge`),
  weld what is built on site (`weld`, `dir: up`). Overlap the steps; 14 frames read well before a 10-frame
  power-on. A pixel belongs to the first step listing it, so put small parts first and a broad catch-all last;
  the command reports `uncovered_pixels` (they would stand from frame 0). If a power-on track moves a part
  (an arm parking), drop it with `dropTracks` and let a `hinge` step do the motion.
- Furnace or forge: `pulse` the mouth, `spill` on the metal around it, `sparks` from the mouth.
- Battery or tank: `fill` on the cells with a `hot` line, then `pulse` the indicator.
- Conveyor: `scroll` on the belt stripes with `period` = the stripe spacing; a full curve 0 to 1 returns to the
  still, so it loops.

## Model rotate

For a part that turns (wheel, millstone, sail, gear) when a 3D model of the building exists. The render folder
holds `sprite.json` and, per frame (in the folder or its `frames/` subfolder), `id_NNN.png` (flat part colours),
`pos_NNN.tif` (16-bit RGB(A) TIFF of the visible surface's object-space coordinates, stored as
`(L / (2 * pos_extent)) + 0.5`; read with `tifffile`, since Pillow cuts 16-bit RGBA to 8 bit) and optionally
`beauty_NNN.png` (its alpha is the silhouette; without it the painted frame's alpha, else opaque). `sprite.json`
gives `id_colours.<part>` (linear, as Blender writes an emission colour), `pos_extent`, and optionally
`rings.<part>.arms` (the symmetry) and a `loop` entry with `rotate_axis`.

```json
{"effect": "model_rotate", "region": "wheel", "frames": "renders/loop", "part": "wheel",
 "painted": "paint/frame0.png", "plate": "paint/plate.png", "symmetry": 8, "tol": 0.03}
```

| Field | Meaning |
|---|---|
| `frames` | the render folder |
| `part` | the part's name in `id_colours` (`idColour` [r, g, b] in sRGB overrides it) |
| `painted` | frame 0 painted at the render's size (or any size: it is resized to the render) |
| `plate` | the same painting with the part painted out: what shows between spokes |
| `symmetry` | n-fold symmetry (8 spokes = 8); default `rings.<part>.arms`, else 1 |
| `axis` | `X`, `Y` or `Z` in object space; default the `loop` entry's `rotate_axis` |
| `tol` | model units: a body point counts as seen in frame 0 within this (0.03) |
| `posExtent` | overrides `pos_extent` (1.0 if neither) |
| `sectorOffset` | degrees where the canonical sector starts (180 / symmetry) |
| `hires` | false skips writing the render-size frames to `<outdir>/<id>-<part>-hires/` |

Render one symmetry interval (a wheel with 8 spokes turns 45 degrees over the loop), with the last frame one step
short of it, and set `"rest": "none"`. Give the region from the ID pass: `"wheel": {"model": {"frames":
"renders/loop", "part": "wheel"}, "alpha": true}` covers every still pixel the part touches in any frame, grown by
`grow` (4) still pixels for the downscale's footprint. A pixel is written only where the downscaled frame differs
from the downscaled painted frame 0, so the rest of the region keeps the still byte for byte. `gates.json` reports
`model.<part>.unmatched_px` per frame: body points frame 0 never shows in any sector, filled from the nearest part
colour (L-041 to L-043). No pos pass: `rotate` with `plane` is the fallback for a thin part.

## External

For motion the effects cannot make. Get the human's go-ahead with the cost first. Make the frames at the still's
size from the still (PixelLab `animate-with-text-v3` keeps the input as frame 1; `interpolation-v2` goes from
the still to an edited end frame; `edit-animation-v2` refines frames), save them as one horizontal sheet, and
add `{"effect": "external", "region": "<part>", "sheet": "<sheet>"}`. Use `map` to reorder or hold frames, with
`null` for frames that keep the still. Only the region is taken; it is snapped to the palette (an AI frame is
a new roll of the dice every time, so its own palette is never trusted). The usual gates follow. Alpha is hardened at 128; add
`"soft": "keep"` to take the sheet's alpha as it is (smoke, steam, a soft painted rim over clear sky), and give the
region `"alpha": true`.
