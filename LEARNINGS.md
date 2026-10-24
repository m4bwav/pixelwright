# Learnings: pixelwright (formerly spritewright)

Procedural lessons for [README.md](README.md). Research findings live in [RESEARCH.md](RESEARCH.md); every change is logged in [CHANGELOG.md](CHANGELOG.md); test runs in [TESTS.md](TESTS.md); state in `evergreen.json`. Format and write-time gate: MAINTENANCE.md (LEARNINGS-FORMAT). Retired entries go to LEARNINGS-ARCHIVE.md with a reason.

Write an entry the moment a real signal happens: a user correction, the same error twice, a discovered workaround, an environment fact, a stated preference, a failed test or a failure in use. Check existing entries first, by meaning (`evergreen.py search "<the lesson>" --kinds learnings` finds near-duplicates in every registered unit): add / update / retire / none. Trigger and Hypothesis are required. Promote after three confirmations; retire when harmful > helpful.

## Active

The first five come from the 2026-10-23 pilot that produced `sw.py` (two buildings, a dense downscaled-render
house style, 128 px stills).

### L-001 · 2026-10-23 · A colour selector alone lights the wrong parts; box it in first
- Trigger: a "warm pixels" rule on a foundry lit its hazard stripes along with the furnace.
- Hypothesis: stripes, rust and lamps share hues; hue alone cannot tell a lamp from paint.
- Rule: every glowing region is a rectangle or polygon around the lit part, narrowed with `select`; never a
  selector over the whole sprite.
- Evidence: pilot foundry brief; `sw.py mask` output read before frames
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-002 · 2026-10-23 · Light is additive; a tint toward a colour turns metal to mud
- Trigger: the first furnace spill blended the metal toward orange and read as a tan smear.
- Hypothesis: real cast light brightens and warms a lit surface; blending toward a flat colour flattens shading.
- Rule: `spill` adds `tint * strength * falloff` to the existing colour, then snaps; do not blend toward a target.
- Evidence: pilot foundry use sheet, before and after
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-003 · 2026-10-23 · Per-pixel random dust reads as TV static
- Trigger: the first placement dust was independent random pixels per frame.
- Hypothesis: the eye reads uncorrelated per-pixel noise as signal noise, not a cloud.
- Rule: particle clouds come from a coarse random grid smoothly upscaled and drifted between frames (`dust`),
  or from a few tracked puffs (`puffs`); never fresh per-pixel noise each frame.
- Evidence: pilot foundry and small_factory place sheets
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-004 · 2026-10-23 · Motion has to be bigger than feels right to read at game zoom
- Trigger: a 9 degree arm dip was invisible at 3x; 13 degrees read.
- Hypothesis: at 1x to 3x a part move of under 2 px at its tip is lost in the still's detail.
- Rule: size moves so the part's far end travels at least 2 to 3 px; check the 4x preview and the gate's
  `noticeable` before review.
- Evidence: pilot small_factory use sheet
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-005 · 2026-10-23 · Pick particle sources with sky above them inside the frame
- Trigger: a chimney touched the top edge (y = 0), so smoke could not rise inside the 128 px frame.
- Hypothesis: sheets keep the still's frame size; anything above the top edge is cut.
- Rule: before choosing a smoke or spark source, check the grid for at least 8 px of transparent sky above it;
  otherwise use another vent.
- Evidence: pilot small_factory (steam from the left tank vent instead)
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-006 · 2026-10-23 · Palette snap flattens a pulse into two or three flat steps
- Trigger: a 10-frame furnace flare with only the still's oranges plus two hot colours came out as 3 visible
  levels (peak held 4 frames, settle in one jump) and never reached white at default `strength` 0.8.
- Hypothesis: `pulse` output snaps to the region ramp, so the curve has only as many visible steps as the ramp
  has colours between rest and hot.
- Rule: for a flare, set `strength` 1.0 and put 3 to 4 graded hot colours in `extraColours` (rest orange to
  near-white); read `focal_mean_abs_luma_delta` for distinct steps before review.
- Evidence: eval fixture machine.png use sheet, before and after (written by an A/B run, T-20261023-2)
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-007 · 2026-10-23 · Construction must look like a real site, not a hologram
- Trigger: Mark redid both `buildup` place sheets: "the general effect is cool, but I'm looking more hard scifi,
  more like it gets unfolded and erected"; then "closer to real life with drone, cranes and trollies putting
  everything into place, some parts might unfold from others ... some parts prepared beforehand in a factory and
  others built on site".
- Hypothesis: a glowing seam with a dotted outline reads as sci-fi fabrication; a hard sci-fi colony wants
  believable logistics: prefab modules delivered and set down, parts telescoping and unfolding, welding on site.
- Rule: make placement construction with `assemble` (crane, drone, trolley, telescope, hinge, weld). Not `buildup`.
  Draw machines (cable, spreader bar, drones) light enough to read against a dark sky (cable grey 124, not black).
- Evidence: a game project's foundry and small_factory place sheets, 2026-10-23
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-008 · 2026-10-23 · A power-on dust track held at full strength reads as a hard fog stripe during construction
- Trigger: Mark redid 4 place sheets: "the fog gets layered on in the beginning like a sharp rectangle and then it
  disperses at the end ... fog could form from the drones flying around, but not as a sharp square that's left to
  right applied"; "the initial stripe at the bottom ... too exactly even".
- Hypothesis: `sw.py assemble` 0.2.0 prefixed every track's curve with its first value, so the "dust settles" track
  stood at full strength from frame 0, and the full-width pad weld swept that haze in as a rectangle in 3 frames.
- Rule: dust in construction comes from the machines (0.3.0: puffs at trolley wheels, the welding torch near the
  ground, drone downwash, touchdowns), the haze ramps up from 0 and is lumpy; split a pad into 2 or 3 plates.
  Machines drawn moving need easing and trails (Mark: "more organic", "give other drones trails").
- Evidence: a game project's anim-b1 picks (crusher, construction_yard, small_factory, foundry place), re-made in anim-b2
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-009 · 2026-10-23 · Machines drawn over a building vanish in the building's own colours
- Trigger: a work drone and a cart over construction_yard's still could not be found even at 6x zoom.
- Hypothesis: MACHINE greys and the accent yellow are the colours these buildings are made of.
- Rule: in a use animation, give a `drone` or `cart` over the building a `machine` livery the still does not use
  (cyan worked), and zoom one frame to check it reads before review.
- Evidence: a game project's construction_yard use (anim-b2)
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-010 · 2026-10-23 · A scroll mask that takes in the wall beside a belt moves the wall
- Trigger: Mark on crusher/use: "the conveyor belt looks a little weird when it moves, part of the wall moves with it."
- Hypothesis: the belt polygon included the vertical wall column at its left end, the tan floor above it and the
  pillar at its right end; `scroll` shifts every masked pixel by `dir`, so those moved too.
- Rule: fit a `scroll` region to the belt only (zoom 12x with a 1 px grid, check each edge), never a loose
  parallelogram around it.
- Evidence: a game project's crusher use, anim-b3 (belt poly [[22,88],[25,88],[44,100],[44,105],[40,105],[22,95]])
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-011 · 2026-10-23 · A cart with no context reads as a stray square; a hinge on a long thin cable reads as a wedge
- Trigger: Mark on construction_yard/use: "The blue square on the bottom seems non sensical." While making
  fuel_cell_bank place, a `hinge` on its long power cable drew a solid dark wedge mid-swing.
- Hypothesis: a cart on the ground line with no door or load source has no story; majority-vote rotation of a
  1 to 2 px curve fills the gaps between its strands.
- Rule: use a `cart` only where it visibly leaves or enters something (a door), in the load's own colours (crate
  brown on a grey chassis on storage_yard); otherwise drop it. Bring a cable or pipe in with `telescope` (dir
  `down`) instead of `hinge`; keep `hinge` for solid arms and beams.
- Evidence: a game project's anim-b3 construction_yard use r2, storage_yard use, fuel_cell_bank place
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-012 · 2026-10-23 · `pulse` cannot make already-bright windows read as brighter
- Trigger: habitat_module use (a window wave) failed the noticeable gate: max 1.7% changed, focal luma 25.
- Hypothesis: the lit windows are near the hot colour already, so the pulse moves them a step at most.
- Rule: for lights that are on at rest, carry the motion with a warm `spill` on the facade around each light group
  (same curve as its pulse); that took habitat_module to 24% changed.
- Evidence: a game project's anim-b3 habitat_module use; anim-b5 launchpad_stage_1 use (2.7% to 25%)
- Limit: spill only reaches the 8% share on a big lit area. basic_lab's six small screens with spill still
  peaked at 6.7% (anim-b5): small lights need a moving part or a larger lit surface to carry the use animation.
- Scope: skill
- Status: active · helpful 2 · harmful 0 · last_confirmed 2026-10-23

### L-013 · 2026-10-23 · A spill whose source box equals its region reads as a flat tinted box
- Trigger: launchpad_stage_1 use: an amber `spill` per tower band (region and source both the band rect,
  strength 0.8) drew solid amber rectangles over the lattice.
- Hypothesis: inside the source box the spill is at full strength, so the whole region takes one tint with hard edges.
- Rule: keep a spill's source narrower than its region (the lamp column, not the band) and its strength near
  0.35 on large regions; zoom one frame at 3x before review.
- Evidence: a game project's anim-b5 launchpad_stage_1 use (strength 0.8 boxes, 0.35 glow, both pass the gate)
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-014 · 2026-10-23 · `rotate` on an opaque part punches transparent holes unless `behind: still`
- Trigger: fuel_processor use: a pressure wheel rotated inside the building failed
  `alpha_changed_outside_alpha_regions` (512, then 66 after a disc polygon); the still is fully opaque there.
- Hypothesis: rotate's default `behind` clears the part's pixels that no rotated source pixel lands on, so the
  rim of a rect or polygon part goes transparent.
- Rule: for a part set into the building (wheel, dish face, fan), give the track `"behind": "still"` and a disc
  polygon centred on the real hub; `alpha: true` only for parts against the sky. Also mark `alpha: true` on a
  `shift` or `scroll` zone whose source has semi-transparent pixels (regolith_extractor head).
- Evidence: a game project's anim-b5 fuel_processor use, regolith_extractor use, probe_lab dish
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-015 · 2026-10-23 · `shift` after `scroll` on the same pixels wipes the scroll (both sample the still)
- Trigger: Mark on mine_common use: "make the drill bit spin". The brief already had a spiral `scroll` and a
  2 px drill `shift`; the spin was only visible in the 3 frames where the shift was 0.
- Hypothesis: `fx_shift`, `fx_scroll` and `fx_rotate` all copy from `s.still`, not from the frame being built, so
  the last of two moving effects on overlapping pixels wins outright.
- Rule: never stack two moving effects on the same pixels. Compose them yourself into a frames sheet (scroll the
  bit, then move the drill block, per frame) and paste it with `external` on a zone that covers the travel
  (the project's `make_b6.py`). An arm carrying a hanging load works as `rotate` on the
  arm plus `shift` on the load by the wrist's offset at full angle, same curve (basic_lab: pivot at the
  shoulder, -22 degrees, load `by` [0.1, -7.4]).
- Evidence: a game project's anim-b6 mine_common use (spin visible in all 10 frames), basic_lab use (gate now
  passes noticeable, 9.4% peak vs 6.7%)
- Scope: skill (candidate fix: let shift/scroll/rotate read the current frame, or a `compose` effect)
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-016 · 2026-10-23 · On soft-alpha painted art, a polygon part cuts the rim and `shift` leaves holes
- Trigger: Colony game FishingDock pilot: a polygon around the rowboat, `shift` [0, 1] with `behind: clear`,
  left water showing through along the gunwale (gates all passed, the zoom showed it).
- Hypothesis: the boat's soft top rim lay above the polygon edge; those pixels were never moved, so the cleared
  pixels below them had no source. The gates cannot see this: every changed pixel is inside an alpha region.
- Rule: on painted sprites with partial alpha, make a moving part's mask from the part's alpha connected
  component (flood fill alpha > 0 from inside the part, boxed away from neighbours), and make the shift zone
  that mask plus the travel. Zoom a moved frame at 10x over a flat background before review.
- Evidence: the project's anim-work/pilot/FishingDock (boat-mask.png, boat-zone.png): clean edge, all gates pass
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-017 · 2026-10-23 · `pulse` on a painted flame flattens it past strength about 0.4
- Trigger: Colony game Bakery pilot: fire `pulse` toward [255, 236, 170] at strength 0.7 turned the flame a
  flat pale peach at the peak frame and lost its yellow core.
- Hypothesis: pulse lerps every pixel toward one colour, so at high strength all pixels converge and the painted
  variation that makes it read as fire disappears; snapping to the warm ramp then picks the same few colours.
- Rule: on painted art keep `pulse` strength at or under 0.4 with `hot` near the flame's own brightest colour
  (Bakery: [255, 214, 110]); carry visibility with a second weak track on the surface around it. A brightness
  curve that keeps relative variation (multiply, not lerp) is the real fix: plan section 7.3.
- Evidence: the project's anim-work/pilot/Bakery/zoom.png (texture kept, all gates pass, peak share 9.8%)
- Scope: skill (fixed in 0.4.0: `brighten`, see L-020)
- Status: active · helpful 2 · harmful 0 · last_confirmed 2026-10-23

### L-018 · 2026-10-23 · A thin part cannot carry a use animation at any angle
- Trigger: Colony game Quarry pilot: the wooden derrick (126 px of the sprite) rotated 3 then 8 degrees
  failed `noticeable` both times (peak 1.5%, then 2.2% changed).
- Hypothesis: a thin line moves few pixels however far it swings, and a bigger swing would bend a real derrick
  past what it can do.
- Rule: before briefing, count the part's pixels; under about 3% of the opaque pixels, pick another part or
  building (or add a second track with area) rather than asking for a larger angle or loosening the gate.
- Evidence: the project's anim-work/pilot/Quarry (gates.json both runs)
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-019 · 2026-10-23 · An alpha-component mask picks up a neighbour's soft edge where they touch
- Trigger: the art lead on the FishingDock pilot: "a little bit of the dock comes off in the animation". The boat's
  alpha component (L-016) had joined the dock through three semi-transparent edge pixels at the bow.
- Hypothesis: soft edges of two painted objects overlap by a pixel or two, so a flood fill crosses between them;
  the gates cannot see it because every changed pixel is inside the mask.
- Rule: after building a part mask from an alpha component, zoom the places where the part touches another object
  and clip the mask there (FishingDock: x < 38). Check the moved frame at 10x over a flat colour at every contact.
- Evidence: the project's anim-work/pilot-r2/FishingDock (dock corner intact in all 16 frames, gates pass)
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-020 · 2026-10-23 · Painted fire reads as glowing when its own colours are multiplied, not lerped
- Trigger: the art lead on the Bakery pilot: "we want the action to be more visible. Intensify the inside of the oven".
  The round 1 `pulse` was capped at 0.4 to keep texture (L-017), so it stayed faint.
- Hypothesis: multiplying each pixel (red most, blue least) lifts the whole oven toward yellow-orange while
  keeping the darker strokes darker, so texture survives at a strength `pulse` cannot reach.
- Rule: for fire or lamps in painted art use `brighten` (gain about 0.9, tint [1, 0.75, 0.4]) on the whole
  interior, masked by hue (red > blue + 30) inside an ellipse, plus a weak `brighten` on the rim; not `pulse`.
- Evidence: the project's anim-work/pilot-r2/Bakery (peak focal change 44.2, all gates pass, zoom shows strokes)
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-021 · 2026-10-23 · A small moving prop is seen by contrast with what is behind it, not by size
- Trigger: Colony game Quarry round 2 (the art lead: raise and lower the load of stones). A load cut from grey rim
  stones over the grey pit wall failed `noticeable` (focal 34.6) and was hard to see in the zoom.
- Hypothesis: the focal brightness gate and the eye both measure contrast; same-tone pixels moving over same-tone
  pixels change almost nothing.
- Rule: build a hauled or carried prop from the still's pixels of a tone that contrasts with its path (pale cut
  blocks over the dark wall) and give it a 1 px outline in a dark colour from the still (the rope). Compose it as
  an `external` sheet with its rope (L-015).
- Evidence: the project's anim-work/pilot-r2/Quarry/make_quarry.py (pale sling: focal 43.9, passes)
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

### L-023 · 2026-10-23 · Painted light needs a source: a uniform brighten reads as a lit window, not a fire
- Trigger: the art lead on the Bakery round 2 (whole oven interior multiplied evenly): "the hottest part of the oven is in
  the back, so that is where it should be more white-hot and also the source of the rest of the reflected light in
  the walls and base of the oven". She almost preferred the fainter round 1.
- Hypothesis: real fire light has one hot point and falls off over the surfaces around it; an even gain lifts the
  front floor as much as the fire, so contrast rises but the light has no direction.
- Rule: brighten a fire or lamp with `hotspot` at the deepest, hottest point, `radius` about the opening's size,
  `floor` 0.25 so the far walls still catch some light, and `coreTint` [1, 1, 1] so only the core goes white-hot.
  Include the dark interior pixels in the mask: they are the walls that reflect.
- Evidence: the project's anim-work/pilot-r3/Bakery (gain 1.5, hotspot [75, 57], radius 10: focal 42.8, all gates
  pass; gain 1.1 radius 9 reached only 30); tests/test_sw.py test_brighten_hotspot_is_hottest_and_whitest_at_its_centre
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-024 · 2026-10-23 · An outline around a moved prop reads as a sticker on painted art
- Trigger: the art lead on the Quarry round 2: "the square border around the stone looks silly and doesn't appear in the
  same style". The 1 px dark rope outline (L-021) was what made the load pass `noticeable`.
- Hypothesis: painted objects in her art are bounded by tone changes and soft shadow, never by a line; a closed
  outline is a pixel-art convention. Without it, a pale prop over pale ground loses most of its contrast.
- Rule: on painted art give a moving prop an irregular silhouette, a shadow row on its underside chosen from the
  still's darker tones of the same material, and a cast shadow on the ground beneath it (the ground's own pixels
  darkened, growing as it nears the ground); no outline. Expect it to sit near the visibility bar and ask the owner
  rather than adding the outline back.
- Evidence: the project's anim-work/pilot-r3/Quarry/make_quarry.py (focal 33.4 without, 36.3 with the cast shadow;
  fails twice, put to the art lead on the round 3 page)
- Scope: skill (amends L-021 for painted art)
- Status: active · helpful 0 · harmful 0 · last_confirmed 2026-10-23

### L-025 · 2026-10-23 · Two review servers can share one port on Windows, and the human sees the older page
- Trigger: stopping the round 2 page on 8766 found two `sw.py review` processes listening there (round 1's page
  had never stopped). Either could have answered the art lead's clicks.
- Hypothesis: `http.server` sets `allow_reuse_address`, and on Windows SO_REUSEADDR lets a second socket bind a
  port that is already listening, with no error.
- Rule: `review` binds exclusively (fixed in 0.4.1) and fails when the port is taken. Before serving a new round,
  list listeners on the port and check each one's command line; stop old rounds by PID.
- Evidence: netstat on 127.0.0.1:8766 (PIDs 81468 pilot-review, 88008 pilot-r2); tests/test_sw.py
  test_review_refuses_a_busy_port
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-026 · 2026-10-23 · A fire's glow must stop short of the oven mouth's rim
- Trigger: the art lead on the Bakery round 3: "the fire highlights on the edge are a little too bright for the edge of the
  stove". An ellipse mask took in the pale stone sill, and the hotspot (radius 10, floor 0.25) lit the fire pixels at
  the mouth by +130 to +170.
- Hypothesis: real oven light is strongest at the back and the mouth's rim stays near its painted tone; an ellipse
  catches stone, and a long falloff carries core-strength light to the edge.
- Rule: mask a fire by what it is (saturated pixels plus the dark inner walls) inside the ellipse; split off a 2 px
  edge ring at low gain (0.25); set the hotspot radius to about the distance from the back to the mouth minus 2,
  with floor 0.15; keep the outer stone lip at gain 0.12 or less. Check the peak frame per pixel at the rim.
- Evidence: the project's anim-work/pilot-r4/make_r4.py bakery() (focal 40.5, all gates pass, rim near still tone)
- Scope: skill (amends L-023)
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-027 · 2026-10-23 · Lift what is already painted, and fill the bare ground from just below it
- Trigger: the art lead on the Quarry round 3: "instead of putting a new stone on top of the image, move the 4 stone blocks
  ... up and down, more slowly". Round 4's first fill (row-nearest) streaked the sand sideways into a flat olive
  slab, and in the one-block take pulled the old shadow in as a black blob.
- Hypothesis: on painted art an owner reads any added object as foreign however well it is shaded; a lift of the
  still's own pixels cannot be. Ground texture runs in every direction, so a sideways fill smears it, and its
  nearest neighbour may be a shadow.
- Rule: animate an object that is already in the still before composing a new one. For a lift, fill each vacated
  column by mirroring the ground just below the part, shade only that bare strip (0.8 to 0.9) and snap to the
  ground's own colours (saturated, not dark), never the full palette. Slow means holds: 32 f at 8 fps with a long
  rest and an eased lowering.
- Evidence: the project's anim-work/pilot-r4/Quarry (both takes pass, focal 51 to 52)
- Scope: skill (amends L-021 and L-024 for painted art)
- Status: active, fill rule superseded by L-031 · helpful 1 · harmful 0 · last_confirmed 2026-10-23

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
  tests/test_sw.py test_soft_over_keeps_a_wall_under_a_moved_soft_rim
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
  tests/test_sw.py test_bands_drift_along_dir_and_loop
- Scope: skill
- Status: active · helpful 0 · harmful 0 · last_confirmed 2026-10-23

### L-030 · 2026-10-23 · On painted art, a polygon around an object also lifts the ground it stands on
- Trigger: the art lead on the Quarry round 4: "there's a little bit of dirt attached to the bottom of the squares when they
  pull up". The part was a polygon around the four blocks; painted edges are soft, so the polygon took a rim of sand
  with them. Her drop of the one-block take ("looks weird because its half the square") was the same cause: the
  polygon cut a block where the eye sees one object.
- Hypothesis: in a painted still the object's boundary is where its colour changes, not a line; any hand-drawn
  shape either cuts the object or takes ground with it.
- Rule: inside a loose polygon, keep only pixels of the object's own colour family (for stone on sand: red minus
  blue below about 52 where the sand sits at 55 and up), keep the largest component and fill pinholes (three or four
  stone neighbours). Lift a whole object as the eye groups it, never part of one. Check with a magenta overlay of the
  mask on a 10x crop before making frames.
- Evidence: the project's anim-work/pilot-r5/Quarry (stone-mask.png, q-r5-look.png; gates pass, focal 55.5)
- Scope: skill
- Status: active · helpful 0 · harmful 0 · last_confirmed 2026-10-23

### L-031 · 2026-10-23 · Grow the bare ground from the texture around it, not from one row or column
- Trigger: the art lead on the Quarry round 4: "the dirt it was on doesn't quite look like it blends in with the rest of the
  dirt". L-027's fill mirrored the sand just below each column, so the patch repeated one strip upside down and its
  shading ran the wrong way.
- Hypothesis: painted ground has texture in every direction; a fill that copies along one axis repeats a line the
  eye catches, while a neighbourhood-matched fill continues the brush marks from every side.
- Rule: use `behind: "grow"` (0.4.3): Efros-Leung synthesis from the hole's edge inward, each pixel copied from the
  source pixel whose 5x5 known neighbourhood matches best, random among the closest four, seeded. Limit the sources
  to the ground (`growFrom`, e.g. the warm sand only) so stone or shadow never seeds it. Keep any contact shadow light
  (0.86 to 0.94 of the ground) and on the bare strip only.
- Evidence: the project's anim-work/pilot-r5/Quarry (bare-plate.png); tests/test_sw.py
  test_behind_grow_fills_the_hole_with_the_ground_around_it
- Scope: skill (supersedes L-027's fill rule)
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

### L-034 · 2026-10-23 · Smoke has to travel; bending a painted plume reads as a waving flag
- Trigger: Colony game batch 1 Smoking Hut: the painted plume `bend` about the chimney mouth (amp 3, two periods) passed
  every gate; the art lead: "smoke still looks crappy".
- Hypothesis: a bend keeps the plume one solid shape that wags in place. Real smoke leaves the chimney: puffs break
  off, rise, swell and thin out, so the shape is never the same twice.
- Rule: for smoke or steam, clear the painted plume above the dense part at the mouth and make it travel: the
  project's own smoke strip at an anchor when it has one, or puffs cut from the plume's dense paint rising along the
  plume's own path, fading out (`external` with `soft: "keep"`). Never bend or shift a plume.
- Evidence: the project's anim-work/batch1/picks.json; batch1-r2/make_r2.py
- Scope: skill
- Status: active · helpful 0 · harmful 0 · last_confirmed 2026-10-23

### L-035 · 2026-10-23 · Puffs sampled from a plume's soft edge come out as rings
- Trigger: Colony game batch 1 round 2 Smoking Hut, first rise take: puff discs sampled from the plume's upper curl read
  as faint "C" shaped rings, not puffs; gates passed.
- Hypothesis: the curl's edge pixels are mostly see-through, so a disc mapped onto it is dense in a ring and empty in
  the middle wherever the curl was thin.
- Rule: take the puff texture from the plume's densest opaque paint (here the column over the chimney mouth) and
  multiply its own alpha by the life and edge fall-off; zoom on a frame row before the page.
- Evidence: the project's anim-work/batch1-r2/make_r2.py puff_layer()
- Scope: skill
- Status: active · helpful 0 · harmful 0 · last_confirmed 2026-10-23

### L-036 · 2026-10-23 · Any painted smoke left still reads as frozen, so clear all of it and grow back what it covered
- Trigger: Colony game batch 1 round 2 Smoking Hut: both takes kept the dense painted column over the roof and animated
  only above it; the art lead redid both: "the chimney smoke that is over the roof doesn't animate ... it just sits there".
- Hypothesis: the eye follows smoke down to its source; a static base under moving puffs says "painted on".
- Rule: when animating smoke (or any flow) painted on a still, remove every pixel of it, including where it covers
  opaque art: clear the sky part and grow the covered part back (`behind: grow` style, one source pool per surface,
  e.g. roof tiles above, chimney stone at the mouth), then emit the motion from the true source (the chimney mouth),
  dense and overlapping enough there that the column reads continuous. Draft with puffs too thin at first: radius
  2.7 px and an edge fall-off of 0.4 at the mouth matched the old column's weight at 96 px.
- Evidence: the project's anim-work/batch1-r3/make_r3.py (grow(), stream_take()); batch1-r3/SmokingHut/cleared-still.png
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23 (round 3 `stream` kept: "this one is the best")

### L-037 · 2026-10-23 · A lit face and a shaded face are two colour families: cut the part with a polygon
- Trigger: Colony game batch 2 Mine cart: a warm-colour select took only the cart's lit front face (59 px); its shaded side,
  ore and rim stayed behind, so a shift would have split the cart.
- Hypothesis: painted 3/4 views shade each face of a box-like object differently; any colour or hue select picks one
  face.
- Rule: for a solid object (cart, crate, block), draw a loose polygon around the whole object and subtract only the
  background it sits on by value (here the arch's near-black interior, value < 35), not by colour family. Check it
  on a 12x overlay of the still before making frames.
- Evidence: the project's anim-work/batch2/make_b2.py (mine()); batch2/ov-Mine.png (first mask). Recurred in
  batch2-r2 Sawmill: a tan-or-pale select took only the lit crescent of the log's end, the shaded bark beside it
  stayed, and the shifted crescent floated; a polygon minus the doorway dark (value < 85) moved the whole log
  (batch2-r2/make_r2.py, sawmill()).
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-038 · 2026-10-23 · Pick the effect from a 12x overlay of the part, not from the montage
- Trigger: Colony game batch 2 Sawmill: at 6x the grey part read as a round saw blade, so the first brief spun it;
  the 12x mask overlay showed a long diagonal blade, which a spin would turn into a tumbling smear.
- Hypothesis: at 96 px a 25-pixel part has no reliable silhouette at montage zoom; shading suggests shapes it
  does not have.
- Rule: before choosing `rotate`, `shift` or `bend` for a small part, overlay its mask at 12x beside the bare
  crop and read the outline. Rotate only parts that are clearly round or pivoted; a blade or tool strokes along
  its long axis (`shift` 1 px, a 4-frame stroke).
- Evidence: the project's anim-work/batch2/make_b2.py (sawmill()); batch2/ov-Sawmill.png
- Scope: skill
- Status: active · helpful 0 · harmful 0 · last_confirmed 2026-10-23

### L-039 · 2026-10-23 · A part going into an opening: clip it by the opening, darken it with depth, and expect it to vanish early
- Trigger: Colony game batch 2 round 2, The art lead on the Mine: "make the mine cart go all the way in the building and then come
  as far out as it can". A plain shift cannot go in: it would slide the cart over the wall.
- Hypothesis: in a 3/4 view a tunnel into a face runs along that face's depth axis ((2, -1) for a left face), so a
  part going in moves up-right and the opening's far jamb hides it after about half its width; the visible travel
  in is short and the rest of the way happens out of sight.
- Rule: once the part is past its rest position, draw it only inside the opening (the arch outline above the
  wall's base line) and blend it toward the interior's mean colour with depth (0.85 at full depth). Move it along
  the track's own axis, read from the planks or rails, not a 45 degree diagonal. Budget the wait inside short (the
  cart is already hidden for the last part of the travel) and the wait outside longer. The plate under the part is
  grown from a pool chosen per pixel: interior dark above the base line, the jamb at the opening's edge, the track
  below the base line (`synthesize` with a `pick` function). `external` with `soft: "keep"` and an `alpha` region
  when the part also leaves the sprite's silhouette.
- Evidence: the project's anim-work/batch2-r2/make_r2.py (mine()); batch2-r2/mine-out.png; passes every gate at
  her quiet bar (48 f at 8 fps).
- Scope: skill
- Status: active · helpful 0 · harmful 0 · last_confirmed 2026-10-23

### L-040 · 2026-10-23 · A part that travels must be the whole object, rendered in 3D, not the pixels the still shows
- Trigger: Colony game batch 2 round 3, The art lead on the Mine round 2: "study what a mine cart looks like, not just the visible
  half and make it so that it comes out of the mine correctly and rolls on a track the whole way". Round 2 moved the
  still's cart pixels: only the faces the doorway showed, minus its dark interior, sliding over bare planks.
- Hypothesis: a still shows a part only as far as its pose needs (half in a doorway, no wheels, no rails). Once the
  part travels, the viewer sees what a real one would show, so lifting pixels gives a fragment, and with no track
  under it the motion reads as sliding.
- Rule: when a part travels more than a few pixels, paint the whole object in code. Render it in ground coordinates
  (s along the path, t across, z up, axes read from the still: the track (-1, 0.5) and the wall base (1, 0.45) in the
  Mine) at 4x, then box-filter down for soft edges. Colour each face from a palette sampled on the still's own matching
  face (lit, shaded, top), upper part of the palette, with low-frequency noise and a mid band, so it keeps her paint.
  Give it what carries the motion (wheels on rails, rails over the planks). Occlude by depth, not by screen region:
  a sample behind the wall plane (s < 0) shows only through the opening and darkens with depth. Calibrate the rest
  pose against the still's part (face widths and bottom row), and offer the new rest frame as the idle still so the
  tile does not pop when it starts working.
- Evidence: the project's anim-work/batch2-r3/make_r3.py (draw_cart, draw_rails, Canvas); passes every gate at her
  quiet bar (48 f at 8 fps). Proportions from the still: the first render (half-length 4.2) read as a dark slab;
  2.6 by 3.5, H 5.6 read as a cart.
- Scope: skill
- Status: active · helpful 0 · harmful 0 · last_confirmed 2026-10-23

### L-041 · 2026-10-23 · A turning part seen at an angle needs per-pixel body coordinates from the model, not a screen rotation
- Trigger: the Sawmill waterwheel, rendered from a Blender model at 42 degrees yaw: a screen-space `rotate`
  turned the wheel in the picture plane, so spokes swept off the wheel's own ellipse; one fitted plane (T = A R A^-1)
  was still wrong for a thick wheel, whose front and back rims sit about 50 px apart at 1024.
- Hypothesis: a wheel seen at an angle is not one 2D shape: every depth layer (front rim, spokes, back rim, hub)
  projects through its own plane, so no single 2D transform moves all of them correctly.
- Rule: when a 3D model exists, render an ID pass and a 16-bit object-space position pass per frame and move the
  painted part by body point (`model_rotate`). `rotate` with `plane` is only the fallback for a thin part with no
  pos pass.
- Evidence: the project's anim-work/sawmill-3d/paint/wheel_loop.py (plane_matrix and warp_back, the abandoned plane
  route; fold_colour, the per-pixel route); renders in sawmill-3d/model/renders/L1_v04_1024_loop (sprite.json
  rings.wheel, pos_*.tif)
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-042 · 2026-10-23 · A painted wheel turned by one spoke interval does not land on itself; fold it into one sector
- Trigger: the same waterwheel loop: turning the painted wheel by exactly one spoke interval (45 degrees for 8
  spokes) left a seam 2.4 times bigger than the other frame steps, because the painter never makes eight spokes
  alike.
- Hypothesis: a loop of one symmetry interval only closes if the part is exactly symmetric; a painting never is.
- Rule: fold every body point into one canonical sector of the part's n-fold symmetry and take its colour there
  (falling back to other sectors where frame 0 hides it), so every frame shows the same symmetric painted part and
  frame n equals frame 0. Check the seam as the last-to-first step against the median step.
- Evidence: the project's anim-work/sawmill-3d/paint/wheel_loop.py run as `wheel_loop.py
  ../model/renders/L1_v04_1024 ../model/renders/L1_v04_1024_loop trial1/L1_beauty_d60_canny70_s2310001.png
  trial1/plate/L1_beauty_d60_canny70_s2310001.png trial1/loop --match-tone`; trial1/loop/report.json: seam_ratio
  1.003, outside_ok true. The spritewright port gives seam ratio 1.02 and passes every gate on the same inputs.
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-043 · 2026-10-23 · Unmatched part pixels take the nearest part colour, never the plate
- Trigger: the same loop: body points that frame 0 shows in no sector (the wheel's edge turning into view) were
  first left to the plate, which showed through as white specks on the wheel.
- Hypothesis: the plate is painted without the part, so any part pixel that falls back to it is a hole in the part.
- Rule: a part pixel with no match takes the nearest matched part colour (grown inward from the matched pixels);
  only pixels the part leaves show the plate. Report the unmatched count per frame and look when it is large.
- Evidence: the project's anim-work/sawmill-3d/paint/wheel_loop.py (the distance-transform fill in main());
  trial1/loop/report.json unmatched_px 9 to 239 of about 29,600 wheel pixels per frame
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-23

### L-044 · 2026-10-24 · A loop for a level's still takes that level's tone references, and starts from the picked candidate
- Trigger: Sawmill session 3: the L2 and L3 wheel loops built with the default (level 1) tone references had a frame 0
  that differed from the approved still by a mean of 3.5 and 5.3 levels over the whole sprite; the round 2 L1 loop
  had been built on seed 2410011 while the art lead picked 2410012.
- Hypothesis: the still was tone-matched to sprites of its own level; a loop that re-runs the tone fit must use the
  same references, or every pixel shifts and the building jumps in colour when it starts working.
- Rule: build every loop from the exact file that was picked, with the references its still used, then compare strip
  frame 0 with the still: only the moving part may differ (L1/L2/L3 here: 675, 675, 676 px, mean 0.5 to 0.65).
- Evidence: the project's anim-work/sawmill-3d/paint/wheel_loop.py `--tone-refs`; batch3/loop_L{2,3}/report.json
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-24

### L-045 · 2026-10-24 · Downscaling the touched area can move a pixel just outside it; pin the outside to frame 0
- Trigger: the Sawmill L1 loop on the picked seed failed "outside unchanged": one pixel at (60, 48), 1 level of 255,
  in 4 of 16 frames.
- Hypothesis: the hi-res frame is composited only inside the dilated part area, but the downscale to canvas size
  blends a few hi-res pixels across that boundary, so rounding can flip a neighbour by a level.
- Rule: after downscaling, copy frame 0 into every frame outside the part's union area and report the largest drift
  that was pinned; a drift of more than a couple of levels means the area is too tight, not a rounding flip.
- Evidence: wheel_loop.py `outside_drift_pinned` [0,0,1,0,0,0,0,1,1,0,0,0,0,1,0,0]. sw.py `model_rotate` composites
  the same way and may need the same pin (not yet seen there).
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-24

### L-046 · 2026-10-24 · A count-median cut spends a palette on near-black twins in a real render
- Trigger: `pxw.py make` on a real Z-Image "pixel art" potion with `{"colours": 12}` gave #020202, #030302 and
  #030303 as three palette entries (artwright: 4 near-duplicate pairs) and lost the cork's brown to pink.
- Hypothesis: the outline is the most common colour; splitting a box at the median by count keeps halving that
  flat, slightly noisy black area, so small but distinct colours (the cork) never get a box.
- Rule: split at the widest channel's mean value, then merge colours closer than 0.03 in OKLab (the more common
  one stays). A palette can come out with fewer than N colours; that is right, not a bug.
- Evidence: after the change the same render gives 8 distinct colours, the brown cork back, artwright
  `clean_pixel_art` true with 0 near-duplicate pairs; tests/test_make.py `test_median_cut_spends_no_colours_on_twins`.
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-24

### L-047 · 2026-10-24 · aw.py pixel nests its verdict under items; a gate reading a missing key passes silently
- Trigger: the first real make printed `ok: true` with the whole aw.py output under `aw_pixel`; the gate test
  `.get("clean_pixel_art") is not False` was reading None.
- Hypothesis: `aw.py pixel` returns `{"items": [{... "clean_pixel_art": ...}], "ok": ...}`; an "is not False" test
  turns any missing key into a pass.
- Rule: read `items[0]` from aw.py, and test a gate against an explicit failing stub (`PIXELWRIGHT_AW` pointing at
  a script that prints a "not clean" verdict) so a shape change fails loudly.
- Evidence: tests/test_make.py `test_artwright_verdict_fails_the_make`; the real potion run before and after.
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-24

### L-048 · 2026-10-24 · artwright judged a small native sprite on a false grid and failed a pixel-perfect make
- Trigger: the action-make-1 A/B runs: `pxw.py make` recovered the 16x16 potion exactly (10x16 after crop), yet
  `aw_pixel` said not clean: scale 7, alignment 26.7%, 0% uniform blocks, 7.03% transitional pixels. Two runs then
  tried to write this lesson into the plugin's own LEARNINGS.md and were refused.
- Hypothesis: a sprite this small has too few edges for aw's grid search, and at native scale every one-pixel
  shading step between two flat colours counts as a blend.
- Rule: make output is native, so the make gate calls `aw.py pixel --scale 1`; artwright 0.4.1 reports the
  transitional share at a stated scale of 1 instead of failing it (artwright L-012). With an older artwright the
  blend problem remains: check the pixels and say so, never loosen the budget.
- Evidence: C-20261024-2; tests/test_make.py `test_artwright_is_told_the_output_is_native`; the eval potion passes
  with both fixes and fails with either alone.

### L-049 · 2026-10-24 · An outcome case that copies its checker and the fixture's source hands the baseline the answer
- Trigger: the first outcome-make-2 A/B passed 3/3 without the plugin. Two of the three runs read
  `evals/check_make_hard.py` (copied in through the case's `files`), whose header named "the 5.5x render", and the
  fixture script copied with it held the true sprite as code.
- Hypothesis: any file in `files` is part of the task; a model checks its work with the checker it finds and reads
  the source that drew the input.
- Rule: copy only the input. Ship a fixture that writes the input from embedded bytes (`outcome2_fixture.py`) and
  keep the builder with the truth and the checker out of `files`; the A/B harness finds a checker missing from the
  run folder in the suite's home. outcome-make-1 still copies both, so its baseline result proves little.
- Evidence: T-20261024-3; evergreen_ab.py `localize` (resolves a script the run folder lacks against the suite home).
- Scope: skill (and artwright)
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-24

### L-052 · 2026-10-24 · A painting on the review page needs its own size, not the sprite's 3x pixel zoom
- Trigger: 1920x1080 paintings (a game's loading screen, candidates side by side) went on the click-to-pick page,
  whose `choose` buttons zoom every image 3x with pixelated rendering for 96 px sprites; context-only cards (the old
  screen, the game's other screens) also got Keep, Redo and Drop buttons.
- Hypothesis: the page was built for sprites only; a painting needs natural size scaled smoothly to the page width,
  and some cards are information, not decisions.
- Rule: give a review item `"display": "full"` for paintings and illustrations, and `"kind": "info"` for a card that
  shows context with a note field but no pick buttons.
- Evidence: tests/test_pxw.py test_review_full_size_and_info_items (first made in spritewright 0.5.1)
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-24

### L-053 · 2026-10-24 · A frame built from zeros fails the rest gate on a painted still: transparent pixels carry colour bytes
- Trigger: a generated construction strip's last frame (every built pixel copied from a painted still onto a zeroed
  canvas) failed `rest_frame_identical` with 0 new colours and a visually identical result.
- Hypothesis: painted stills often keep RGB values in fully transparent pixels (alpha 0), and the gate compares
  exact RGBA, so a canvas that starts at (0, 0, 0, 0) differs in thousands of invisible pixels.
- Rule: start every generated frame from a copy of the still and clear only its opaque pixels; draw temporary
  elements over that. Never start from `np.zeros_like(still)`.
- Evidence: a 96x96 house strip, 30 frames: rest_frame_identical false before the change, true after
- Scope: skill
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-24

### L-054 · 2026-10-24 · Before an A/B, score a plain ten-line script on the case; if it passes, the baseline will too
- Trigger: outcome-make-3, a real Z-Image render with off-grid shading. A plain script (sprite height / 16, sample
  block centres, nearest palette colour) recovered it exactly once halved for the repository, as did `pxw.py make`.
- Hypothesis: the baseline arm is a model with numpy; anything the obvious script solves, it solves in a turn or two.
  Fractional scales, palettes spread over a set and model shading inside blocks are all within that script's reach.
- Rule: write the obvious plain solution first and run the checker on it (minutes, no cost). Spend an A/B only on a
  case where it fails by more than a pixel the model could fix by looking. Re-check the shipped bytes, not the
  original: resizing a render to fit the repository can make it easier.
- Evidence: T-20261024-4 (plain 3 pixels off at 1024 px, 0 off at the shipped 512 px crop)
- Scope: skill (eval design)
- Status: active · helpful 1 · harmful 0 · last_confirmed 2026-10-24
