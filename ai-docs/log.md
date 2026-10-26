# pixelwright log

Append-only, newest last. Notes that name the projects using this plugin stay private, outside this repository.

## 2026-10-24: 0.6.0, first public release

spritewright (sprite animation in code) became pixelwright: the same animation skill, renamed
pixelwright-animate, plus pixelwright-make, which turns AI renders and drawings into real pixel art (grid snap,
background, palette, clean, crop, tile), and a hub skill holding the one CLI, `pxw.py` (`sw.py` stays as a shim).
The repository starts from one fresh commit; the earlier history stays private because it names client work.

- Tests: `tests/test_pxw.py`, `tests/test_make.py`, `tests/check_skills.py`, all green.
- The make eval cases in `evals/evals.json` are written but have not yet run in an A/B harness pass.
- Next: the wiki (pages planned from the README and skills).

## 2026-10-24: GitHub wiki for 0.6.0 written (draft, not published)

Ten pages (Home, Getting-Started, Making-Pixel-Art, Palettes, Animating-A-Sprite, Commands, Gates,
Coming-From-Spritewright, FAQ, Development) plus sidebar, footer and three pictures drawn in code, in
`pixelwright.wiki-draft/` beside this clone. Every output was printed by `ai-docs/notes/2026-10-24-wiki-verify.py`
against the plugin as `claude plugin install` installs it, on Windows (Python 3.14 and 3.9) and Linux; the three
outputs are saved beside it. wikiwright's check, outputs (161 checked, 0 missing) and snippets passed; everwrite
found no strong tells. The maintainer publishes (the wiki repository exists); how, and the update procedure, are in
`ai-docs/notes/2026-10-24-github-wiki.md`.

- Found: artwright 0.4.0 fails outlined sprites from `make` because transparent pixels are stored as RGBA 0,0,0,0;
  nine inaccuracies in the shipped docs (listed in the note), the first being project and personal names in public
  files.
- Next: publish the draft and run `wikiwright.py live`; re-run the Gates page's artwright cases when 0.6.1 ships.

## 2026-10-24: wiki updated to 0.6.1 and published

The verification program was re-run against 0.6.1 with artwright 0.4.1 on Windows (Python 3.14 and 3.9) and
Linux; the three saved outputs were replaced. The artwright verdict now passes the outlined sprites `make` writes
(0.6.1 calls `aw.py pixel --scale 1`), so the Gates, Home and FAQ pages say which versions that needs. Published as
wiki commit `59f76a3`; `wikiwright.py live` found 10 pages and 0 failures, and the three images answered 200.
Details in `ai-docs/notes/2026-10-24-github-wiki.md`.

## 2026-10-24: 0.6.2 released, wiki updated to 0.6.2

The owner said to release everything. PR #1 (merge `49a8981`) fixed the wiki survey's open items 3, 4, 7 and 8: a
missing input prints `ok: false` JSON, `find_aw` reads `CLAUDE_CONFIG_DIR`, recipe.md's `--root` and `clean`
wording, a duplicate changelog ID. Tagged `v0.6.2` with a hand-written GitHub release (no release workflow here).
artwright 0.4.2 (its PR #18, tag `v0.4.2`) leaves fully transparent pixels out of `transitional_pixels`, and
evergreen 0.17.1 (evergreen-protocol PR #33, tag `v0.17.1`) ships the `worth --ab` command-evidence fix; all three
are installed locally. Wiki commit `76c84de`, `live` 0 failures; details in `ai-docs/notes/2026-10-24-github-wiki.md`.
spritewright was not retired: its sessions were still committing on 2026-10-24 and port 8765 was held.

## 2026-10-24: outcome-make-3, a real model render; make's measured value is speed

A Z-Image Turbo img2img render of the eval potion (Mac host, denoise 0.75) became outcome-make-3: off-grid model
shading, no stated size, only the input copied (`outcome3_fixture.py`, embedded bytes, since the repository allows
no images but the banner). `pxw.py make` recovers it exactly, and so does a plain centre-sampling script, so no A/B
was spent on it (T-20261024-4, L-054). outcome-make-1 now copies only its input too. `evergreen.json`'s `tests`
block is filled in. Across three tries, nothing separates the arms on a single sprite; the open question for the
owner is whether speed and one tested pipeline are enough for make. 0.6.3 (PR #4, from another session) is merged
but not tagged. The old spritewright repository was retired the same evening by another session (archived
privately, its plugin entry and evergreen unit removed); nothing from it is owed here.

## 2026-10-24: 0.6.3 and 0.7.0 released, wiki updated to 0.7.0; make's eval hunt closed

The owner ruled that make's measured value, speed and one tested pipeline, is enough, so the search for an eval case
the baseline fails is closed (recorded under T-20261024-4 in TESTS.md). The owner then approved releasing both
merged versions: `v0.6.3` on `2901382` (review page items, PR #4) and `v0.7.0` on `a3f02f5` (natural construction,
PR #7 from another session), each with a hand-written GitHub release; CI passed on both commits. The local install is
0.7.0. The wiki was re-verified against the plugin as `claude plugin install` installs it (identical to
`git archive v0.7.0` apart from `.in_use`) on Windows 3.14, Windows 3.9 and Linux; the only differences were versions,
the new `site` effect in `doctor` and the unknown-effect error, and the test counts (44 and 27). Animating-A-Sprite now
describes the natural vocabulary and the 0.6.3 review items (neither run for the wiki). Details in
`ai-docs/notes/2026-10-24-github-wiki.md`.

## 2026-10-25: 0.8.0, make fixes and steps from a book pass

Six books (three on pixel art, Gonzalez and Woods, two on rendering) were read for the owner's plugins; R-20261025-1
holds what applies here. Make side built: the grid test now rejects periods that a handful of edges fit by chance
(L-061), opt-in clearing of enclosed background (L-062), linear-light dither and a contrast cap, `swap` for palette
variants, `clean.corners` for pixel-perfect lines, a `fog` step and a box filter for model_rotate. Default outputs
are byte-identical to 0.7.3 apart from no-grid images. Rulings: `ai-docs/notes/2026-10-25-books-round2.md`.

- Tests: test_make 36, test_pxw green, check_skills ok.
- Next: the animate side (flicker-pixel and uneven-cadence gates, pixel-perfect bolts and trails, puff noise that
  moves with the puff, timing rules).
