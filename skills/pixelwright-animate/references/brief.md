# Brief schema

Checked 2026-10-23 against `pxw.py` 0.1.0.

```json
{
  "id": "foundry",
  "still": "Assets/Images/Buildings/foundry.png",
  "motion": "Use: the furnace mouth flares white-hot, sparks spit out, it settles. Place: powers on from dark.",
  "extraColours": [[255, 250, 220], [255, 214, 110], [255, 150, 40]],
  "noticeable": {"share": 0.08, "luma": 40},
  "regions": {
    "furnace": {"rects": [[44, 24, 68, 35]], "select": "warm"},
    "body":    {"rects": "all"},
    "sky":     {"rects": [[40, 0, 72, 24]], "alpha": true},
    "screen":  {"poly": [[1, 42], [11, 42], [11, 51], [1, 51]], "select": "cool", "exclude": ["furnace"]}
  },
  "animations": {
    "use":   {"frames": 10, "focal": "furnace", "fps": 12, "tracks": [
      {"effect": "pulse", "region": "furnace", "hot": [255, 250, 220], "curve": [0, 0.5, 1, 1, 0.8, 0.6, 0.4, 0.2, 0.1, 0]},
      {"effect": "sparks", "region": "sky", "source": [50, 24, 62, 26], "bornFrames": [1, 2, 3],
       "colours": [[255, 250, 220], [255, 150, 40], [200, 70, 20]]}
    ]},
    "place": {"frames": 10, "focal": "furnace", "tracks": [
      {"effect": "darken", "region": "body", "curve": [1, 1, 0.9, 0.7, 0.5, 0.3, 0.6, 0.2, 0.1, 0]}
    ]}
  }
}
```

| Field | Meaning |
|---|---|
| `id` | file stem for every output (`cardId` is accepted for older briefs) |
| `still` | the source PNG, relative to `--root`, then to the brief's folder |
| `motion` | one sentence per animation, shown on the review page |
| `extraColours` | colours allowed beyond the still's own (a hotter white, ember red); keep it short |
| `noticeable` | per-brief override of the noticeable gate (per animation too) |
| `regions.<name>.rects` | `[x0, y0, x1, y1]` boxes, x1/y1 exclusive, in still pixels; `"all"` = whole image |
| `regions.<name>.poly` / `maskImage` | a polygon, or a PNG mask (white = in) of the still's size |
| `regions.<name>.model` | `{"frames": <render folder>, "part": <name>, "grow": 4}`: every still pixel the part covers in any ID frame of a 3D render, grown by `grow` (see effects.md, Model rotate) |
| `regions.<name>.select` | keep only `warm`, `cool` or `bright` pixels of the area (lit parts) |
| `regions.<name>.alpha` | the region may change alpha (transparent sky for particles, a part moving out) |
| `regions.<name>.exclude` | subtract other regions |
| `animations.<name>` | `frames`, `tracks`, optional `focal` (region for the brightness measure), `fps`, `rest` (`first`, `last`, `none`) |
| `take` | optional; review keys gain `-<take>` |

Older briefs with top-level `use` and `place` objects instead of `animations` still work.

A region without `alpha` and without `select` is cut to the still's opaque pixels.

## Review extra

`<batch>/review-extra.json` adds sections that are not animations: a list of items.

```json
[
  {"heading": "New stills, batch 2", "key": "still/basic_lab", "title": "basic_lab", "subtitle": "new still",
   "kind": "choose", "choices": [{"value": "s11", "src": "stills-b2/basic_lab-s11.png"}]},
  {"key": "brief/crusher", "title": "crusher", "subtitle": "played by crush", "kind": "approve",
   "text": ["Use: ...", "Place: ..."], "images": ["briefs-b1/crusher.png"]}
]
```

`kind`: `choose` (one button per candidate image plus "None fit"), `approve` (Approve, Redo, Drop) or anything
else (Keep, Redo, Drop). `heading` starts a new heading above the item. Image paths are relative to the batch
folder.
