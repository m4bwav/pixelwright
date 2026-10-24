# Changelog: pixelwright (formerly spritewright)

Every change to [README.md](README.md) and its companions, newest first, each with the reason. Reasons cite findings in [RESEARCH.md](RESEARCH.md) (`R-`), lessons in [LEARNINGS.md](LEARNINGS.md) (`L-`), and test runs in [TESTS.md](TESTS.md) (`T-`). State in `evergreen.json`. Protocol: MAINTENANCE.md.

Entry shape: `### C-YYYYMMDD-n · date · one-line summary`, then `because:` (IDs or "user request"), `files:` (file and section), and a sentence on what changed. Cite section headings, not line numbers.

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
