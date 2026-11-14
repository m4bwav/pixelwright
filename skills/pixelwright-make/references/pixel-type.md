# Pixel type

For a font or lettering drawn on a pixel grid: scores, menus, name entry, signs. From Omagari, *Arcade Game Typography* (Thames & Hudson, 2019), a survey of about 4,500 arcade games, page numbers as printed. Its plates were sampled, not all studied.

## The grid

- Spacing lives inside the tile. Tiles sit edge to edge, so in an 8x8 font a glyph gets 7x7 at most and the eighth row and column are the gap (pp. 14-15). Draw a full-width M and MMM becomes one blob.
- Five pixels high is the floor for capitals and numerals; the hard ones are B, E, S and 2, 3, 5, 6, 8, 9 (p. 14).
- Spend the spare row and column on an outline or drop shadow. It doubles as the gap and lifts the letters off a busy background (p. 14).
- Multiples of eight are the old hardware's tile sizes, not a law. 8x16 and 16x16 suit big scores and name entry (pp. 15, 219, 264). Pick the size from the text's job and the screen.

## Drawing

- Stem width decides symmetry: an even stem cannot hold a centred one-pixel notch in Y, so pick odd stems if you need that detail (p. 74).
- Give a shape up when the counter needs the room: a sloped A may have to become an octagon or square (p. 74).
- Pick one corner rule and apply it through the set. Omagari's main complaint about Atari's Quiz Show font is that C, D and G are rounded differently from B, O, P and R (p. 74).
- Lowercase on an 8-row cell has no room below the baseline: either raise the descenders of g, j, p, q, y (the old printer and arcade habit) or use a taller cell, and choose once for the whole set (Wagner, *From ASCII Art to Comic Sans*, ch. 4).
- Test the extremes: over-cropped lowercase p and q go unreadable first (p. 127).
- Colour is part of the design in a pixel font, not a later setting. Rows of graded colour, or an alternating palette, give many looks from one small grid (pp. 14, 142).
- A style can date: square MICR-style letters said future until they said retro (pp. 130-131).

## The set

- List the strings first and draw only the characters they use. Old games left letters out to save memory (p. 172).
- A name-entry screen needs delete and confirm glyphs. Three letters can fit one 8x8 tile by a ligature, a shifted baseline or a colour per letter (p. 172; plate p. 173).
- Check punctuation against ASCII: the grave accent is not a closing quote (p. 172).

## Size and spacing on the real screen

- Physical height = glyph pixels x screen height in mm / internal vertical resolution. Eight pixels on a 19-inch arcade CRT at 224 lines came to about 10 mm, readable at arcade distance (p. 15). The same 8 pixels on a modern phone is about half a millimetre at native resolution, at 400 pixels per inch (p. 14).
- Work out that number for the smallest target screen. A handheld console in handheld mode is the case ports miss (p. 264).
- Monospacing is a hardware habit and looks mechanical for Latin text. Use proportional widths when the engine allows, for anything longer than a score or label (pp. 264-265). This is a tendency, not a ban: a monospaced look can be the point in a retro style.

## Scaling up

- No program recovers a designer's intent from pixels; five designers give five answers (p. 74). Do not hand a low-resolution font to an upscaler and call it done.
- The three routes: universal diagonals stay close but do not gain from the resolution; universal rounding reads naturally but exposes the source's inconsistencies; a harmonised redraw is the usual middle ground (p. 74).

## Using it in an engine

A real font file is worth the setup when text changes at run time. Omagari built colour fonts from screenshots with a script into OpenType SVG (p. 266). Support differs by engine and has moved since 2019; check the target engine's docs. A bitmap font sheet is the safe default.

## Atlas to font file

| Route | Use | Expect |
|---|---|---|
| Ref2FontV3 LoRA on FLUX.2 Klein 9B (an "Aa" reference in, a 1280x1280 atlas out) | draft atlas only, then fill the gaps by hand or a second render | 10-25 of 70 glyphs missing or repeated (serif ~10, display ~12, pixel ~25; skipped letters, not malformed ones); style carries over. Klein 9B is non-commercial: never in sold projects. |
| `pxw.py font atlas.png out.ttf --grid CxR --chars "..." --px WxH [--baseline N]` | any atlas with one character per cell, read left to right | one square per lit font pixel (runs merged), proportional advance unless `--mono`; empty cells listed in `missing` (exit 1). No kerning or hinting. Needs fontTools. |
