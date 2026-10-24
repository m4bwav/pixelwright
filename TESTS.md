# Tests: pixelwright (formerly spritewright)

Test runs for [README.md](README.md). Cases live in `evals/evals.json`. A failure that taught something is a lesson in [LEARNINGS.md](LEARNINGS.md); a fix it caused is logged in [CHANGELOG.md](CHANGELOG.md) with `because: T-...`; research it triggered is in [RESEARCH.md](RESEARCH.md); counts and the failing list are in `evergreen.json` under `tests`. Rules: MAINTENANCE.md (testing section) and the plugin's `protocol/TESTING.md`.

A test passes on evidence (a tool call in the trace, a file, a marker, a log line), never on the transcript's claim that something was done.

Entry shape: `### T-YYYYMMDD-n · date · harness · env · passed/total`, then one line per failing case (`id · kind · class · what the evidence showed`), then `led to:` (L-, C-, R- ids or none). Newest first. Budget 150 lines; archive older runs to `TESTS-ARCHIVE.md`.

## Runs

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
