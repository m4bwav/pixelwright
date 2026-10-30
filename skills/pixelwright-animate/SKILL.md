---
name: pixelwright-animate
description: Animate an existing 2D game sprite (a building, machine or prop) without redrawing it. A brief names regions of the still and effects (glow pulse, blink, glint, light spill, power-off, sparks, steam, dust, part shift, rotate or bend, a wheel turned by a 3D render's passes, brighten for painted art, drifting bands, stripe scroll, level fill, arcs, drones and carts, realistic construction); pxw.py makes the frames in code, keeps every pixel outside the regions identical, locks colours to the still's palette, gates the result, packs a sheet with previews and serves a click-to-pick review page. PixelLab frames paste back through the mask. Use on 'animate this building', 'make the furnace glow when used', 'placement animation', 'sprite sheet from this still'. Making a still into real pixel art is pixelwright-make; rendering stills is comfyui-gen; measuring pixel art is artwright-pixel. Also 'refresh pixelwright'.
---

# pixelwright-animate

Animate the part, not the sprite. A diffusion or video model redraws a whole sprite every frame and it drifts;
a code effect inside a mask cannot. The still is the truth: the rest frame is the still byte for byte, and
nothing outside the brief's regions ever changes.

Script: `../pixelwright/scripts/pxw.py` (Python 3.9+, numpy, Pillow; Windows, macOS, Linux). Every command prints one
JSON object (usage errors: argparse text, exit 2). Call it as `python <plugin>/skills/pixelwright/scripts/pxw.py <command> ...`. `scripts/sw.py` here is the
old spritewright name, kept for one release; it runs `pxw.py`.

## Step 0: ready

1. Read the plugin's `evergreen.json`; if `next_due` has passed or `contradiction` is set, say so in one line,
   do the task, then refresh (MAINTENANCE.md).
2. `pxw.py doctor` must return `ok: true`. Missing numpy or Pillow: `python -m pip install numpy pillow`.
   `aw` in its output is artwright's `aw.py`, used for the frame checks; without it those checks are skipped
   and you say so.

## Step 1: brief

One JSON file per sprite. Full schema and an example: [references/brief.md](references/brief.md).

1. Look at the still at 8x with coordinates: `pxw.py grid <still.png> grid.png`. Read the PNG.
2. Decide what the real machine would do when used, and (for a placed building) how it powers on. Motion is
   what that object would really do, strong enough that a player sees something happened. One sentence per
   animation goes in `motion`; a human approves the motions before frames are made when this is a batch.
3. Write regions as rectangles (or a polygon or mask image) in still pixels. Narrow lit parts with
   `"select": "warm" | "cool" | "bright"` so only the lamp pixels glow, not the hazard stripes next to them.
   A region that may become transparent or draw into empty sky needs `"alpha": true`.
4. `pxw.py mask <brief> mask.png` tints every region; read it. `empty_regions` must be empty.

## Step 2: frames

Pick effects from [references/effects.md](references/effects.md); each track has a region and a per-frame
`curve` (0 to 1). Timing defaults: 12 fps, 8 to 12 frames for a use animation, holds by repeating curve values;
see [references/timing-and-gates.md](references/timing-and-gates.md).

```
pxw.py frames <brief.json> <outdir> --root <folder the brief's paths are relative to>
```

It writes, per animation: `<id>-<anim>-<N>f.png` (horizontal sheet, frame size = still), `<id>-<anim>-<N>f/fNN.png`,
`.preview.png` (4x animated PNG beside the still, pausing on the rest frame), `.contact.png`, and
`<id>.gates.json`. Confirm the sheet exists and the JSON says `ok: true` before reporting anything.

Animation names: `use` rests on its first frame, `place` on its last (it ends on the still), anything else on
its first unless `"rest": "last"` or `"rest": "none"` (a loop; the seam gate applies).

Placement: write the power-on (`darken` curves from 1 to 0, region by region, one flicker), then add the
construction frames: `pxw.py assemble <brief> <brief-assembled.json> --plan plan.json` (parts arrive the way a
real site builds: crane, drones, trolley, telescoping stacks, unfolding arms, on-site welding; see
[references/effects.md](references/effects.md) "Patterns"). `uncovered_pixels` must be 0. The older
`pxw.py buildup` (seam rising behind a dotted holographic outline) reads as too futuristic for hard sci-fi (L-007).
A natural building (timber, daub, thatch or tile; a village seen from above at an angle) takes a natural plan
instead: `"vocabulary": "natural"` with the roof polygon, the ground diamond, the wall height and the eave and
ridge lines; it raises stakes, footing, posts, walls course by course, rafters and the roof from the eave up, in
colours sampled from the still (effects.md "Patterns", L-055). The roof must differ from the walls in material (thatch,
tile or shingle over timber, daub or stone). A log building with a plank roof takes `"walls": "logs"` (whole
courses, the faces in turn, no posts: the frame order would raise the dark seams before the logs) and `"roofOrder":
"boards"` (boards side by side from the front rake), with the roof traced by hand as always (L-065, which replaces
L-056's "needs another build order"). Site lines are clipped to the finished silhouette by default (`clip`, L-057). Trace the
roof polygon by hand on an 8x grid: a colour mask of the thatch also takes the straw-toned daub and timber (L-059).
Open-sided sheds (roof on posts over goods) take the same plan; no posts-only variant (L-064).
A dug site (quarry, clay pit: a rim round a sunken floor, no roof) takes `"walls": "pit"`: a `floor` region
instead of roof, eave and ridge, dug out from the centre; the rim laid round from the front corner; `props` (one
region name or a list: crane, ladders, a hut) rise last, bottom up, and show the ground under them until then. Give
a prop polygon over sand or stone a colour `select` (`wood`) so the polygon's ground stays ground (L-067).
`"scaffold"` (any natural plan) puts a pole scaffold up first and takes it down from the top over the last frames.
Match the footprint: `"walls"` for square and oblong buildings (poles just outside each wall, one on every corner,
up to the eaves), `"ring"` only for round pits and towers. Both are open work: 2 px poles about 26 px apart, a
ledger every 9 px, a plank deck at every second ledger. Its pixels are the only ones the silhouette gate lets stand
outside the still. Tune with `"ring": {"ringRadius", "height", "lift", "bay", "deckEvery", "poles"}`; it shrinks to
fit the canvas (L-068, L-069).

## Step 3: gates

Every animation in `gates.json` must `pass`:

| Gate | Rule |
|---|---|
| `rest_frame_identical` | the rest frame equals the still exactly (exact RGBA, never a perceptual tolerance) |
| `changed_outside_mask` | 0 pixels change outside the tracks' regions |
| `alpha_changed_outside_alpha_regions` | 0 |
| `new_colours` | 0: only the still's colours, `extraColours` and the tracks' declared colours |
| `noticeable` | peak changed share >= 8% of opaque pixels or peak focal brightness change >= 40 (override per brief) |
| `loop_seam_ok` | loops only: the last-to-first jump is no bigger than the largest step inside |
| `drawn_outside_silhouette` | construction (`site`) only: 0 pixels on any frame where the still is fully transparent (L-057) |

Two more numbers are reported, not failed: `flicker_pixels` (lone pixels that turn on and back off over three
frames with no changed neighbour, excluding matched motion; `flicker_at` gives up to 8 unique `[x, y]` pairs,
with no frame index; an animation's `"max_flicker_pixels": 0` makes it a gate) and
`cadence_uneven` (a linear `scroll` or `shift` whose whole-pixel steps differ, such as 1, 2, 1, 1, 2: let the frame
count divide the period or distance, so each frame moves the same whole number of pixels). Fix both unless the
blink is the point.

Also read `aw_pixel_frames` (artwright's frame-size, bounding-box and baseline checks). A gate that fails twice
for the same sprite stops the work: report it with the gate JSON, do not loosen the threshold to pass.

Look at the `.contact.png` yourself before a human sees it: one-frame flicker, specks near glows, a part that
vanished, sparks that read as noise.

## Step 4: review

Put each sprite's brief in `<batch>/<id>/brief.json` and its frames in `<batch>/<id>/out/` (a newer take:
`brief-<take>.json` and `out-<take>/`). Then:

```
pxw.py review <batch> --port 8765
```

Run it in the background. Sections come from every `*.gates.json` under the folder; extra sections (pick one of
several candidate stills, approve a text brief) come from `<batch>/review-extra.json`
([references/brief.md](references/brief.md#review-extra)). `--link URL LABEL` (repeatable) puts links at the top of the page,
such as the askwright question set or inbox for questions that go with this review. Clicks save to `<batch>/picks.json` (`keep`, `redo`
with a note, `drop`, or a candidate value); decided items leave the page, `redo` stays. Send the human one
message: the URL and "click, then say done". When they say done, read `picks.json` and act on every item.

## Step 5: hand off to the engine

The sheet name carries the kind and frame count (`foundry-use-10f.png`: 10 frames of width/10), so an importer
needs no side file. Engine import and wiring belong to the project (a Unity editor script on
`ISpriteEditorDataProvider`, a Godot `SpriteFrames` resource); see
[references/timing-and-gates.md](references/timing-and-gates.md#engines). Keep sprite IDs stable across reslices.

## Parts from a 3D render

When a 3D model of the building exists (a Blender blockout painted over), take a turning part's mask and motion
from the model's passes, not from masks drawn by hand: the ID pass says where the part is in every frame, and the
pos pass says which point of its body each pixel shows. `model_rotate` gives each part pixel the colour that body
point has in the painted frame 0, folded into one sector of the part's symmetry, so every frame shows the same
painted part and the loop closes after one spoke interval. The gaps come from a plate painted without the part.
Region: `"model": {"frames": ..., "part": ...}`. Details: [references/effects.md](references/effects.md#model-rotate).
A screen-space `rotate` is wrong for a wheel seen at an angle; with no pos pass, give it a `plane` (L-041).

## Fallback: motion code cannot fake

A dome opening or an arm unfolding: ask the human first (it costs money), naming the sprite, the motion and the
cost. PixelLab (REST `api.pixellab.ai/v2`, Bearer key from the `PIXELLAB_API_KEY` environment variable, never a
file): `animate-with-text-v3` keeps the input as frame 1; `interpolation-v2` and `edit-animation-v2` suit a
building better. Save its frames as a sheet of the still's frame size and add a track
`{"effect": "external", "region": "<part>", "sheet": "<sheet.png>"}`: only that region is taken, snapped to the
still's palette, and the same gates run. Details: [references/effects.md](references/effects.md#external).

## Guards

- Never overwrite a shipped still or sheet without the human's say-so; candidates live in a scratch folder.
- Rotate only from the original still (`rotate` does), never from a rotated copy; at 0 degrees the part must
  equal the still.
- Construction: a temporary line (string, post, plate, rafter, lath) only draws where the finished building stands,
  on the part that explains it; lines over the sky that vanish on the last frame read as chatter, not scaffolding.
  Real scaffolding needs visible thickness and must read at 1x (L-057).
- Smoke that should follow a game state (fuel, heat, season) is one reusable overlay strip at a chimney anchor, not
  painted into each sprite's loop (L-058).
- Particles are hard-edged palette pixels with a 2 to 3 frame trail, never soft blurred circles.
- Preview timing from the APNG or the engine, never from a GIF (256 colours, 10 ms steps).
- Painted art: a part is the object's own colour family inside a loose shape, never the bare shape (soft edges
  carry ground along, L-030), and the ground a moved part leaves bare is `behind: grow` from the ground around it
  (L-031). A solid object with lit and shaded faces (cart, crate) is a loose polygon minus the background by value,
  not a colour select, which takes one face (L-037).
- Small parts: read a 12x overlay of the mask beside the bare crop before choosing the effect; rotate only what is
  clearly round or pivoted, and let a blade or tool stroke along its long axis (L-038).
- A part that goes into an opening (cart into a mine): move it along the track's own axis, draw it only inside
  the opening once it passes its rest position, and darken it toward the interior with depth; the far jamb hides
  it early, so keep the wait inside short (L-039).
- A part that travels more than a few pixels is the whole object, painted in code in ground coordinates with colours
  sampled from the still's matching faces, carried by what moves it (wheels on rails), occluded by depth behind the
  wall; offer the new rest frame as the idle still (L-040).
- Many copies of one building in a scene: the engine should hold each copy's first frame for a random part of one
  cycle before the loop runs, not start it on a random frame, so copies fall out of step and a start from an idle
  still equal to frame 0 stays seamless (L-060).
- Smoke and steam travel: puffs break off, rise and thin out (the project's own smoke strip, or `external` with
  `soft: "keep"`); never bend or shift a painted plume in place (L-034). Remove all the painted smoke, growing back
  what it covered, and emit from the true source; any part left still reads as frozen (L-036).

## Maintenance

Evergreen unit at the plugin root: `evergreen.json`, [RESEARCH.md](../../RESEARCH.md),
[CHANGELOG.md](../../CHANGELOG.md), [LEARNINGS.md](../../LEARNINGS.md), [TESTS.md](../../TESTS.md),
[MAINTENANCE.md](../../MAINTENANCE.md). Write a learning when corrected, when the same error happens twice, or
when a workaround is found (Trigger and Hypothesis).
