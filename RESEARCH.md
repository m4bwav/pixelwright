# Research: pixelwright (formerly spritewright)

Findings that back [README.md](README.md). Changes they caused are logged in [CHANGELOG.md](CHANGELOG.md); procedural lessons live in [LEARNINGS.md](LEARNINGS.md); test runs and their evidence in [TESTS.md](TESTS.md); schedule and state in `evergreen.json`. Protocol: MAINTENANCE.md.

Topic: Making real pixel art from AI renders and drawings (true-grid snap, palette lock, background, outlines, crop, tiles, gates) and animating existing 2D game sprites with code-made effects inside region masks (palette-locked frames, exact gates, sheets, previews, click review); PixelLab and other AI tools as sources and fallbacks. Tier `moderate`. Last refresh 2026-10-23; next due 2026-11-22.

## Current understanding

- **Settled (high confidence):** for a sprite that already exists, animate a region, not the whole sprite. AI
  image and video models redraw every frame ("each frame is a new roll of the dice", R-P2), so the approach that
  ships is code-made effects inside a mask with the still as the rest frame. R-P4, R-P5 and R-F11 all converge
  on base plus overlay or patch. A 2026-10-23 pilot built 4 sheets for 2 buildings this way; all gates passed and
  the reviewer kept all 4.
- **No maintained tool does this job** (R-F1, R-F11 to R-F16): every popular sprite skill or MCP server makes
  motion with a paid model and gates nothing by pixel diff or palette. The nearest neighbours (SpriteCook skills,
  OpenAI's sprite-pipeline, claude-pxl) are pointed at, and their checks were borrowed (loop close, flicker look,
  frame-1 lock-back).
- **Gates are exact:** RGBA equality for the rest frame and outside the mask (perceptual diffs hide 1 px edge
  changes, R-T2), one palette across all frames (per-frame quantising flickers, R-P1), constant frame size and
  anchor (R-T5). No published harness exists for these (R-T9); this unit's tests are the harness.
- **Moving:** PixelLab's API (endpoints, size and frame limits, credit costs; spec version "dev", R-S2, R-S3) and
  the crowd of hosted sprite MCP servers (R-F1). Re-check both every refresh.
- **Thresholds are taste, not fact:** the "noticeable" floor (8% changed or +40 focal brightness) comes from one
  project's picks; no source gives numbers (R-T9). Calibrate per project from review notes.
- **Previews:** APNG through Pillow (lossless, per-frame durations); GIF bands many-colour stills and rounds
  timing to 10 ms (R-S7, R-P12).
- **Engines:** the sheet name `<id>-<anim>-<N>f.png` is the hand-off; Unity slices through
  `ISpriteEditorDataProvider` with stable sprite IDs (R-S8), Godot through `SpriteFrames` (R-S9). Import code
  stays in the project.

## Open questions

- Which fixer fails least on the same real renders: pxw.py snap, Pixel Snapper, unfake or proper-pixel-art?
  (one batch of 10 renders through each, scored by `aw.py pixel`)
- Wandering grids: AI renders whose block size drifts across the image (26 to 32 px in one measured case) defeat
  one global lattice; does a per-row or per-region lattice pay for its complexity?

- Does PixelLab `animate-with-text-v3` take an arbitrary non-character image directly, or through `/uploads`
  first; does it accept a palette or mask? (schemas in `api.pixellab.ai/v2/openapi.json` not read in full)
- PixelLab USD price per generation and per-tier quotas (the pricing page renders by JavaScript; use a browser or
  fetchwright).
- Does Pillow 13 merge identical consecutive APNG frames (PR #7146 era behaviour)? The preview's hold frames
  depend on it; a one-line local test settles it.
- Build-up reveal order at small sizes: structural bottom-up (current) or another reveal; only a 2015 3D
  prerender case exists (R-P6).
- Saint11 timing and particle guidance was not reached; fetch saint11.art directly.

## Search plan

Four tracks; every refresh runs at least one query on each (scope each to the period since the last refresh; add
the year). Protocol §4 explains the tracks and how tooling, practice and testing findings are judged.

Subject:

- Pixel Snapper, unfake, proper-pixel-art releases and READMEs (what they now fix that pxw.py does not)
- `https://api.pixellab.ai/v2/llms.txt` (diff against the last refresh) and `openapi.json` (read with offsets)
- `pixellab.ai/docs/tools/animate-with-text-new`, `pixellab.ai/termsofservice` (clause 2.1, ownership)
- `aseprite.org/release-notes/` and `aseprite.org/docs/cli/`
- Pillow image-file-formats page (APNG, GIF) and `docs/releasenotes`
- Unity sprite data provider API (the 2022.2 manual page or package API docs; Unity 6 manual URLs redirect-loop);
  Godot `SpriteFrames` class page
- Official forums: PixelLab Discord (no public forum or changelog), community.aseprite.org,
  discussions.unity.com (2D category), forum.godotengine.org, github.com/python-pillow/Pillow/releases

Tooling:

- `https://registry.modelcontextprotocol.io/v0/servers?search=sprite` and `?search=pixel` (many new entries; note
  dates)
- `gh search code 'path:SKILL.md sprite animation'` and `'path:SKILL.md "pixel art"'` (needs auth)
- skills.sh repo pages for spritecook/skills, nousresearch hermes-agent pixel-art, omer-metin pixel-art-sprites
  (weekly installs)
- `raw.githubusercontent.com/openai/plugins/main/plugins/game-studio/skills/sprite-pipeline/SKILL.md`
- github.com/willibrandon/pixel-plugin, github.com/Hugo-Dz/spritefusion-pixel-snapper (archive flags, releases)
- Supersession sweep: `"sprite animation" skill deprecated OR superseded OR archived <year>`

Practice:

- forums.factorio.com `working_visualisations`; community.aseprite.org rotation and timing threads
- `"build-up animation" OR "construction animation" city builder pixel <year>`
- `site:itch.io devlog pixel art building animation <year>`; Reddit r/PixelArt, r/gamedev, r/aigamedev through
  fetchwright (WebFetch is blocked there)
- hn.algolia.com `search_by_date?query=pixel%20art%20animation`

Testing:

- `pixel art palette check OR lint OR validate CI <year>`; Glama pages of aseprite MCP servers (metric schemas)
- `sprite sheet visual regression OR snapshot test game <year>`
- `site:arxiv.org sprite animation evaluation OR benchmark <year>`

Best sources (primary first): PixelLab llms.txt and openapi.json, Aseprite release notes and CLI docs, Pillow
docs, Unity and Godot manuals, the MCP registry, skills.sh, forums.factorio.com, community.aseprite.org. Noisy:
SEO "best AI pixel art" lists, Kling and Pixa marketing pages, OnWorks mirrors, third-party PixelLab reviews.

## Findings log

Newest first. Sub-ids from the creation pass: R-S (subject), R-F (tooling), R-P (practice), R-T (testing).

### R-20261025-1 · 2026-10-25 · Six books: three on pixel art, image processing, two on rendering
- Track: subject and practice. Magnitude 0.3 (bugs fixed, new opt-in steps; no claim reversed).
- Azzi, Pixel Logic: the most exact of the pixel books: staircase and anti-aliasing amounts, banding, outlines by
  background, hue-shifted ramps, dither only between low-contrast neighbours and never on animated parts (pp.
  111-120), popping rows of 2-3 px, faces kept out of sub-pixel motion, 3-frame minimum loops. Silber, Pixel Art
  for Game Developers: tile repetition faults, palette swaps, pixel flashing (confirms R-P10), flipped light.
  Dawe and Humphries, Make Your Own Pixel Art: fog at about 40% and 80% for middle and far layers, effect beats.
- Gonzalez and Woods, Digital Image Processing 4e: a peak counts only when it stands above chance (section 4.5 and
  the spectral chapters; the grid test, L-061); hole filling by region labelling (section 9.5).
- Hughes et al., Computer Graphics: Principles and Practice 3e: an ordered pattern is seen as its average light,
  so dither belongs in linear light (sections 17.4.5, 28.12); a box filter does not ring where Lanczos does
  (section 19); detail under 2 px aliases (section 25.4). Gambetta, Computer Graphics from Scratch: one pixel per
  major-axis step, and line and fill from one computation.
- Probes on 0.7.3: Bayer dither turned mid grey 75% white on black and white (a light-keeping mix is about 22%);
  Lanczos left a dark halo outside a bright disc reduced 8x; `fx_arc` bolts are about 30% redundant L-corners and
  `fx_scroll` at period 8 over 6 frames steps 1, 2, 1, 1, 2 (both for the animate pass).
- Notes, with page citations and the full proposal lists: kept with the owner's book-learnings records, outside
  this repository.

### R-20261024-1 · 2026-10-24 · Survey for pixel creation (the pixelwright expansion)
- Track: tooling and subject. Magnitude 0.3 (scope widened; no animation claim changed).
- Fixers exist and are good at their core job: Sprite Fusion Pixel Snapper (Rust CLI and WebAssembly, MIT; grid
  snap and palette quantise), unfake (Rust, JS and a PyPI port; scale detection, Wu quantise, several downscale
  modes), proper-pixel-art (PyPI, MIT; one grid and palette over animation frames; PyAV bundles a GPL FFmpeg).
  None locks a sprite to an existing set's colours, cleans outlines or gates its output for an agent, and each is a
  heavier install than numpy and Pillow or not Python. Sources: artwright's pixel-art.md (checked 2026-10-21),
  pypi.org/project/unfake, help.scenario.com Pixel Snapper article.
- Aseprite CLI converts with `--color-mode indexed --palette x.gpl --dithering-algorithm ordered
  --dithering-matrix bayer4x4` and `--scale`; it is the user's own paid editor, so pixelwright writes `.gpl` files
  it reads instead of driving it. Source: aseprite.org/docs/cli.
- PixelLab (REST v2) generates with style references and does inpainting and animation: a source of renders, like
  ComfyUI. Its exact v2 routes were not confirmed this pass (llms-full.txt not read). Source: pixellab.ai/llms-full.txt
  listing, pixellab-mcp README.
- Decision: pixelwright's own snap (phase coherence over edge positions, block mode) plus palette, clean, crop and
  tile steps, gated by artwright's `aw.py pixel`; the fixers are named as alternatives.

### R-20261023-1 · 2026-10-23 · Creation pass
- Summary: two research agents covered all four tracks. Nothing maintained animates an existing still with
  masked code effects and pixel gates; the unit fills that gap and points at model-based tools as fallbacks. The
  pilot's design (mask, palette lock, rest frame = still) matches every practice source found. Cost: searches 40
  · fetches 45 · tool calls 87 · about 30 minutes of agent time.
- Track: subject, tooling, practice, testing
- Sources: below
- Magnitude: n/a (initial)
- Applied: C-20261023-1

#### Subject
- R-S2 · PixelLab v2: `animate-with-text-v3` (default; first_frame, action, frame_count; up to 256 px;
  w x h x frames <= 524,288), `interpolation-v2`, `edit-animation-v2`, `animate-pixminimax` (beta), `vfx`; Bearer
  auth, async jobs, `GET /balance`. https://api.pixellab.ai/v2/llms.txt
- R-S3 · "Animate with Text (New)" keeps the input as frame 1; 4 to 16 even frames; 64 px = 1 generation,
  128 px x 8 frames = 5. https://www.pixellab.ai/docs/tools/animate-with-text-new
- R-S4 · PixelLab ToS 2025-11-23: users own outputs, commercial use allowed, no training other models.
  https://www.pixellab.ai/termsofservice
- R-S6 · Aseprite v1.3.18.6 stable (2026-09-22); CLI `--sheet --sheet-type horizontal --data --format json-array`
  unchanged. https://aseprite.org/release-notes/
- R-S7 · Pillow writes APNG with per-frame duration, loop, disposal, blend; GIF is capped at 256 colours.
  https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html
- R-S8 · Unity sprite data provider API: factories, GetSpriteRects/SetSpriteRects, Apply, name-fileID pairs; keep
  spriteID stable. https://docs.unity3d.com/2022.2/Documentation/Manual/Sprite-data-provider-api.html
- R-S9 · Godot 4 SpriteFrames: sheet import, FPS per animation, per-frame duration multiplier.
  https://docs.godotengine.org/en/4.2/classes/class_spriteframes.html
- R-S10 · 8 to 12 fps convention, 12 the default, holds on twos (convention, no authority).
  https://polycount.com/discussion/comment/2323860

#### Tooling
- R-F1 · MCP registry: about 35 sprite or pixel servers, nearly all hosted credit generators added in the last 3
  months; none does masked local effects. https://registry.modelcontextprotocol.io/v0/servers?search=sprite
- R-F5 · The official PixelLab MCP covers characters and tilesets only and is all rights reserved; call REST for
  buildings. https://github.com/pixellab-code/pixellab-mcp
- R-F11 · spritecook-animate-assets (about 1.0K installs, MIT, no evals): model-based, paid; its per-frame
  checklist was borrowed. https://github.com/spritecook/skills
- R-F12 · OpenAI game-studio sprite-pipeline: seed frame, strip normalisation, frame-1 lock-back.
  https://raw.githubusercontent.com/openai/plugins/main/plugins/game-studio/skills/sprite-pipeline/SKILL.md
- R-F13 · willibrandon/pixel-plugin (387 stars): an Aseprite driver that exports Unity and Godot JSON; no gates.
  https://github.com/willibrandon/pixel-plugin
- R-F14 · Sprite Fusion Pixel Snapper (about 3.3k stars): grid snap and palette lock for cleaning renders.
  https://github.com/Hugo-Dz/spritefusion-pixel-snapper
- R-F15 · Procedural effect code exists only in pieces (hermes-agent pixel-art, gb-sprite); none is masked.
  https://skills.sh/nousresearch/hermes-agent/pixel-art

#### Practice
- R-P1 · Lock one palette across all frames; per-frame quantising flickers.
  https://chronocrash.com/forum/goto/post?id=111189
- R-P2 · AI frames are a new draw each time; keep only the masked region. https://kling.ai/topics/animate-pixel-art-ai
- R-P4 · Frames as patches over a base sprite, reviewed at zoom with a grid (claude-pxl, about 218 stars).
  https://github.com/crsolver/claude-pxl/wiki
- R-P5 · Factorio: animated parts as an overlay over an always-drawn base.
  https://forums.factorio.com/viewtopic.php?p=540609
- R-P6 · City-builder build-up: about 5 frames, ground plan to finished, following the structure.
  https://gamedeveloper.com/design/city-builder-games-make-build-up-animations-cheaply
- R-P7 · The first build frame must replace everything shown before. https://bugs.launchpad.net/widelands/+bug/842960
- R-P8 · Never rotate pixel parts with interpolation; always rotate from the original.
  https://community.aseprite.org/t/rotating-is-causing-distortion-to-the-sprite-solved/4380
- R-P9 · Sub-pixel motion only on large, flat areas.
  https://tinywarriorgames.com/2019/01/04/game-development-pixel-art-sub-pixel-animation/
- R-P10 · 1 px features blink under animation (unconfirmed lead). https://itch.io/post/12910150
- R-P11 · Idle loops: 2 to 4 frames of 1 px moves, long holds; the seam must not pop.
  https://itch.io/blog/559673/pixel-art-idle-cycle-animation-tutorial
- R-P12 · Preview timing from PNG frames or the engine, never a GIF (10 ms rounding).
  https://community.aseprite.org/t/animated-gif-export-rounding-frame-durations/1181
- R-P13 · Particles for pixel art are hard-edged palette pixels with a short trail, not soft circles.
  https://kenney.nl/learn/drawing-particle-effect-sprites
- R-P14 · No dated case studies of agents animating building stills (baseline for the next refresh).
  https://hn.algolia.com/api/v1/search_by_date?query=pixel%20art%20animation&tags=story

#### Testing
- R-T1 · aseprite-mcp `compare_frames` returns changed count, percent and bbox: the same metric shape as these
  gates. https://glama.ai/mcp/servers/NosytLabs/aseprite-mcp/tools/compare_frames
- R-T2 · pixelmatch ignores anti-aliased-looking pixels by default; use exact equality on pixel art.
  https://github.com/mapbox/pixelmatch
- R-T4 · Deterministic engine snapshots (seeded particles, fixed time).
  https://bugnet.io/blog/how-to-use-visual-snapshot-testing-for-game-ui-regressions
- R-T5 · Jitter comes from frame size changes under a fixed anchor; add a loop-seam check.
  https://bugnet.io/blog/fix-pygame-sprite-animation-flicker-on-rect-change
- R-T7 · SSIM, PSNR and LPIPS miss vanished props; human review stays the last gate. https://arxiv.org/html/2412.03685v2
- R-T8 · After import, check filter, compression and PPU; compression shifts colours.
  https://discussions.unity.com/t/sprite-color-loss-changes-when-imported/666275
- R-T9 · No published harness for mask-confined or "noticeable" sprite gates; build own fixtures (baseline).
  https://glama.ai/mcp/servers/NosytLabs/aseprite-mcp/tools/compare_frames
