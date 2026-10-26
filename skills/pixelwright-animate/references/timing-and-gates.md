# Timing, gates and engines

Checked 2026-10-23. Sources are the `R-` entries in the plugin's RESEARCH.md.

## Timing

- 12 fps (83 ms a frame) is the default; 8 to 12 fps is the pixel-art norm (R-S10). Holds are repeated curve
  values, not longer frames, so every engine plays them the same.
- Use (event) animations: 8 to 12 frames, a fast attack and a slower settle. Placement: 8 to 12 power-on frames,
  plus about 6 construction frames in front (a build-up of about 5 frames from ground plan to finished is the
  city-builder norm, R-P6).
- Idle loops: 2 to 4 frames of 1 px moves with long holds, up to about 8 to add a blink (R-P11). Loops use
  `"rest": "none"` and must pass the seam gate.
- Sub-pixel tricks (shifting edge colours) only on big flat areas; on small sprites move whole pixels (R-P9).
- 1 px features blink in and out when animated; thicken them or leave them out of the region (R-P10, now
  confirmed by two books: Silber section 8.3, Azzi p. 199). `flicker_pixels` counts them. A row that appears or
  goes should pop 2-3 px at once, not 1.
- Keep faces and eyes out of shimmer, bend and sub-pixel regions: a face that wobbles by a pixel reads as a
  different expression (Azzi p. 205).
- Loops need at least 3 frames to read as motion; a 2-frame idle works only slowly, about 500 ms a frame (Azzi
  p. 232; Silber exercise 8.3). Walks: 8 frames typical, 16 smooth.
- In-betweens favour a key: frames bunched near the start or end pose read as weight; evenly spaced ones read as
  mechanical (Azzi pp. 232-234).
- A steady move needs a steady step: 8 px over 6 frames steps 1, 2, 1, 1, 2 and judders (Computer Graphics:
  Principles and Practice, section 18.2); 4 px over 8 frames stalls every other frame. Let the frame count divide
  the distance or the period. `cadence_uneven` reports it.

## Gates

The gates in SKILL.md step 3 are exact. Reasons:

- Exact RGBA equality, not a perceptual diff: tools such as pixelmatch ignore anti-aliased-looking 1 px changes
  by default, which on pixel art hides real edge changes (R-T2).
- One palette for all frames: quantising each frame alone gives each frame its own palette, which reads as
  flicker (R-P1).
- Frame size and anchor never change; jitter comes from frames of different sizes under a fixed anchor (R-T5).
  The sheet's frame size is the still's by construction; artwright's `aw.py pixel --frames` checks the
  bounding box and baseline.
- `noticeable` thresholds (8% changed or a focal brightness change of 40) come from one project's human picks
  (a glint at 4.5% read as subtle). No published number exists (R-T9); move them by the reviewer's comments,
  per brief, not globally.
- The human click review is the final gate; no metric catches a part that silently vanished (R-T7).

## Engines

The sheet name `<id>-<anim>-<N>f.png` is the contract; import and wiring are project code.

- Unity 6: TextureImporter Sprite Mode Multiple, slice N frames of width/N with `ISpriteEditorDataProvider`
  (`SpriteDataProviderFactories`, `GetSpriteRects`/`SetSpriteRects`, `Apply`), register names through
  `ISpriteNameFileIdDataProvider`, and keep each rect's `spriteID` across reslices so references survive (R-S8).
  Copy the still's import settings (filter, PPU, compression) so frame 0 looks exactly like the still;
  compression can shift colours (R-T8).
- Godot 4: a `SpriteFrames` resource from the sheet ("Add frames from sprite sheet", N horizontal), FPS per
  animation, or `add_frame(anim, texture, duration)` for holds without duplicate frames (R-S9).
- Aseprite (optional): `aseprite -b frames/*.png --sheet out.png --sheet-type horizontal --data out.json
  --format json-array` when a project wants Aseprite JSON (R-S6).
- An engine snapshot test must be deterministic: seeded particles, a fixed time, a fixed resolution (R-T4).
