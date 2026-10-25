# Tests: pixelwright (formerly spritewright)

Test runs for [README.md](README.md). Cases live in `evals/evals.json`. A failure that taught something is a lesson in [LEARNINGS.md](LEARNINGS.md); a fix it caused is logged in [CHANGELOG.md](CHANGELOG.md) with `because: T-...`; research it triggered is in [RESEARCH.md](RESEARCH.md); counts and the failing list are in `evergreen.json` under `tests`. Rules: MAINTENANCE.md (testing section) and the plugin's `protocol/TESTING.md`.

A test passes on evidence (a tool call in the trace, a file, a marker, a log line), never on the transcript's claim that something was done.

Entry shape: `### T-YYYYMMDD-n · date · harness · env · passed/total`, then one line per failing case (`id · kind · class · what the evidence showed`), then `led to:` (L-, C-, R- ids or none). Newest first. Budget 150 lines; archive older runs to `TESTS-ARCHIVE.md`.

## Runs

### T-20261024-5 · 2026-10-24 · unittest + port check · Windows 11, Python 3.14 · unit 46/46
- `tests/test_pxw.py` 44/44 (two new natural-assemble tests), `tests/test_make.py` OK, `check_skills.py` OK.
- Port check: a 96x96 painted house (30 frames, 12 fps) through `pxw.py assemble` (natural) then `frames`: the sheet
  equals the original project script's strip byte for byte; gates pass, rest frame identical, 0 new colours.
- led to: C-20261024-7, L-055

### T-20261024-4 · 2026-10-24 · real model render (Z-Image img2img on the Mac) + unittest · Windows 11, Python 3.14 · unit 68/68; no A/B run
- Renders: make_render's potion drawn at 58.5x on 1024 px, Z-Image Turbo img2img, seed 11, denoise 0.5, 0.65, 0.75,
  0.85. At 0.5 and 0.65 the model only adds shade columns; 0.75 adds off-grid curved shading inside blocks and moves
  the highlight up one art pixel; 0.85 redraws the sprite (26x16, no truth).
- `pxw.py make` on the 1024 px takes: 0, 0 and 2 pixels off the original potion; the 2 at 0.75 are the highlight the
  model really drew, so the case's truth is the potion with those two pixels pink (checked by eye).
- A plain script (sprite height / 16, sample block centres, nearest palette colour): 0, 2 and 3 off at full size.
  Halved and cropped to fit the repository (outcome3_fixture.py, about 29.25 px per art pixel), the plain script and
  make both recover the 0.75 take exactly. A model with numpy writes that script in a turn or two, so an A/B would
  tie; it was started and stopped before any run finished, to save the cost.
- New case outcome-make-3 (real render, no size given, only the input copied) kept as a regression case for make;
  `tests/test_make.py` `test_real_model_render_comes_back_exactly` runs it. outcome-make-1 now copies only
  `outcome1_fixture.py` (L-049).
- Reading: across fractional scale, a palette spread over a set, and a real model render, nothing yet separates the
  arms on a single sprite. make's measured value is speed (time x0.64, T-20261024-3) and one tested pipeline.
- Owner's ruling (2026-10-24, after this run): make's value as speed and one tested pipeline is enough. The hunt for
  a single case where the baseline fails is closed; batches, a near-background colour and a drifting grid stay unscored
  ideas, to be scored with the plain script first (L-054) if a later change gives a reason.
- led to: L-054, C-20261024-6

### T-20261024-3 · 2026-10-24 · evergreen 0.17.1 worth --ab (claude -p), outcome-make-2 · Windows 11, Opus · outcome 3/3 with vs 3/3 without, twice
- New case outcome-make-2: the 16x16 potion at a fractional 5.5x on a 3 px offset, blurred and noised, with the
  palette spread over three reference sprites. The checker passes `pxw.py make` (scale found 5.507, 0 pixels wrong)
  and fails nearest sampling at 5 or 6, corner sampling at 5.5, and image width / 16.
- First A/B (6 runs, about $1.95): 3/3 vs 3/3. Two baseline runs read the checker, copied in through `files`, whose
  header named the 5.5x scale; the fixture's source held the true sprite (L-049).
- Second A/B with only the input copied (`outcome2_fixture.py` writes it from embedded bytes; the checker is found in
  the suite's home): 3/3 vs 3/3 again, about $1.97; with the plugin cost x0.89, turns x0.87, time x0.64. The baseline
  finds the grid itself ("about 5.53 screen pixels per art pixel" from colour edges). Verdict CUT for this case.
- The `command` evidence graded correctly in every run: the L-040 fix shipped in evergreen 0.17.1 works. The with arm
  wrote nothing into the clone (L-043 not seen).
- Reading: on clean synthetic fixtures the make skill buys speed, not correctness. A case it exists for needs what a
  model cannot see from a clean grid: a real model render (T-20261024-1's Z-Image potion), a grid that wanders across
  the image, or a background close to a sprite colour.
- led to: L-049

### T-20261024-2 · 2026-10-24 · evergreen worth --ab (claude -p), make cases · Windows 11, Opus · action 3/3 with (re-graded) vs 0/3 without; outcome 3/3 vs 3/3 (re-graded)
- 12 runs, about $5.60; cost x1.42, turns x1.21, time x0.6 with the plugin. `pixelwright-make` fired in 6/6 with-arm
  runs and never without. The harness printed "the skill never fired" because the cases are filed under the hub
  `pixelwright`; give make cases `"skill": "pixelwright-make"` before the next A/B.
- action-make-1 · action · harness misgrade + environment · with: all three ran `pxw.py make`; the harness passed one
  and counted two as environment faults because they tried to write a lesson into the plugin's own LEARNINGS.md (the
  with arm loads the live clone with `--plugin-dir`, so the first run's write landed in the repository). Without: 0/3
  by construction (no pxw.py).
- outcome-make-1 · outcome · harness misgrade · reported 0/3 and 0/3; `python evals/check_make_outcome.py .` by hand in
  all six workdirs prints pass (pixel-exact). On this fixture the model does as well without the plugin; the case
  does not separate the arms. A harder value case is owed: a fractional scale, a wandering grid or a set palette the
  model has to infer.
- Real finding: in the with arm `make` reported ok false on a pixel-perfect result (artwright's false grid and ramp
  blends), fixed in 0.6.1 with artwright 0.4.1.
- led to: L-048, C-20261024-2

### T-20261024-1 · 2026-10-24 · unittest + real renders · Windows 11, Python 3.14 · unit 64/64; real renders 2/2 as expected
- `tests/test_pxw.py` 41/41 (animation, unchanged); `tests/test_make.py` 23/23 (new); `tests/check_skills.py` ok once
  the banner exists. The 32 frame builds of the animation suite hash identically before and after the move to pxw.py.
- Real renders (Z-Image Turbo on the Mac, a "32x32 pixel art" prompt, 1024 px): a potion with a visible grid snapped
  at 26.17 px to 39x39 native, made into a 32x32 sprite of 8 colours that artwright calls clean pixel art; a
  treasure chest drawn with smooth curves found no grid (scale 1, coherence under 0.5), which is right: it is a
  painted sprite, and the skill says not to snap it.
- Eval cases added, not yet run with the harness: trigger-make-1/2, decoy-make-1, action-make-1, outcome-make-1.
  `evals/check_make_outcome.py` passes the skill's output and fails a plain nearest downsample (281 stray colours).
- led to: L-046, L-047

### T-20261023-2 · 2026-10-23 · evergreen worth --ab (claude -p) + unittest · Windows 11, Opus · unit 23/23; A/B action 2/3 with vs 0/3 without; outcome 3/3 vs 3/3 (re-graded)
- `tests/test_sw.py`: 23/23 (every effect, every gate fails when its rule breaks, review page, legacy gates files).
  `tests/check_skills.py`: ok. Regression: the 8 pilot sheets reproduce byte for byte.
- A/B, 3 runs per arm, cost x1.71, turns x1.42, time x1.24 with the skill.
- action-1 · action · evidence-is-the-skill's-tool · with 2/3 ran `sw.py frames` and left gates.json (the 3rd built
  the sheet but the evidence regex missed its call); without 0/3 by construction. Measures "used sw.py", not value.
- outcome-1 · outcome · harness misgrade · the harness reported 0/3 and 0/3; `python evals/check_outcome.py .` run by
  hand in all 6 kept workdirs prints pass. True result 3/3 with, 3/3 without: on a 48 px single-glow task the model
  does as well without the skill, at about 60% of the cost.
- Worth verdict printed CUT (+33 points inside a 38-point noise margin, 1.71x cost). It rests on the tautological
  action case and the misgraded outcome; treat it as UNPROVEN. The suite needs a value case the baseline is likely to
  miss: a placement with build-up and power-on, sparks confined to sky, a loop with a seam, a batch reproduced
  byte for byte.
- led to: evergreen L-040 (command evidence misgrade), C-20261023-2

### T-20261023-1 · 2026-10-23 · not yet run · plugin · 0/0
- Suite scaffolded; no run recorded. Write the cases in `evals/evals.json` (at least two trigger prompts, two decoys, one action case with evidence, one outcome case), run the baseline without the skill, then run with it (`evergreen-test`).
- led to: none
