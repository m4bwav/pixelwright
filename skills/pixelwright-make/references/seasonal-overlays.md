# Seasonal overlays: snow (or moss, frost, soot) layered on existing building sprites

Lessons from the colony-sim roof-snow pilot (2026-11-07 to 11-12: 4 PRs, about 35 sprites, parked by the
owners as too slow to iterate). Read this before painting any overlay that sits on top of finished art.

## The shape that worked

- **One overlay sprite per building still**, same size, transparent except the covered pixels. The game
  fades its alpha by a coverage value; the base art is never edited.
- **Shade from the base, don't paint flat white.** Take the covered pixel's own luminance, map it into a
  snow ramp (blue-grey shadow to warm white). The roof texture still reads through.
- **Ragged eave:** a 1-2 px overhang below the lowest covered row, chosen by a per-cell hash, so the edge
  is not a ruler line.
- **Stagger in the engine, not in the art:** each building starts at its own coverage threshold (hash of its
  map cell); heated buildings see a fraction of the coverage (35% worked). Sliders for spread, fade width and
  warm hold made tuning possible without rebuilding sprites.

## Finding the roof: the slow part

- **Colour mask** (saturated thatch gold in the upper part of the sprite, regions joined and filled) works
  on thatch only. It fails on plank, shingle and slate roofs, whose colours match their walls.
- **Hand polygons** (a JSON of roof outlines per sprite, plus an optional `cut` list for towers and
  chimneys inside the outline) cover everything else, but each needs a person or agent to trace it and a
  look at full coverage. This is what made iteration cumbersome: every new building, upgrade level or redraw
  of the base art is another polygon.
- Drop specks smaller than about a third of a region; leave light-grey chimneys and red-brick towers bare.
- Large sprites with many roof planes (192x144 university) needed several polygons and still read wrong on
  the first pass.

## Animated buildings

Never put overlay pixels on pixels that move. Diff every frame of the active strip against frame 0 and
remove changed pixels from the mask. A mill whose sails cover 315 of 321 roof pixels gets no layer at all.

## Review

- The owner asked for examples on several building types before judging the render code: show each
  overlay as bare / light / full / heated, on thatch, plank and slate, plus buildings that have no layer.
- Offline composites of the engine's alpha rule are fine as examples, but say they are not in-game shots.
- Early test layers covered only one roof slope; check both slopes and both eaves on every sprite.

## If this is picked up again

Wait until the base art stops changing (every redraw stales its polygon). Better roof detection is the
missing piece: a per-sprite roof mask painted once by the artist, or a segmentation model asked for "roof",
would remove the polygon step. Until then, budget one look per sprite.
