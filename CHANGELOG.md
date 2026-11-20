# Changelog: pixelwright (formerly spritewright)

Every change to [README.md](README.md) and its companions, newest first, each with the reason. Reasons cite findings in [RESEARCH.md](RESEARCH.md) (`R-`), lessons in [LEARNINGS.md](LEARNINGS.md) (`L-`), and test runs in [TESTS.md](TESTS.md) (`T-`). State in `evergreen.json`. Protocol: MAINTENANCE.md.

Entry shape: `### C-20261120-1 · 2026-11-20 · 0.28.0: action-inputs, first/last-frame stills on a floor strip
- because: user request (technique harvest script backlog, verdict #18: r/aigamedev post 1x8m8ly by
  u/FutureTechPilot; ideas only, written fresh from our notes)
- files: pxw.py (new `action-inputs` command: `cmd_action_inputs`, `_sprite_cut`, `VIDEO_SIZES`),
  tests/test_make.py (TestActionInputs, 3 tests), pixelwright-animate SKILL.md (model-effects pointer) and
  references/model-effects.md (Character actions from a video model), plugin.json, pxw.py VERSION
- Opt-in: a new command only; every existing output is byte-identical. From one stance sprite (and an optional
  end pose) it writes the first and last frames at an H3 size or WxH (multiple of 32): whole-number nearest
  scale, feet on one ground line at the centre, a darker floor strip across the width, a sidecar with the prompt
  line, and a key-overlap gate (exit 1 when the sprite wears the background or strip colour).

### C-20261119-5 · 2026-11-19 · 0.27.0: cadence_mixed, contact and sound frames, Williams timing rules
- because: book learnings round 6 (Williams, The Animator's Survival Kit, expanded ed. 2009, pp. 79, 92-97, 109,
  294, 301), L-094
- files: pxw.py (`_step_cadence`, `_cadence_mixed`, gates `cadence_mixed`, `contact_frame`/`sound_frame`),
  tests/test_pxw.py (two TestRound2Gates tests), pixelwright-animate SKILL.md (step 3 report-only numbers),
  references/timing-and-gates.md (mixed cadence, walk beats, too-fast fix, which frame takes the sound) and
  references/effects.md (hits), plugin.json, pxw.py VERSION
- Report-only: sheets, frames and previews are byte-identical; gates.json gains `cadence_mixed` only when a region
  on twos touches one on ones, and `contact_frame`/`sound_frame` only when the brief names `contact_frame`. The old
  "sound on the flash frame" rule now applies to flash-led events; hard contacts take contact + 1 (L-094).

### C-20261119-4 · 2026-11-19 · 0.26.0: hue-shifted ramps and the ramp_chalky check
- because: book learnings round 6 (Pickard et al., Color & Light, 3dtotal 2021, pp. 46-48, 101-102), L-093
- files: pxw.py (new `ramp` command: `hue_ramp`, `ramp_report`, `oklab_to_rgb`), tests/test_make.py (TestRamp),
  pixelwright-make SKILL.md (Step 4) and references/recipe.md (Commands), plugin.json, pxw.py VERSION
- Opt-in: a new command only; every existing command and recipe output is byte-identical.

### C-20261119-3 · 2026-11-19 · 0.25.0: elastic grid snap, Atkinson dither, sprite stack, colour cycle
- because: user request (technique harvest pa20, p7, p14, p16)
- files: pxw.py (`_cut_profile`, `_walk_cuts`, `snap_grid(elastic=)`, `snap --elastic auto|on|off`, recipe
  `snap.elastic`; `DIFFUSION` kernel table behind `_fs_dither`, `--dither atkinson`; new `stack` command
  (`stack_sprite`, `_slices`); anim effect `cycle` (fx_cycle)), tests/test_make.py (TestElastic jitter, drift and
  CLI; TestStack; test_atkinson_dither_is_quieter_than_fs), tests/test_pxw.py
  (test_cycle_steps_colours_along_the_ramp_inside_the_region), pixelwright-make SKILL.md (snap checks, Hand-offs)
  and references/recipe.md, pixelwright-animate SKILL.md and references/effects.md (`cycle` row), plugin.json,
  pxw.py VERSION
- Credits: elastic cut walk adapted from Sprite Fusion Pixel Snapper by Hugo Duprez (MIT),
  https://github.com/Hugo-Dz/spritefusion-pixel-snapper (perfectPixel by theamusing, MIT, was compared and not
  adopted). Atkinson error-diffusion option inspired by sedthh/pyxelate (MIT), https://github.com/sedthh/pyxelate.
  Sprite stack and colour cycle: ideas from Pixel-Composer by Tanasart (MIT); no code copied from any of them.
- Output change: `snap` and `make` now walk each cell edge (grid "elastic") when either axis coherence is under 0.7
  and the scale is over 2; such images (jittered or drifting upscales) snap differently than in 0.24.0, recovering
  the native size where the uniform grid lost cells. `--elastic off` (recipe `"elastic": "off"`) restores the 0.24.0
  output. The snap JSON gains `grid` (and `cut_widths` when elastic). FS dither output is byte-identical (same taps
  and divisor, now from a table). Every other output is unchanged.

### C-20261119-2 · 2026-11-19 · 0.24.0: sparks bounce off a floor; pixelfx hand-off
- because: user request (technique harvest pa20, p5)
- files: pxw.py (fx_sparks `floor` and `bounce` keys), tests/test_pxw.py (test_sparks_floor_bounce_optional),
  pixelwright-animate references/effects.md (sparks row), SKILL.md (Fallback: standalone fire, explosion and pickup
  sprites go to patch-gg/pixelfx, then pxw make and gate), plugin.json, pxw.py VERSION
- Credits: patch-gg/pixelfx (MIT) for the particle sim idea (ground bounce with restitution); no code copied.
  With `floor` set, sparks are step-integrated and reflect (vy * -bounce, vx * 0.7). Without it the closed form
  runs unchanged, so existing sheets stay byte-identical.

### C-20261119-1 · 2026-11-19 · 0.23.0: RotSprite rotate, FS dither, ramps, palette sort, tilesets, sheet tags, thick outlines, onion skin
- because: user request (technique harvest pa20), R-20261119-1
- files: pxw.py (load_palette JASC fix; new `rotate` and `tileset` commands; `palette --dither fs
  --dither-strength --sort`; `swap --ramp`, `swap --step --mask --palette`; `clean --outline-width --outline-shape
  --inside`; `anim --extrude --tag --sort`; review page canvas player with frameTags playback and an onion-skin
  toggle), tests/test_make.py (TestPa20, 10 tests), skills/pixelwright-make/SKILL.md (Hand-offs),
  references/recipe.md (Commands), pixelwright-animate references/model-effects.md and brief.md (review-extra),
  RESEARCH.md, plugin.json, pxw.py VERSION
- Credits: Pixelorama (MIT), Aseprite's MIT-licensed render code and file spec, Piskel; ideas only, no code copied.
  JASC `.pal` files no longer crash (the `JASC-PAL` header was parsed as a hex colour). Output changes: `palette`
  now reports and writes its `--gpl` dark to light (`--sort luma`, the default; was the found order). `anim` sheets
  and JSON are identical at `--extrude 0` without `--tag`. Every other existing output is byte-identical; the 1 px
  outline path is unchanged without the new flags. fx_rotate inside `anim` briefs keeps its 4x supersample (not
  switched to RotSprite, so existing sheets stay reproducible).

### C-YYYYMMDD-n · date · one-line summary`, then `because:` (IDs or "user request"), `files:` (file and section), and a sentence on what changed. Cite section headings, not line numbers.

### C-20261118-3 · 2026-11-18 · 0.22.0: `pxw.py shadow` (drop shadow + feet anchor) and the colour-match note
- because: user request (technique harvest D2 SpriteCast, owed shadow/anchor export and colour match)
- files: pxw.py (new `shadow` command), tests/test_make.py (ShadowTest), skills/pixelwright-make/SKILL.md (Step 3),
  references/recipe.md (Commands), plugin.json, pxw.py VERSION
- `shadow` writes a soft or pixel drop-shadow sprite and an anchor JSON (lowest opaque row centre, pixel and
  normalized, Phaser/Godot/Unity values). Colour match is the existing `palette` with `from:`; documented, no new
  step. Existing commands unchanged.

### C-20261118-2 · 2026-11-18 · 0.21.1: non-square output cells note for pixel type
- because: user request (technique-harvest book round 20, Schlomer, *Typographic Knitting*; book rule, unverified on our tools)
- files: skills/pixelwright-make/references/pixel-type.md (Drawing, new Non-square output cells),
  skills/pixelwright-make/SKILL.md (pixel type line), plugin.json, pxw.py VERSION
- Docs only; no command output changed. Measure the cell aspect, stretch the template by whole cell blocks, treat
  grey edge pixels as dither; the knitting book is cited as support for the odd-stem rule.

### C-20261118-1 · 2026-11-18 · 0.21.0: walk/combat sheet route and `dirs --grid 6x4`
- because: user request (technique harvest D9 civitai 3046939, GPU-tested 2026-11-18: adopt-partly)
- files: skills/pixelwright/SKILL.md (Route), skills/pixelwright-make/SKILL.md (Step 1, Hand-offs), pxw.py (`dirs
  --grid 6x4`), tests/test_make.py (test_dirs_6x4_sheet), plugin.json, pxw.py VERSION, CHANGELOG.md (two stray
  Latin-1 middle dots in C-20261111-2 re-encoded as UTF-8)
- Hub row: comfyui-gen's boogu-walk-sheet, then a forced `snap --scale 4 --offset 0,0` (auto snap missed the soft
  4x grid on 4/4 sheets), bg, palette, and `dirs --grid 6x4`, which cuts 24 RGBA frames of 32x48 and reports each
  row's walk baselines (the real D9 sheet: 46/44/46 in every row). 3x3 and 2x2 output is unchanged.

### C-20261117-2 · 2026-11-17 · 0.20.0: `anim --slots` (ten characters from one clip) and the `overlap` gate
- because: user request (technique harvest D1 r/aigamedev 1xsvbmr, D2 SpriteCast), both GPU-tested 2026-11-17
- files: pxw.py (`anim --slots/--align-feet/--find-loop`, new `overlap` command), tests/test_pxw.py (SlotsTest),
  tests/test_make.py (OverlapTest), skills/pixelwright-animate/SKILL.md (Fallback), references/model-effects.md
  (Ten characters from one clip), skills/pixelwright-make/SKILL.md (Step 3), references/recipe.md (Commands)
- `anim --slots CxR` splits one i2v clip of a character sheet into slots, keys each from its own border colour,
  refuses a slot whose character overlaps the key or whose feet jump, aligns feet and centre and keeps the
  smoothest loop window. On the real H3 clip: 9 of 10 slots clean, the green frog refused. `overlap` scores a
  repaint's silhouette against its guide (raw and bbox-fitted IoU; warn < 0.85, fail < 0.70): the depth-only table
  (0.08) fails, barrel and crate pass. Existing `anim` output is unchanged without `--slots`.

### C-20261117-1 · 2026-11-17 · 0.19.3: code-drawn cost baseline; skeletal-sprite route noted
- because: R-20261117-1; user request (technique harvest D8, D4)
- files: skills/pixelwright/SKILL.md (Route, code-drawn row), RESEARCH.md, plugin.json, pxw.py VERSION
- Docs only; no command output changed.

### C-20261114-1 · 2026-11-14 · 0.19.2: raised descenders or a taller cell for lowercase pixel type
- because: user request (technique-harvest book round 16, Wagner *From ASCII Art to Comic Sans*, ch. 4)
- files: skills/pixelwright-make/references/pixel-type.md (Drawing), plugin.json, pxw.py VERSION
- Docs only; no command output changed.

### C-20261113-1 · 2026-11-13 · 0.19.1: pose from a mannequin render (Qwen-Image-Edit-2511, AnyPose fix)
- because: R-20261113-1; user request (technique-harvest, r/StableDiffusion 1pw1s08, GPU-tested 2026-11-12d)
- files: skills/pixelwright-animate/references/model-effects.md (Pose from a mannequin render), RESEARCH.md,
  plugin.json, pxw.py VERSION
- Docs only; no command output changed.

### C-20261112-3 · 2026-11-12 · 0.19.0: `pxw.py font` (atlas to TTF) and the Ref2Font route row
- because: R-20261112-2; user request (technique-harvest, r/StableDiffusion 1qw83f5, GPU-tested 2026-11-12b)
- files: skills/pixelwright/scripts/pxw.py (font), skills/pixelwright-make/references/pixel-type.md (Atlas to font
  file), skills/pixelwright-make/SKILL.md (pixel type line), tests/test_make.py (TestFont), RESEARCH.md, plugin.json
- New command; fontTools is an optional import used by `font` only. Existing commands unchanged.

### C-20261112-2 · 2026-11-12 · 0.18.1: seasonal-overlays reference (roof-snow pilot, parked)
- because: L-091; user request (roof snow tabled, record what was learned)
- files: skills/pixelwright-make/references/seasonal-overlays.md (new), skills/pixelwright-make/SKILL.md (Seasonal overlays), LEARNINGS.md, plugin.json
- Docs only; no script changed.

### C-20261112-1 · 2026-11-12 · 0.18.0: `pxw.py dirs --grid 2x2` and the Klein 4B spritesheet LoRA route
- because: R-20261112-1; user request (technique-harvest, r/FluxAI 1qzbz0f, GPU-tested 2026-11-12)
- files: skills/pixelwright/scripts/pxw.py (dirs), skills/pixelwright-make/SKILL.md (Hand-offs),
  tests/test_make.py (PadDirs), RESEARCH.md, plugin.json
- `dirs` cuts a 2x2 four-view sheet into S, E, N, W (or `--names`) and reports repeated silhouettes; the 3x3
  default is unchanged. pixelwright-animate is at its 200-line budget, so the route lives in make only.

### C-20261111-2 · 2026-11-11 · 0.17.0: `pxw.py pad`/`unpad` for edit models, `pxw.py dirs` ring-sheet cutter
- because: R-20261111-2; user request (technique-harvest, r/aigamedev 1pa9ygr and 1tlidho, GPU-tested 2026-11-11)
- files: skills/pixelwright/scripts/pxw.py (pad, unpad, dirs), skills/pixelwright-make/SKILL.md (Hand-offs),
  tests/test_make.py (PadDirs), RESEARCH.md, plugin.json
- New commands only; every existing command's output is unchanged.

### C-20261111-1 · 2026-11-11 · 0.16.0: `pxw.py fit` console tile and colour budgets, `gameboy` palette
- because: R-20261111-1; user request (technique-harvest, r/aigamedev 1q4pgaa)
- files: skills/pixelwright/scripts/pxw.py (fit, PALETTES), skills/pixelwright-make/SKILL.md (Hand-offs), tests/test_make.py (CropTile), RESEARCH.md, plugin.json
- New command counts unique 8x8 tiles (flip-deduped with `--flip`), colours per tile and per attribute area against gb or nes targets and fails when over; existing commands unchanged.

### C-20261110-3 · 2026-11-10 · harvest.json: technique-harvest targets for this unit
- because: user request 2026-11-10: plugins store their own technique-harvest targets (evergreen 1.1.0 harvest.json)
- files: harvest.json (new)
- Data file only; no skill text or version changed.

### C-20261110-2 · 2026-11-10 · 0.15.0: `pxw.py anim --sheet RxC` cuts one model sprite sheet into frames
- because: R-20261110-1; user request (technique-harvest, r/aigamedev 1wbmvnm)
- files: skills/pixelwright/scripts/pxw.py (anim), skills/pixelwright-animate/references/model-effects.md, tests/test_pxw.py (Anim), RESEARCH.md, plugin.json, skills/pixelwright-animate/SKILL.md (Guards: two bullets joined to get back under 200 lines)
- Gutter search with an equal-split fallback and the sheet prompt; anim without `--sheet` is unchanged.

### C-20261110-1 · 2026-11-10 · 0.14.0: `pxw.py breathe` sleep loop from a prone frame
- because: L sleep loop from a death strip (2026-11-10)
- files: skills/pixelwright/scripts/pxw.py (breathe), skills/pixelwright-animate/SKILL.md (Sleeping characters), tests/test_pxw.py (Breathe), LEARNINGS.md, plugin.json
- New command, ported from a game's one-off script; on its nine people sheets the output matches the hand-made sleep rows pixel for pixel.

### C-20261109-5 · 2026-11-09 · 0.13.3: explosion pattern and engine game-feel layers (docs)
- because: R-20261109-4; user request
- files: skills/pixelwright-animate/references/effects.md (Patterns), skills/pixelwright-animate/references/timing-and-gates.md (Engines), RESEARCH.md, plugin.json, pxw.py VERSION
- Frame-by-frame explosion beats and a list of engine-side layers; no command output changes.

### C-20261109-4 · 2026-11-09 · 0.13.2: code-drawn route and craft rules (docs)
- because: R-20261109-3; user request (technique-harvest, r/aigamedev post 1xb3k2l)
- files: skills/pixelwright/SKILL.md (Route), skills/pixelwright-make/SKILL.md (Step 4: look), RESEARCH.md, plugin.json, pxw.py VERSION
- Untested route for small icons, tiles and UI drawn as palette-keyed grids, credited to claude-pxl (MIT); no command output changes.

### C-20261109-3 · 2026-11-09 · 0.13.1: character actions from a video model (docs)
- because: user request (technique-harvest #18, r/aigamedev post 1x8m8ly)
- files: skills/pixelwright-animate/references/model-effects.md (Character actions from a video model), plugin.json, pxw.py VERSION
- New untested guidance section, credited to the post; no command output changes.

### C-20261109-2 · 2026-11-09 · 0.13.0: `normals` writes normal maps for 2D lights
- because: R-20261109-2; user request
- files: skills/pixelwright/scripts/pxw.py (normals), skills/pixelwright-make/SKILL.md (Hand-offs), skills/pixelwright/SKILL.md (Route), tests/test_make.py (TestNormals), RESEARCH.md, plugin.json
- New command after Hugo-Dz/spritefusion-sprite-normals (MIT); no existing command changes output.

### C-20261109-1 · 2026-11-09 · 0.12.0: `anim` cleans an image model's effect GIF into one sheet
- because: L-090, R-20261109-1; user request
- files: skills/pixelwright/scripts/pxw.py (anim), skills/pixelwright-animate/SKILL.md (Effects from a model's animation), skills/pixelwright/SKILL.md (Route), tests/test_pxw.py (Anim), plugin.json
- New command; no existing command changes output.

### C-20261106-5 · 2026-11-06 · 0.11.0: `stack` on moving effects, `detached_pixels_late` on upgrades
- because: L-015, L-082
- files: skills/pixelwright/scripts/pxw.py (`_moving_source`, `_detached_pixels`, `gates`), references/effects.md, tests/test_pxw.py
- `shift`, `scroll` and `rotate` take `stack: true` to read the frame so far; briefs without it are unchanged. Upgrade strips report detached scraps and can cap them with `max_detached_pixels`; the threshold is not calibrated on real strips, so the cap is opt-in. The rafter half of L-082 already failed `drawn_outside_silhouette`; a test now holds it for `before`.

### C-20261106-4 · 2026-11-06 · Sfxwright, when installed
- because: user request
- files: skills/pixelwright/SKILL.md (Sfxwright, when installed)
- Hand sound effects to sfxwright when present and read its sounds.json; this plugin's own steps stay as the fallback.

### C-20261106-3 · 2026-11-06 · 0.10.2: `collapse` pit plans leave no dirt ghost of a fallen prop
- because: user request (a clay pit's shed, a coop and a tree left dirt in their own outlines, standing in the air)
- files: skills/pixelwright/scripts/pxw.py (collapse: `build_stump`, `build_base`), tests/test_pxw.py, plugin.json
- In a pit plan the dirt base covered every fallen pixel of the still, props included. Props are now left out of it; their debris lands on the floor as before. Plans without `walls: pit` render as in 0.10.1.

### C-20261106-2 · 2026-11-06 · 0.10.1: `collapse` leaves a fenced yard open
- because: user request (a ranch's rubble filled its whole fenced yard with dirt and failed the outside gate)
- files: skills/pixelwright/scripts/pxw.py (collapse: `_col_open_yard`, `_col_tidy`), tests/test_pxw.py, plugin.json
- The hole fill that stops grass showing through a heap also filled any hole the fence enclosed. Holes the still already had that are at least 9 px across now stay open; thinner gaps fill as before, so buildings without a yard render byte for byte as in 0.10.0.

### C-20261106-1 · 2026-11-06 · 0.10.0: `collapse` command for rubble, collapse and clear strips
- because: L-088; user request
- files: skills/pixelwright/scripts/pxw.py (collapse), tests/test_pxw.py, skills/pixelwright-animate/SKILL.md, LEARNINGS.md, plugin.json
- One seeded shard simulation gives the rubble still, a collapse strip opening on the still and resting on the rubble, a clear strip, and burnt versions. `--clear-to` ends the clear strip on the next strip's first frame. Gates check the joins, that the heap settled, that it really fell, and that it rests as one piece. No existing command changes output.

### C-20261105-2 · 2026-11-05 · frames no longer crashes on an empty weld step
- because: L-085
- files: skills/pixelwright/scripts/pxw.py (_drones_at, puff sources), tests/test_pxw.py, LEARNINGS.md

### C-20261105-1 · 2026-11-05 · 0.9.2: learnings consolidated, 83 active to 10
- because: consolidation due (83 > 25); L-ids below
- files: LEARNINGS.md, LEARNINGS-ARCHIVE.md (new), skills/pixelwright-animate/references/effects.md (Rules from use, Natural construction, Model rotate, table, track-order note), references/brief.md, skills/pixelwright-make/references/recipe.md (snap), TESTS.md (Case design), plugin.json, pxw.py (version)

Docs only; no effect or make output changes. The 0.9.1 entry shared the ID C-20261104-1 with 0.9.0 and is now C-20261104-2. brief.md cited L-046 for `display: full`; it is L-052. effects.md said every later track sees earlier pixels, which `shift`, `scroll` and `rotate` do not.
Promoted: L-001, L-002, L-003, L-004, L-005, L-006, L-007, L-008, L-009, L-010, L-011, L-012, L-014, L-015, L-018, L-023, L-030, L-031, L-034, L-036, L-037, L-038, L-039, L-040, L-041, L-042, L-043, L-044, L-049, L-052, L-053, L-054, L-055, L-056, L-057, L-058, L-059, L-060, L-061, L-062, L-063, L-064, L-065, L-066, L-067, L-069, L-070, L-071, L-072, L-073, L-074, L-075, L-076, L-077, L-080, L-081, L-082, L-084, L-086.
Retired or merged: L-017, L-019, L-020, L-021, L-024, L-025, L-026, L-035, L-045, L-046, L-047, L-048, L-068, L-079.
Edited, still active: L-016 (takes L-019), L-027 (takes L-021, L-024), L-028, L-029 (test path), L-085 (reproduced on 0.9.1; Scope and Status added).
Survivors that took merged rules: L-023 (L-020, L-026), L-036 (L-035), L-069 (L-068), L-078 (L-079).

### C-20261104-2 · 2026-11-04 · 0.9.1: `roofFaces` frames a complex roof one face at a time
- because: L-086 (user report)
- files: pxw.py (natural site rafters), pixelwright-animate SKILL.md, tests, LEARNINGS.md

A hipped, L-shaped or courtyard roof gets its ridge, rafters and laths per traced face instead of one eave and ridge grid.
### C-20261104-1 · 2026-11-04 · 0.9.0: pixel type reference from Arcade Game Typography
- because: user request (pre-approved book changes); the plugin had nothing on fonts
- files: skills/pixelwright-make/references/pixel-type.md, skills/pixelwright-make/SKILL.md, plugin.json, pxw.py (version)

Grid, drawing, character set, physical size, scaling up. No new commands.

### C-20261103-4 · 2026-11-03 · 0.8.23: learning on old-roof scraps in upgrade strips
- because: L-082
- files: LEARNINGS.md, plugin.json, pxw.py (version)

Docs only: what to check in the last frames of a strip built with `before`, and the missing gate.

### C-20261103-3 · 2026-11-03 · 0.8.22: an upgrade's back footing, string, post and plates stand behind the old building
- because: L-081 (user report)
- files: skills/pixelwright/scripts/pxw.py (`_site_items`, `fx_site`, `VERSION`), tests/test_pxw.py, LEARNINGS.md (L-081), .claude-plugin/plugin.json
Site pieces on the B corner and the R-B and B-L edges are tagged as back and drawn before the old still; front pieces still draw over it.

### C-20261103-2 · 2026-11-03 · 0.8.21: upgrades build over the old level; the scaffold's back half stands behind it
- because: L-081 (revised: user request)
- files: skills/pixelwright/scripts/pxw.py (`fx_site`, `_site_old`, `SITE_TIMELINE`, `VERSION`), skills/pixelwright-animate/SKILL.md, tests/test_pxw.py, LEARNINGS.md (L-081), .claude-plugin/plugin.json
No teardown: the old still stays inside the new silhouette until the new work covers it, what sticks out past it is wiped from the ground up over `wipe`, and the scaffold's back half draws behind the old building. `demolish` is gone.

### C-20261103-1 · 2026-11-03 · 0.8.20: upgrade strips (`before`: the old level comes down, the new one rises)
- because: L-081
- files: skills/pixelwright/scripts/pxw.py (`fx_site`, `_site_old`, `SITE_TIMELINE`, gates, `VERSION`), skills/pixelwright-animate/SKILL.md, tests/test_pxw.py, LEARNINGS.md (L-081), .claude-plugin/plugin.json
A natural plan's `before` (the previous level's still, same canvas) opens the strip on it and takes it down from the top over `demolish`, with a ragged edge, behind the scaffold; the gates allow its pixels and colours.

### C-20261102-4 · 2026-11-02 · 0.8.19: no scaffold on low or wide sites; buildings in a painted yard rise with the rim (docs only)
- because: L-080
- files: LEARNINGS.md (L-080), .claude-plugin/plugin.json, skills/pixelwright/scripts/pxw.py (`VERSION`)
Fenced yards and docks skip the scaffold; a building standing on a painted yard floor is part of the rim, not a prop.

### C-20261102-3 · 2026-11-02 · 0.8.18: fill a dark opening by fading its rim inward (docs only)
- because: L-078, user request
- files: LEARNINGS.md (L-078), .claude-plugin/plugin.json, skills/pixelwright/scripts/pxw.py (`VERSION`)
A dark opening gets its rim's own colours fading into black with depth, not a drawn back wall or pattern.

### C-20261102-2 · 2026-11-02 · 0.8.17: a changed still re-makes every strip and review media resting on it (docs only)
- because: L-077, user request
- files: skills/pixelwright-animate/SKILL.md (natural plans), LEARNINGS.md (L-077), .claude-plugin/plugin.json,
  skills/pixelwright/scripts/pxw.py (`VERSION`)
After a still changes, every strip whose rest frame it is and every GIF or page showing them is re-made and re-shown in
the same change.

### C-20261102-1 · 2026-11-02 · 0.8.16: a still showing the working state gets a cold idle still (docs only)
- because: L-076
- files: skills/pixelwright-animate/SKILL.md (natural plans), LEARNINGS.md (L-076), .claude-plugin/plugin.json,
  skills/pixelwright/scripts/pxw.py (`VERSION`)
A lit still is the active loop's base; the idle tile and the construction strip end on a cold still grafted from an
image edit in the still's own colours.

### C-20261101-3 · 2026-11-01 · 0.8.15: fires lit last, stack mouths with their rim (docs only)
- because: L-075
- files: skills/pixelwright-animate/SKILL.md (natural plans), LEARNINGS.md (L-075), .claude-plugin/plugin.json,
  skills/pixelwright/scripts/pxw.py (`VERSION`)
A building's fire stays dark until it stands; a stack mouth is laid with its rim; a pit's water comes after its ring.

### C-20261101-2 · 2026-11-01 · 0.8.14: stone buildings and small structures (docs only)
- because: L-074
- files: skills/pixelwright-animate/SKILL.md (natural plans), LEARNINGS.md (L-074), .claude-plugin/plugin.json,
  skills/pixelwright/scripts/pxw.py (`VERSION`)
How to build an all-stone building without rafters or a roof frame, and a small well without a scaffold, from the
existing log and pit orders.

### C-20261101-1 · 2026-11-01 · 0.8.13: props one at a time, `propGround` per prop
- because: L-073
- files: skills/pixelwright/scripts/pxw.py (`fx_site`, `SITE_KEYS`, `VERSION`), skills/pixelwright-animate/SKILL.md
  (pit order), tests/test_pxw.py, LEARNINGS.md (L-073), .claude-plugin/plugin.json
`"propOrder": "each"` raises a pit plan's props in list order, each over its own slice of the timeline; `"propGround"`
takes a list of prop names to leave empty while the others show grown ground.

### C-20261030-6 · 2026-10-30 · 0.8.12: `propGround: "clear"` for a fenced yard
- because: L-072
- files: skills/pixelwright/scripts/pxw.py (`fx_site`, `SITE_KEYS`, `VERSION`), skills/pixelwright-animate/SKILL.md
  (pit order), tests/test_pxw.py, LEARNINGS.md (L-072), .claude-plugin/plugin.json
A pit plan can leave a waiting prop empty instead of growing the ground into it: a yard's floor is bare, so the grown
ground was faint edge pixels stretched into columns.

### C-20261030-5 · 2026-10-30 · 0.8.11: pit props only where they stand against the sky
- because: L-071
- files: skills/pixelwright-animate/SKILL.md (pit order), LEARNINGS.md (L-071), .claude-plugin/plugin.json,
  skills/pixelwright/scripts/pxw.py (`VERSION`)
Docs only: a prop over a lumpy floor streaks while it waits, so frames and ladders lying on the floor go with it.

### C-20261030-4 · 2026-10-30 · 0.8.10: adding a part to a still that already has strips
- because: user request, L-070
- files: skills/pixelwright-animate/SKILL.md (rules), LEARNINGS.md (L-070), .claude-plugin/plugin.json,
  skills/pixelwright/scripts/pxw.py (`VERSION`)
Docs only: lift the part from a sibling sprite with a saturation mask, put its rectangle in the region it rests on,
and re-make every strip from the new still instead of stamping frames.

### C-20261030-3 · 2026-10-30 · 0.8.9: a square scaffold for square buildings, lighter planking
- because: user request, L-069
- files: skills/pixelwright/scripts/pxw.py (`_scaffold`, `SCAFFOLD_SHAPES`, silhouette gate),
  tests/test_pxw.py (walls scaffold test), skills/pixelwright-animate/SKILL.md (Step 2), LEARNINGS.md (L-069),
  .claude-plugin/plugin.json
`"scaffold": "walls"` follows the ground diamond with a pole on every corner and stops at the eaves; both shapes now
lay a plank deck only at every second ledger, with ledgers 9 px and poles about 26 px apart, instead of boarding
the front.

### C-20261030-2 · 2026-10-30 · 0.8.8: review --link
- because: user request (link the pick page to the questions inbox)
- files: skills/pixelwright/scripts/pxw.py (`review_page`, `review` arguments), tests/test_pxw.py (`test_review_links`),
  skills/pixelwright-animate/SKILL.md (review), .claude-plugin/plugin.json
`pxw.py review --link URL LABEL` (repeatable) adds escaped links at the top of the review page.

### C-20261030-1 · 2026-10-30 · 0.8.7: a round scaffold for natural construction
- because: user request, L-068
- files: skills/pixelwright/scripts/pxw.py (`_scaffold`, `fx_site`, `SITE_TIMELINE`, `SITE_KEYS`, silhouette gate),
  tests/test_pxw.py (ring scaffold test), skills/pixelwright-animate/SKILL.md (Step 2), LEARNINGS.md (L-068),
  .claude-plugin/plugin.json
`"scaffold": "ring"` raises a ring of poles, ledgers and front boards first, builds behind it, and takes it down from
the top; the silhouette gate exempts only the scaffold's own pixels.

### C-20261029-1 · 2026-10-29 · 0.8.6: the pit build order for dug sites
- because: L-067
- files: skills/pixelwright/scripts/pxw.py (`fx_site`, `_site_built`, `_site_geometry`, `_nearest_under`, natural plan
  keys, `wood` selector, region `polys`), tests/test_pxw.py (pit test), skills/pixelwright-animate/SKILL.md (Step 2),
  LEARNINGS.md (L-067), .claude-plugin/plugin.json
`"walls": "pit"` digs the floor from the centre, lays the rim round from the front corner, then raises props bottom up,
each prop showing the ground under it until it goes up. A region may list several polygons (`polys`).

### C-20261028-1 · 2026-10-28 · 0.8.5: chimneys on the roof stay in the roof polygon
- because: L-066 (refines L-056)
- files: LEARNINGS.md (L-056 rule, L-066), skills/pixelwright/scripts/pxw.py (VERSION), .claude-plugin/plugin.json
Docs only: notch a chimney out of the roof only when it reaches the ground.

### C-20261026-2 · 2026-10-26 · 0.8.4: moving pixels no longer fail the flicker cap; fog and report caveats
- because: user request; wiki findings 10 to 12 in ai-docs/notes/2026-10-24-github-wiki.md
- files: skills/pixelwright/scripts/pxw.py (_pixel_moves, gates, VERSION), .claude-plugin/plugin.json,
  tests/test_pxw.py (TestRound2Gates), tests/test_make.py (TestRound2),
  skills/pixelwright-animate/SKILL.md (Step 3), skills/pixelwright-animate/references/timing-and-gates.md (Gates),
  skills/pixelwright-make/references/recipe.md (fog), ai-docs/
- Intentional report bug fix: the flicker check matches a travelling pixel across three frames even when it
  moves more than 1 px per frame. It allows a 1 px difference between incoming and outgoing steps; over clear
  sky it matches alpha, so a spark may change colour, and over opaque art it matches RGBA. `flicker_pixels`
  and `flicker_at` may shrink, and an animation capped with `max_flicker_pixels` may now pass. Unmatched motion
  can still count. No effect or make step changes; image bytes stay the same.
- `flicker_at` is documented as up to 8 unique `[x, y]` pairs in row order, without frame indices. Fog advice
  now warns that a high amount with a sparse palette can flatten a sprite to one colour while every gate
  passes. This is a caveat, with a regression fixture, rather than a new gate or a changed default.

### C-20261026-1 · 2026-10-26 · 0.8.3: log walls and plank roofs in natural plans; L-065
- because: L-065 (L-056 superseded for log-and-plank buildings)
- files: skills/pixelwright/scripts/pxw.py (SITE_TIMELINE, _site_geometry, _laid, _site_built, _site_items, fx_site,
  SITE_KEYS, _assemble_natural, VERSION), tests/test_pxw.py (sheet, cabin, built,
  test_natural_logs_lay_whole_courses_and_boards_from_the_front), skills/pixelwright-animate/SKILL.md (Step 2),
  skills/pixelwright-animate/references/effects.md (site row, Patterns), LEARNINGS.md (L-056 status, L-065),
  ai-docs/log.md, .claude-plugin/plugin.json
- A natural plan takes `"walls": "logs"` (`course` px: whole courses, the faces in turn, each log from the front
  corner out, the gable the same way, no corner posts or plates) and `"roofOrder": "boards"` (`board` px: boards side
  by side from the front rake, each whole from eave to ridge). Plans without them are unchanged.

### C-20261025-5 · 2026-10-25 · 0.8.2: open-sided buildings take the ordinary natural plan; L-064
- because: L-064 (and L-059 confirmed twice more)
- files: LEARNINGS.md (L-059 status, L-064), skills/pixelwright-animate/SKILL.md (Step 2: frames),
  ai-docs/log.md, skills/pixelwright/scripts/pxw.py (VERSION), .claude-plugin/plugin.json
- Docs only: the skill no longer suggests a posts-only reading for open-sided sheds; four of them passed every gate
  with the plain natural plan.

### C-20261025-4 · 2026-10-25 · 0.8.1: flicker-pixel and uneven-cadence reports, pixel-perfect arcs, timing rules from the books; L-063
- because: R-20261025-1 (R-P10 confirmed by Silber section 8.3 and Azzi p. 199; cadence from Computer Graphics:
  Principles and Practice section 18.2), L-063
- files: skills/pixelwright/scripts/pxw.py (gates, fx_arc, _pixel_perfect, VERSION), skills/pixelwright-animate/SKILL.md
  (Step 3), skills/pixelwright-animate/references/timing-and-gates.md (Timing),
  skills/pixelwright-animate/references/effects.md (arc row, Patterns), tests/test_pxw.py (TestRound2Gates),
  LEARNINGS.md (L-063), ai-docs/notes/2026-10-25-books-round2.md, .claude-plugin/plugin.json
- `gates.json` gains `flicker_pixels` (with `flicker_at`) and, when it applies, `cadence_uneven`; both are reported,
  not failed, unless a brief sets `max_flicker_pixels`. `arc` gains `perfect` (clean one-pixel bolts). Sheets and
  frames are byte-identical to 0.8.0 (the arc default was checked on 20 seeds). Timing rules: pop rows 2-3 px,
  faces out of shimmer, 3-frame loops, favour keys, steady steps; use-animation and effect beats in Patterns.

### C-20261025-3 · 2026-10-25 · 0.8.0: grid test against chance, enclosed holes, linear-light dither with a contrast cap, swap, pixel-perfect corners, fog, box downscale; L-061, L-062, R-20261025-1
- because: R-20261025-1 (three pixel-art books, Gonzalez and Woods, Computer Graphics: Principles and Practice and
  Gambetta, read 2026-10-25), L-061, L-062
- files: skills/pixelwright/scripts/pxw.py (detect_scale, snap_grid, _flood, remove_background, _linear, _nearest,
  quantise, load_palette, fix_corners, run_make, cmd_swap, cmd_palette, cmd_clean, cmd_bg, _downscale,
  _model_frames, usage, VERSION), skills/pixelwright-make/SKILL.md (description, Step 0, Choosing, Step 4,
  Hand-offs), skills/pixelwright-make/references/recipe.md (Recipe, Commands, How each step works, Rules from the
  books), skills/pixelwright-animate/references/effects.md (model_rotate `filter`), tests/test_make.py (TestRound2),
  tests/test_pxw.py (TestDownscale), RESEARCH.md (R-20261025-1), LEARNINGS.md (L-061, L-062),
  ai-docs/notes/2026-10-25-books-round2.md, README.md (Choices made), .claude-plugin/plugin.json
- Behaviour change: `snap` finds no grid where the edges are too few to tell a grid from chance (fewer than 8, or a
  coherence under 2.8/sqrt(edges)); a smooth JPEG render used to snap at scale 17 or 57 into mush. 304 real
  renders give the same scale as before. Everything else is new and opt-in, and default outputs are byte-identical
  (checked against 0.7.3 on random images for every dither pattern and the downscale): `background.holes`,
  `dither.space: linear` and `dither.max_step`, `clean.corners`, `fog`, the `swap` command and model_rotate's
  `filter: box`. The make skill gains the outline-by-background rule, the smallest-feature size rule, no dither on
  sprites that will move, sharing ramp ends before raising the budget, and the mirrored-light caveat.

### C-20261025-2 · 2026-10-25 · 0.7.3: trace natural roofs by hand; desync loops with a random first-frame hold; L-059, L-060
- because: L-059, L-060, L-056 (confirmed again)
- files: LEARNINGS.md (L-056 count, L-059, L-060), skills/pixelwright-animate/SKILL.md (Placement, Guards),
  skills/pixelwright/scripts/pxw.py (VERSION), .claude-plugin/plugin.json
- Docs only: the roof polygon of a natural plan is traced on a grid, not taken from a colour mask, and loops shared
  by many copies are put out of step by a random hold on frame 0 rather than a random start frame.

### C-20261025-1 · 2026-10-25 · 0.7.2: natural construction lines stay inside the finished silhouette; new gate; L-057, L-058
- because: user request (stray construction lines read as visual chatter), L-057, L-058, T-20261025-1
- files: skills/pixelwright/scripts/pxw.py (_site_items clip, _drop_specks, fx_site, SITE_KEYS, gates, VERSION),
  skills/pixelwright-animate/SKILL.md (Placement, Step 3 gates, Guards), skills/pixelwright-animate/references/effects.md
  (site row), tests/test_pxw.py (test_natural_site_lines_stay_inside_the_finished_silhouette), TESTS.md
  (T-20261025-1), LEARNINGS.md (L-057, L-058), .claude-plugin/plugin.json
- Site elements draw only on the part of the finished building that explains them, leftover specks are dropped, and
  a `site` animation now fails when any frame draws where the still is empty (`drawn_outside_silhouette`). `clip:
  false` keeps the old full lines.

### C-20261024-8 · 2026-10-24 · 0.7.1: natural construction needs a roof of a different material than the walls; L-056
- because: L-056
- files: LEARNINGS.md (L-056), skills/pixelwright-animate/SKILL.md (Placement), skills/pixelwright/scripts/pxw.py
  (VERSION), .claude-plugin/plugin.json
- A guard on choosing buildings for a natural plan: trace the eave as a material change at 8x first, and set aside
  buildings whose walls and roof are one material.

### C-20261024-7 · 2026-10-24 · 0.7.0: natural construction (`assemble` plan `"vocabulary": "natural"`, `site` effect); L-055
- because: user request (a construction strip for a painted village building, approved by its owner), L-053, L-055
- files: skills/pixelwright/scripts/pxw.py (fx_site and helpers, _assemble_natural, cmd_assemble, usage, VERSION),
  skills/pixelwright-animate/references/effects.md (effects table, Patterns), skills/pixelwright-animate/SKILL.md
  (Placement), tests/test_pxw.py (test_natural_assemble_builds_up_from_the_ground_and_ends_on_still,
  test_natural_assemble_needs_the_geometry), TESTS.md (T-20261024-5), LEARNINGS.md (L-055), .claude-plugin/plugin.json
- A second construction vocabulary beside crane, drone and trolley: a timber-framed building raised on site from its
  ground diamond, ported from a project script whose 30-frame strip it reproduces byte for byte. Site colours fall
  back to the whole still's when a material (grey stone) is absent, instead of invented greys.

### C-20261024-6 · 2026-10-24 · Eval case outcome-make-3 (a real model render); outcome-make-1 copies only its input; no version change
- because: T-20261024-4, L-049, L-054
- files: evals/evals.json (outcome-make-1 prompt and files, outcome-make-3), evals/fixtures/outcome1_fixture.py,
  evals/fixtures/outcome3_fixture.py, evals/check_make_real.py, tests/test_make.py
  (test_real_model_render_comes_back_exactly), TESTS.md (T-20261024-4), LEARNINGS.md (L-054)
- outcome-make-3 is a Z-Image img2img render with the model's own shading and no stated size; make recovers it
  exactly, and so does a plain script, so it serves as a regression case, not a value case. outcome-make-1 now
  writes its input from embedded bytes instead of copying make_render.py and its checker into the run.

### C-20261024-5 · 2026-10-24 · 0.6.3: review items for paintings (`display: full`) and context cards (`kind: info`); L-052, L-053
- because: L-052 (ported from spritewright 0.5.1, which shipped after the fork), L-053
- files: skills/pixelwright/scripts/pxw.py (review_page, VERSION), skills/pixelwright-animate/references/brief.md
  (Review extra), tests/test_pxw.py (test_review_full_size_and_info_items), LEARNINGS.md (L-052, L-053),
  .claude-plugin/plugin.json
- A review item with `"display": "full"` shows its images at their own resolution, smoothly scaled, instead of the
  sprite's 3x pixel zoom; `"kind": "info"` shows text and images with a note and no buttons. Sprite items are
  unchanged.

### C-20261024-4 · 2026-10-24 · Eval case outcome-make-2 (fractional scale, palette from a set); no version change
- because: T-20261024-2 (outcome-make-1 too easy), T-20261024-3, L-049
- files: evals/evals.json (outcome-make-2), evals/fixtures/make_render_hard.py (builder, holds the truth),
  evals/fixtures/outcome2_fixture.py (the only file copied into a run), evals/check_make_hard.py, LEARNINGS.md
  (L-049), TESTS.md (T-20261024-3)
- A harder outcome case with a checker drawn in code. It still does not separate the arms (3/3 both); recorded as
  such, and the next case should use a real render.

### C-20261024-3 · 2026-10-24 · 0.6.2: a missing input prints a JSON error; `find_aw` reads `CLAUDE_CONFIG_DIR`; wiki-survey doc fixes
- because: user request (the wiki survey's open items 3, 4, 7 and 8 and the `find_aw` finding in
  ai-docs/notes/2026-10-24-github-wiki.md)
- files: skills/pixelwright/scripts/pxw.py (main, find_aw, VERSION, docstring), tests/test_make.py (TestErrors),
  skills/*/SKILL.md and AGENTS.md (the JSON-output sentence names argparse's usage text), pixelwright-make
  references/recipe.md (`--root` has no fallback; a written `clean` replaces the default), CHANGELOG (the 0.4.4
  entry's duplicate ID is now C-20261023-12), .claude-plugin/plugin.json
- A missing or unreadable input printed a traceback; it now prints `ok: false` with the error and exits 1. The make
  gate finds artwright in a `CLAUDE_CONFIG_DIR` install before `~/.claude`. Needs artwright 0.4.2 for an outlined
  sprite on transparent black to pass without `--scale`.

### C-20261024-2 · 2026-10-24 · 0.6.1: the make gate tells artwright the output is native (`--scale 1`)
- because: L-048, T-20261024-2
- files: skills/pixelwright/scripts/pxw.py (aw_pixel, VERSION), tests/test_make.py
  (test_artwright_is_told_the_output_is_native), LEARNINGS.md (L-048), TESTS.md (T-20261024-2),
  .claude-plugin/plugin.json; docs: pixelwright-make/SKILL.md (the .gpl holds the colours used; coherence can be
  absent), animate references (checked against sw.py), CHANGELOG (23 make tests), a project name generalised in
  CHANGELOG and LEARNINGS (wiki survey findings)
- On a small sprite artwright fitted a false grid and failed a make that matched its source pixel for pixel. Output
  pixels are unchanged; only the verdict differs. Needs artwright 0.4.1 for native shading ramps to pass as well.

### C-20261024-1 · 2026-10-24 · 0.6.0: spritewright becomes pixelwright; pixel creation (make) added
- because: user request (2026-10-24: "expand spritewright to handle pixel art as well as animation", released
  publicly as pixelwright; own plugin, `pxw.py` with an `sw.py` shim, own numpy grid snap), R-20261024-1
- files: skills/pixelwright/ (new hub SKILL.md; scripts/pxw.py, moved from skills/spritewright/scripts/sw.py),
  skills/pixelwright-make/ (new SKILL.md, references/recipe.md), skills/pixelwright-animate/ (the old spritewright
  skill renamed: name, description, Script line, `pxw.py` in the body and references; scripts/sw.py shim),
  tests/test_pxw.py (moved from test_sw.py, imports pxw), tests/test_make.py (new, 23 tests), tests/check_skills.py
  (pxw.py version, banner exemption), evals (make cases, make_render.py fixture, check_make_outcome.py),
  README.md, AGENTS.md, SECURITY.md, RESEARCH.md, evergreen.json, .claude-plugin/plugin.json, CI workflow
- New `pxw.py` commands: `make` (recipe pipeline with gates and artwright's `aw.py pixel`), `snap`, `bg`, `palette`,
  `clean`, `crop`, `tile`, `palettes`. Animation effects are byte-identical: the 32 frame builds of the animation
  test suite hash the same before and after the move. `PIXELWRIGHT_AW` is read, then `SPRITEWRIGHT_AW`.

### C-20261023-11 · 2026-10-23 · 0.5.0: `model_rotate` effect, `model` regions, `plane` on `rotate`; L-041 to L-043
- because: L-041, L-042, L-043, user request (port a game project's waterwheel prototype into spritewright)
- files: skills/spritewright/scripts/sw.py (fx_model_rotate and helpers, Sprite.region_mask, fx_rotate, gates,
  cmd_frames, VERSION), references/effects.md (table, Model rotate), references/brief.md (regions), SKILL.md (Parts
  from a 3D render), tests/test_sw.py (TestModelRotate, TestRotatePlane), LEARNINGS.md (L-041 to L-043),
  README.md (effect list), .claude-plugin/plugin.json
- `model_rotate` turns a painted part from a 3D render's ID and 16-bit pos passes, folding colours into one
  symmetry sector so the loop closes; output goes through the normal palette snap and gates, and render-size frames
  are written beside the sheet. A region can come from the ID pass (`model`). `rotate` takes an optional `plane`
  (T = A R A^-1). Reading the pos TIFF needs `tifffile`, imported only by this effect; nearest-point lookup and the
  image filters are numpy, so the core still needs only numpy and Pillow. Existing effects are byte-identical
  (`rotate` without `plane` keeps its old code path).

### C-20261023-10 · 2026-10-23 · Guard for a part going into an opening; L-039, L-037 recurrence
- because: L-039, L-037
- files: SKILL.md (Guards), LEARNINGS.md (L-039 new; L-037 evidence and helpful count)
- One Guards line from the Mine round 2: a part going into an opening moves on the track's axis, is clipped
  by the opening and darkened with depth, with a short wait inside.

### C-20261023-9 · 2026-10-23 · Guards for solid parts and small parts; L-037, L-038
- because: L-037, L-038
- files: SKILL.md (Guards), LEARNINGS.md (L-037, L-038; L-032 to L-036 redated to 2026-10-23, the day they were
  written)
- Two Guards lines from the batch 2 drafts: cut a solid object with a polygon minus the background, and read
  a 12x mask overlay before choosing rotate, shift or bend for a small part.

### C-20261023-12 · 2026-10-24 · 0.4.4: `external` keeps soft alpha with `soft: "keep"`; L-034, L-035
- because: L-034, L-035, user request (the art lead's batch 1 note on the Smoking Hut: "smoke still looks
  crappy")
- files: skills/spritewright/scripts/sw.py (fx_external, VERSION), references/effects.md (External),
  tests/test_sw.py (external soft keep), SKILL.md (Guards), LEARNINGS.md (L-034, L-035), .claude-plugin/plugin.json
- `external` hardened alpha at 128, so rising smoke pasted over clear sky became a hard cutout; `soft: "keep"` takes
  the sheet's alpha as it is. Without the flag nothing changes.

### C-20261023-8 · 2026-10-23 · 0.4.3: `behind: "grow"` texture-synthesis fill; L-030, L-031
- because: L-030, L-031, user request (the art lead's round 4 note on the Quarry: "the dirt it was on
  doesn't quite look like it blends in with the rest of the dirt")
- files: skills/spritewright/scripts/sw.py (_grow_fill, _behind, VERSION), references/effects.md (table, behind
  paragraph), tests/test_sw.py (behind grow), LEARNINGS.md (L-027 status, L-030, L-031), .claude-plugin/plugin.json
- A moved part's hole can now be filled with ground grown from the pixels around it (Efros-Leung, seeded, cached per
  part), for any effect that uses `behind`. Other modes are unchanged.

### C-20261023-7 · 2026-10-23 · 0.4.2: `bands` effect; `soft: "over"` on `shift` and `bend`; L-026 to L-029
- because: L-026, L-027, L-028, L-029, user request (the art lead's round 3 notes on the pilot: "imagine the
  blue cloth wraps around the loom and moves over it", "a little ghosting on the one to the left")
- files: skills/spritewright/scripts/sw.py (fx_bands, _place, fx_shift, fx_bend, EFFECTS, VERSION),
  references/effects.md (table), SKILL.md (description), tests/test_sw.py (bands, soft over), LEARNINGS.md,
  .claude-plugin/plugin.json
- `bands` moves soft brightness lines along a direction at sub-pixel speed and loops exactly at k = 1, so a painted
  cloth or belt can travel one way without a periodic texture. `soft: "over"` composites a moved part's
  semi-transparent pixels over what is under them. Without the new option, `shift` and `bend` are byte-identical.

### C-20261023-6 · 2026-10-23 · 0.4.1: `brighten` hotspot falloff; `review` refuses a busy port; L-023 to L-025
- because: L-023, L-024, L-025, user request (the art lead's round 2 notes on the pilot: "the hottest part
  of the oven is in the back ... the source of the rest of the reflected light")
- files: skills/spritewright/scripts/sw.py (fx_brighten, cmd_review, VERSION), references/effects.md (table),
  tests/test_sw.py (hotspot, busy port), LEARNINGS.md, .claude-plugin/plugin.json
- `brighten` takes an optional `hotspot`, `radius`, `floor` and `coreTint`, so light has a source and falls off;
  without them it is byte-identical. `review` binds its port exclusively and fails with a clear error when the port
  is taken, instead of silently sharing it with an older page on Windows.

### C-20261023-5 · 2026-10-23 · 0.4.0: `bend` and `brighten` effects, `behind: nearest`; L-017, L-019 to L-022
- because: L-017, user request (the art lead's notes on the pilot page: "intensify the inside of the oven",
  Weaver cloth sway approved)
- files: skills/spritewright/scripts/sw.py (fx_bend, fx_brighten, _behind nearest, EFFECTS, VERSION),
  references/effects.md (table, behind note), SKILL.md (description), tests/test_sw.py, LEARNINGS.md,
  .claude-plugin/plugin.json
- `brighten` multiplies a region's own colours (warm-weighted per channel) so painted fire glows without the
  flattening `pulse` causes; `bend` sways a hanging part about its anchor row; `behind: nearest` fills a vacated
  pixel from its row neighbour when there is no plate. Existing effects are byte-identical.

### C-20261023-4 · 2026-10-23 · 0.3.0: machine dust, ragged eased welds, drone trails; `arc`, `drone`, `cart` effects; L-008, L-009
- because: L-008, L-009, user request (Mark's redo notes on a game project's batch 1 page)
- files: skills/spritewright/scripts/sw.py (fx_assemble and helpers, cmd_assemble, fx_dust lumpy, fx_arc, fx_drone,
  fx_cart, gates), references/effects.md (table, Patterns), SKILL.md (description), tests/test_sw.py, LEARNINGS.md
- `assemble` ramps a power-on `dust` track up from 0 (lumpy) instead of holding it at full strength, draws dust puffs
  where machines work near the ground (gone before the rest frame), welds with a ragged eased front and a gliding
  torch drone, and gives drones motion trails. New effects: `arc` (electric crackle), `drone` (work drone on a path
  with a torch), `cart` (ground cart with a crate).

### C-20261023-3 · 2026-10-23 · 0.2.0: `assemble` effect and command (realistic construction); L-007
- because: L-007, user request (Mark: "closer to real life with drones, cranes and trollies putting everything into place")
- files: skills/spritewright/scripts/sw.py (fx_assemble, cmd_assemble, gates allow machine colours),
  skills/spritewright/SKILL.md (Step 2 placement), references/effects.md (table, Patterns), tests/test_sw.py, LEARNINGS.md
- A placement sheet's construction frames now come from a plan of parts, each arriving by crane, drone, trolley,
  telescope, hinge or on-site weld, with the machines drawn in a fixed small palette; anything an earlier track
  draws outside the silhouette waits until the last part is in; `dropTracks` removes a power-on motion the
  assembly replaces. `buildup` stays for compatibility.

### C-20261023-2 · 2026-10-23 · Review page reads older gates files and skips a take's unchanged sheets; L-006
- because: T-20261023-2, user request (move the building pilot's review page onto sw.py)
- files: skills/spritewright/scripts/sw.py (review_items), tests/test_sw.py, LEARNINGS.md
- `review` accepts gates files that say `cardId` and lack `frames`, and leaves out a take's sheet that is byte-identical
  to the base `out/` sheet, so a build take shows only the animation it changed. L-006 (palette snap flattens a pulse;
  give a flare 3 to 4 graded hot colours) was written by an A/B run of the skill and kept: it matches what the run saw.

### C-20261023-1 · 2026-10-23 · Created as an evergreen unit
- because: user request
- files: README.md, RESEARCH.md, LEARNINGS.md, evergreen.json (skills: also TESTS.md and evals/evals.json)
- Initial version. Tier `moderate`, interval 30d. See R-20261023-1 for the research basis; the first test run, for a skill, is logged in TESTS.md.
