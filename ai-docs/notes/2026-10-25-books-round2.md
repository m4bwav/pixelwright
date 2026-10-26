# 2026-10-25: book pass, make side (0.8.0)

Rulings made while building R-20261025-1 into pixelwright-make. Each is small and reversible.

1. **Grid test line 2.8/sqrt(k).** The notes proposed 3/sqrt(k); a real 16 px sprite at a fractional scale has 10
   edges at coherence 0.94, under 3/sqrt(10) = 0.95. Random edges reach about 2.6/sqrt(k) one time in 20, so 2.8
   keeps both (L-061).
2. **Holes off by default** (L-062): existing tests and the real-render eval rely on background-coloured pixels
   inside a sprite staying.
3. **Linear-light dither is an option, not the default.** It is plainly more faithful to the light (worst step
   error 0.03 against 0.62 on a grey ramp), but sheets and sprites made with `bayer4` must stay reproducible, and
   nobody has looked at real sprites both ways. Flip the default only after a side-by-side on real renders, with a
   CHANGELOG entry.
4. **Contrast cap on both dither spaces.** In `linear` it compares the two colours being mixed; in `srgb` it
   compares the dithered pick with the undithered nearest colour. 0.12 OKLab lightness is the suggested value
   (heuristic); no default, so nothing changes unless asked.
5. **Fog blends in sRGB**, as a layer opacity in an editor does (the book's method), and runs before the palette
   step so the result is locked again; without a palette step it adds colours, which the budget gate reports.
6. **swap is a command, not a recipe step**: variants are made from a finished sprite or a folder of frames, and
   an unmapped colour fails rather than passing through.
7. **Corner fixer visits pixels in reading order with earlier removals counting**, so a doubled stair keeps one
   pixel a step; checking every pixel against the original removed both pixels of a step and broke the line.
8. **Box downscale only for model_rotate frames**, as the `filter` field; Lanczos stays the default for
   reproducible sheets.

Dropped from the proposals: ramp builder, fractional shift, flame effect, Lloyd refinement of median cut and a
`false_contours` gate (low value for their bytes, or no failing case yet).
