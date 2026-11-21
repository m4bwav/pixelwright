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
- Machine in-betweens (FILM or RIFE, comfyui-gen `h3_assemble.py interp`) are evenly spaced and blend colours.
  Run them on the video before cutting and snapping frames, never on snapped pixel art, and then pick frames
  that bunch near the keys rather than keeping every one.
- A steady move needs a steady step: 8 px over 6 frames steps 1, 2, 1, 1, 2 and judders (Computer Graphics:
  Principles and Practice, section 18.2); 4 px over 8 frames stalls every other frame. Let the frame count divide
  the distance or the period. `cadence_uneven` reports it.
- Keep one cadence over one area: a part on twos beside a region moving on ones strobes (Williams, The Animator's
  Survival Kit, p. 79). Pixel art's 8 to 12 fps norm stands; only the mix is the fault. `cadence_mixed` reports it.
- Walk beats at 12 fps: 4 frames a step brisk, 6 natural, 8 slow (Williams p. 109 gives 8, 12, 16 at 24 fps).
- Too much action too fast: add frames and cushions, do not shrink the poses (Williams).
- In-betweens by intent (Thomas and Johnston, The Illusion of Life, p. 66, at 24 fps on twos; halve for 12 fps,
  minimum 0) between two head or part positions: 0 a huge hit, 1 a thrown-object hit, 2 a twitch, 3 a dodge,
  4 a crisp order, 5 a friendly call, 6 noticing, 7 trying to see, 8 searching, 9 pondering, 10 a slow stretch.
  Fast use actions keep their spacing jumps; full in-betweens even the timing and kill the snap.
- Moving hold: a held end pose lasts 4 to 8 frames at 12 fps; drift the furthest parts 1 px toward the extreme
  over its last half, or let parts arrive one after another (Thomas and Johnston pp. 62-63; Blair, Cartoon
  Animation, p. 144). `dead_hold` reports a run of more than 8 identical frames in a non-loop.
- Run cycles of 6 frames or fewer: no two frames within 2 of each other (seam included) may share a silhouette,
  or the cycle strobes or reads backwards; vary every foot position (Blair p. 109). `cycle_same_silhouette`
  lists such pairs (alpha masks differ but overlap above 0.97; a glow loop with a fixed alpha is skipped).

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
- `flicker_pixels` counts unique locations over the animation, including the seam of a loop. `flicker_at`, when
  present, samples up to 8 `[x, y]` pairs in row order (top to bottom, then left to right), with no frame index.
  Inspect the frames to find the blink. A matching pixel travelling through three frames is excluded even when
  its step exceeds 1 px; incoming and outgoing steps may differ by 1 px for rounding or acceleration. Over
  transparent sky, the match uses alpha so a spark may change colour; over opaque art it uses exact RGBA.
  This is a motion heuristic, not particle tracking. Set `max_flicker_pixels` on an animation only after reviewing
  its frames; intentional blinks and unmatched motion can still count.

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
- Game feel belongs in the engine, not the sheet (R-20261109-4): play the sheet at about 80 ms a frame and add the
  rest as engine layers, each behind a toggle: a screen flash (about 40% for 1 to 2 frames), shake (about 10 to 16
  game frames for an explosion: one slow wave and a quick tail; 4 to 8 high-frequency for melee), hit-stop measured
  in game frames (2 to 4 light, 6 to 10 heavy), debris rocks, a scorch decal that stays, embers, a smoke sheet held
  about 1.5 to 2 s, and a short point light. Which frame takes the sound: on a hard contact (a hit, a slam, a landing) the sound lands one frame after contact,
on the bounce (Williams p. 294); on a flash-led event (an explosion, a shot) its attack lands on the flash frame.
Often the flash is the bounce frame and both agree. Name `contact_frame` in the animation and gates.json carries
`sound_frame` = contact + 1; set `sound_frame` yourself for a flash-led event. The visual accent leads the
sound, never trails it (Blair p. 198: 2 to 3 frames at 24 fps, about 1 at 12); `sound_before_contact` flags a
`sound_frame` set before `contact_frame`. game-juice's juice-apply
  writes these; pixelwright supplies the separate layer sheets.
- An engine snapshot test must be deterministic: seeded particles, a fixed time, a fixed resolution (R-T4).
