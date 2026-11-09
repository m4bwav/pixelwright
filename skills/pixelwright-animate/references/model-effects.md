# Effects from a model's animation (ChatGPT GIF, video frames)

Explosions, lightning, fire and spells are hard in code and easy for a model. Image models draw soft "HD pixel
art": no shared grid, 250+ colours, a background tint, a blast that wobbles ([L-090](../../../LEARNINGS.md)). Ask for the fixes in the
prompt, then clean in one pass:

- Prompt: "flat solid pure magenta #FF00FF background in every frame" (green #00FF00 for violet or purple
  effects, or the key eats them); pin it: "the bottom edge is the ground line and the explosion hits it at the
  bottom centre, at the same point in every frame"; "fine pixel art, each art pixel 2 to 3 image pixels wide";
  "the tallest flames reach about 85 percent of the frame height, empty background above and at both sides".
  Re-roll coarse or cut-off takes (about 5 in 7 usable). Any reachable video model can stand in for ChatGPT:
  same prompt rules, frames via ffmpeg.

```
pxw.py anim <fx.gif | frames...> <outdir> --name fx [--key magenta|green] [--scale 2.6] [--colours 20]
    [--neutral-greys] [--palette game.hex] [--anchor bottom|none] [--only 3-14]
```

One grid for every frame (detected over all frames pooled; soft art has none, so the command stops and asks for
`--scale`: measure one art pixel on a zoomed frame), the key cleared and its spill removed, one palette for all
frames with up to 6 extra colours for small far-off accents (embers), key-tinted greys made neutral with
`--neutral-greys`, frames that touch the ground pinned to one x, then frames, `<name>_sheet.png` + `.json`
(rects, durations), a `.hex` palette and a contact sheet. `--palette` maps several effects to one game palette so
they belong together. The JSON prints colours and wobble before and after. Hit feel (hit-stop, flash, shake) is
game-juice's job.

## Character actions from a video model

Untested here: tricks from u/FutureTechPilot's r/aigamedev post "Tricks for AI video to 2D battle animations"
(reddit.com/r/aigamedev/comments/1x8m8ly, MiniMax H3 in ComfyUI), reworded. Whole-sprite motion drifts more than
an effect does, so treat each clip as a draft to clean with `pxw.py anim`.

- Floor strip: paint a slightly darker strip under the feet in the start image and say the character stands on
  it; the camera stops drifting and cropping.
- Stance as first and last frame (FL2VA): every clip starts and ends in the same idle pose, so the loop closes
  and clips chain. H3 forces the end frame and often overshoots, then snaps back in the last second: trim it.
- On the spot: no travel inside the clip; the game moves the sprite for leaps, dives and slides.
- Describe only the character's own body ("rocks back on its shell, eyes squeezed shut", not "gets hit") so no
  stray objects appear, in plain words (not "gathering power" or "huge").
- Describe what is there, never name what should not be, even negated; end with "nothing else in the frame; only
  the character moves".
- Short actions: H3 renders at least 4 s, so render the minimum and retime after to one fixed frame count for
  every action.
- The game draws the hit (flash, stars, numbers) on the strike frame; that is game-juice's job.
