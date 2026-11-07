# Learnings: pixelwright (formerly spritewright)

Procedural lessons for [README.md](README.md). Research findings live in [RESEARCH.md](RESEARCH.md); every change is logged in [CHANGELOG.md](CHANGELOG.md); test runs in [TESTS.md](TESTS.md); state in `evergreen.json`. Format and write-time gate: MAINTENANCE.md (LEARNINGS-FORMAT). Promoted and retired entries live in [LEARNINGS-ARCHIVE.md](LEARNINGS-ARCHIVE.md), each with its reason.

Write an entry the moment a real signal happens: a user correction, the same error twice, a discovered workaround, an environment fact, a stated preference, a failed test or a failure in use. Check existing entries first, by meaning (`evergreen.py search "<the lesson>" --kinds learnings` finds near-duplicates in every registered unit): add / update / retire / none. Trigger and Hypothesis are required. Promote after three confirmations; retire when harmful > helpful.

## Active

### L-013 · 2026-10-23 · A spill whose source box equals its region reads as a flat tinted box
- Trigger: launchpad_stage_1 use: an amber `spill` per tower band (region and source both the band rect,
  strength 0.8) drew solid amber rectangles over the lattice.
- Hypothesis: inside the source box the spill is at full strength, so the whole region takes one tint with hard edges.
- Rule: keep a spill's source narrower than its region (the lamp column, not the band) and its strength near
  0.35 on large regions; zoom one frame at 3x before review.
- Evidence: a game project's anim-b5 launchpad_stage_1 use (strength 0.8 boxes, 0.35 glow, both pass the gate)
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-016 · 2026-10-23 · On soft-alpha painted art, a polygon part cuts the rim and `shift` leaves holes
- Trigger: Colony game FishingDock pilot: a polygon around the rowboat, `shift` [0, 1] with `behind: clear`,
  left water showing through along the gunwale (gates all passed, the zoom showed it).
- Hypothesis: the boat's soft top rim lay above the polygon edge; those pixels were never moved, so the cleared
  pixels below them had no source. The gates cannot see this: every changed pixel is inside an alpha region.
- Rule: on painted sprites with partial alpha, make a moving part's mask from the part's alpha connected
  component (flood fill alpha > 0 from inside the part, boxed away from neighbours), and make the shift zone
  that mask plus the travel. A flood fill can cross into a neighbour through soft pixels where they touch (L-019), so clip the mask at every contact and zoom a moved frame at 10x over a flat background before review.
- Evidence: the project's anim-work/pilot/FishingDock (boat-mask.png, boat-zone.png): clean edge, all gates pass
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-022 · 2026-10-23 · Cloth sway on a 48 px/tile painted building cannot reach the visibility bar
- Trigger: Colony game Weaver (the art lead approved "cloths sway from the rail"): `bend` at 2 px, then 3 px plus a
  loom creep, failed `noticeable` twice (peak 1.9% then 3.3% changed, focal 15 to 16 of 40).
- Hypothesis: four cloths of 20 to 60 pixels each, moving 1 to 3 px, change only their side edges; cloth is
  pale against pale straw and timber, so contrast is low too (L-021).
- Rule: a gentle cloth or plant sway is a secondary track, not a building's whole use animation. Pair it with a
  motion that has area or contrast, or ask the owner whether quiet is what they want; do not raise the amplitude
  past what cloth in a draught does.
- Evidence: the project's anim-work/pilot-r2/Weaver (gates.json, both runs); put to the art lead on the round 2 page
- Scope: skill
- Status: active · helpful 0 · harmful 0 · last_confirmed 2026-10-23

### L-027 · 2026-10-23 · Lift what is already painted before composing anything new
- Trigger: the art lead on the Quarry round 3: "instead of putting a new stone on top of the image, move the 4 stone blocks
  ... up and down, more slowly". Round 4's first fill (row-nearest) streaked the sand sideways into a flat olive
  slab, and in the one-block take pulled the old shadow in as a black blob.
- Hypothesis: on painted art an owner reads any added object as foreign however well it is shaded; a lift of the
  still's own pixels cannot be. Ground texture runs in every direction, so a sideways fill smears it, and its
  nearest neighbour may be a shadow.
- Rule: animate an object that is already in the still before composing a new one. For a lift, fill each vacated
  column by mirroring the ground just below the part, shade only that bare strip (0.8 to 0.9) and snap to the
  ground's own colours (saturated, not dark), never the full palette. Slow means holds: 32 f at 8 fps with a long
  rest and an eased lowering. Only if nothing in the still can move, compose a prop in contrasting tones with a
  shadow row and a cast shadow, no closed outline (L-021, L-024), and ask the owner if it sits near the bar.
  Fill: `behind: "grow"` (L-031), not the mirrored strip above.
- Evidence: the project's anim-work/pilot-r4/Quarry (both takes pass, focal 51 to 52)
- Scope: skill (amends L-021 and L-024 for painted art)
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-028 · 2026-10-23 · A moved painted part must take its soft rim along, and the rim must not overwrite
- Trigger: the art lead on the Weaver round 3: "a little ghosting on the one to the left". The curtain's part mask only had
  pixels at alpha 200 or more, so its soft rim stayed put while the cloth swayed. With the rim included, its faint
  hem (alpha 1 to 86) replaced the opaque wall it moved onto and punched holes in it.
- Hypothesis: painted edges are a band of partial alpha; replacing pixels is right only for opaque ones, and behind
  a nearly see-through rim pixel there was air, not the neighbouring wall.
- Rule: grow the part into adjacent semi-transparent pixels; move it with `soft: "over"` (0.4.2) so rim pixels
  composite over what is under them; in the plate, clear the pixels behind rim pixels (alpha < 200) and fill only
  the opaque ones from their neighbours. Dump the alpha rows at the hem for both sway extremes.
- Evidence: the project's anim-work/pilot-r4/Weaver (f04 and f12 hem rows, gates pass);
  tests/test_pxw.py test_soft_over_keeps_a_wall_under_a_moved_soft_rim
- Scope: skill (part of plan hypothesis 7.1)
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-029 · 2026-10-23 · Cloth travelling one way: move the light, not the pixels
- Trigger: the art lead on the Weaver round 3: the blue cloth should wrap around the loom and move over it, not back and
  forth. `scroll` would loop only if the cloth's texture repeated with the scroll period, and painted cloth does not.
- Hypothesis: the eye reads travel from lines moving across a surface; the surface's own shading can stay where it
  is.
- Rule: use `bands` (0.4.2): faint darker weave lines (gain -0.3, period 4, width 1.2) drifting along the cloth, one
  period per loop; give a second region (the drape) the same period and an `origin` so the lines carry over the
  edge. Pair it with a periodic part (the loom head lifting on each pick) for rhythm.
- Evidence: the project's anim-work/pilot-r4/Weaver (32 f, focal 17.8 against the quiet bar she accepted);
  tests/test_pxw.py test_bands_drift_along_dir_and_loop
- Scope: skill
- Status: active · helpful 0 · harmful 0 · last_confirmed 2026-10-23

### L-032 · 2026-10-23 · On fire that is already bright, a white coreTint snaps to a pale grey blotch
- Trigger: Colony game batch 1 Smelter, first draft: `brighten` at gain 1.2 with `coreTint` [1, 1, 1] on mouths that are
  already painted yellow-orange put a pale green-grey blotch at each hotspot.
- Hypothesis: the yellow pixels are near the top of the range, so whitening pushes them past every warm colour in the
  still and the palette lock picks the nearest pale colour it has, which is grey stone or plaster.
- Rule: when the fire is already bright in the still, keep the gain low (about 0.6) and the coreTint warm
  ([1, 0.85, 0.45]); the white core (Bakery, gain 1.5) is for fires painted dark or dull. Zoom on the peak frame
  before anyone sees it: the gates pass either way.
- Evidence: the project's anim-work/batch1/Smelter (make_b1.py smelter())
- Scope: skill
- Status: active · helpful 0 · harmful 0 · last_confirmed 2026-10-23

### L-033 · 2026-10-23 · brighten cannot light an opening painted near-black
- Trigger: Colony game batch 1 Brickworks: the kiln mouth is almost black with a few orange coal pixels; `brighten` failed
  `noticeable` at gain 1.2 and again at 2.5 with a warm coreTint.
- Hypothesis: brighten multiplies, so a near-black pixel stays near-black whatever the gain; only the few coal pixels
  move, too few for the share or focal bar.
- Rule: before briefing a glow, check the opening has painted mid-tones to multiply. A dark one needs new paint (a
  lit keyframe from an edit or inpaint, `external`, tweened) or a different motion; ask the human which.
- Evidence: the project's anim-work/batch1/Brickworks/frames.log
- Scope: skill
- Status: active · helpful 0 · harmful 0 · last_confirmed 2026-10-23

### L-078 · 2026-11-02 · Fill a dark opening by fading its rim inward, not by inventing a back wall
- Trigger: a cold furnace's flat black openings were filled with a painted interior (staggered brick courses, mortar,
  an ash floor). The reviewer said it looked like a bad painting of a wall stuck in the hole; what they wanted was the
  existing arch and jambs carried on into the dark.
- Hypothesis: at sprite scale a drawn back wall reads as a flat surface right behind the opening, so the hole loses its
  depth, and a regular pattern (courses, mortar) looks mechanical next to the painted stone. A gradient from the rim's
  own colours to near black reads as depth with no new detail to judge.
- Rule: for a dark opening (door, kiln or furnace mouth, window, cave), give each dark pixel the colour of the nearest
  rim pixel dimmed by its distance inside (a falloff over most of the opening's half-width, roughly 0.8 at 1 px down to
  under 0.1), a little darker under the top and a little lighter toward the floor, snapped to the still's palette. Add
  no pattern the painting did not already have. Below roughly 14 px across the fade draws puckered rings, so use a 1 px
  reveal in the rim's stone at about half brightness, then a flat dark back from the still's darkest stone, the
  bottom one or two rows slightly lighter as a floor (L-079).
- Evidence: a 96 px furnace with two arched mouths; the brick version was rejected, and the rim fade (10 px falloff)
  read as deep, dark mouths at 1x and 4x.
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-11-02

### L-085 · 2026-11-03 · A catch-all `rest` weld can crash assemble on an empty part
- Trigger: `pxw.py frames` raised IndexError in `_torch` on three buildings.
- Hypothesis: a final `rest` weld step had no pixels left because the other parts already covered the silhouette.
- Rule: drop the catch-all `rest` weld when the other parts cover the silhouette. `pxw.py assemble` reports these as `empty` with `ok: false`; a hand-written track gets the crash. Since 2026-11-05 `frames` draws no machine for an empty step.
- Evidence: all three passed with the empty step skipped; `uncovered_pixels` stayed 0. Reproduced on 0.9.1, 2026-11-05: a second weld step with no pixels left raises the IndexError at `_torch`.
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-11-05

### L-086 · 2026-11-05 · A rect rotate region turns whatever sits behind the wheel
- Trigger: a reviewer rejected a winch wheel because part of the fixed brace turned with it; every gate had passed.
- Hypothesis: `rotate` takes all pixels in its rects, and no gate can tell a wheel from the structure it overlaps.
- Rule: when a rotating part overlaps structure, drop the rotate track and spin a colour-and-radius mask taken from the still, leaving the rest on the plate; fill rim gaps by angle. Zoom into the part across the turn before review.
- Evidence: take 2 kept the brace fixed in a zoomed frame check; reviewer verdict pending.

### L-087 · 2026-11-06 · Soft-edged pixels show the ground when a piece moves onto a heap
- Trigger: a collapse heap kept green flecks after every hole enclosed by the silhouette had been filled, and the flecks survived a burnt recolour.
- Hypothesis: the source still has low-alpha edge pixels. They look solid on the plate, but moved onto other pieces they overwrite an opaque pixel with a see-through one.
- Rule: when a shard leaves its place, drop pixels under half alpha and make the rest opaque. Keep the untouched frame 0 as the still. To tell a colour from a hole, recolour the frame: a real colour changes, the ground does not.
- Evidence: flecks gone on five buildings after this change, checked on the rest frames at 2x; frame 0 still equals the still by script.
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-11-06

### L-088 · 2026-11-06 · Check a strip's last frame against the next strip's first frame
- Trigger: a clear strip ended on an empty plot while three of five construction strips it hands over to opened with a few hundred pixels already drawn, so the join would pop. Each strip passed its own gates.
- Hypothesis: gates look at one strip against its still. A sequence played one after another has joins no single strip's gate can see.
- Rule: when strips play in sequence, read the next strip's first frame and make the earlier strip end on it (`collapse --clear-to`). Compare what shows only: colour under alpha 0 is unseen and a byte compare fails on it.
- Evidence: opaque pixels on the first frame of the construction strips were 151, 165 and 338 on the three that popped and 0 on the other two.
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-11-06
