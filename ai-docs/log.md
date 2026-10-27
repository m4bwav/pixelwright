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

## 2026-10-25: 0.8.1, animate gates from the book pass

`gates.json` reports `flicker_pixels` (lone pixels that blink over three frames) and `cadence_uneven` (linear moves
whose whole-pixel steps differ); `arc` gains `perfect` for clean one-pixel bolts; the timing reference gains the
books' rules. Sheets are byte-identical to 0.8.0. The cadence report caught the skill's own first wording of the
fix (L-063).

- Tests: test_pxw (TestRound2Gates, 4 new; five mutations each fail a test), test_make, check_skills green.

## 2026-10-25: 0.8.2, open-sided buildings (docs only)

Four open-sided sheds made natural construction strips with the ordinary plan and passed every gate on the first
run, so the skill drops the idea of a posts-only reading (L-064). L-059's hand-traced roofs confirmed on two more
batches.

## 2026-10-26: wiki updated to 0.8.2

With the owner's approval, the wiki went from 0.7.0 to the `v0.8.2` release (tagged 2026-10-26 on `18e320c`, holding
the untagged 0.7.1 to 0.8.1). The verification program gained `--old` and cases for every 0.8.x make option and the
new animation reports; it ran against the installed plugin on Windows 3.14, and on `git archive v0.8.2` on Windows 3.9
and Linux, with artwright 0.7.0. The old cases changed only in versions, help text, the new report fields and test
counts (50 and 36). New wiki page Versions-And-Upgrading; Making-Pixel-Art, Palettes, Commands and Gates describe the
snap chance test, holes, linear dither, corners, swap, fog, flicker and cadence. Wiki commit `bea16e8`, live 11 pages,
0 failures. Four new findings for the maintainer (items 10 to 13 in `ai-docs/notes/2026-10-24-github-wiki.md`): the
flicker gate counts moving sparks, `fog` 0.8 with PICO-8 flattens a sprite to one colour unnoticed by any gate,
`flicker_at`'s form is undocumented, and the wiki's own eval sentence was stale.

## 2026-10-26: 0.8.3, log walls and plank roofs

The natural construction plan gains a log build order (`walls: "logs"`) and a board-by-board plank roof
(`roofOrder: "boards"`), so log buildings with plank roofs no longer need setting aside (L-065 supersedes L-056 for
them). Piloted on a painted log lodge: every gate passed on the first run once the roof trace covered the top rim.

- Tests: test_pxw (one new; removing the board order fails it), test_make, check_skills green.

## 2026-10-26: 0.8.4 wiki findings follow-up

Rechecked findings 10 to 12 against 0.8.3 source before editing; the natural log-wall and plank-roof changes
were already present. The flicker gate now looks for a matching incoming and outgoing motion step beyond the
immediate neighbours. Steps may differ by 1 px for rounding or acceleration. Over transparent sky it matches
alpha, allowing a travelling spark to change colour; over opaque art it matches RGBA. This changes only the
report and any explicit flicker cap, not generated frames.

The recipe warns that heavy fog plus a sparse palette can collapse opaque colours while passing every gate.
A fixture preserves that behaviour. Animation references now specify the `flicker_at` coordinate format and
its lack of frame indices. Added INDEX and HANDOFF, which were absent, to keep the current state discoverable.

- Validation: the coordinating session reports 55 animation tests passed (13.473 seconds), 37 make tests passed
  (ResourceWarning), structure checks passed and `git diff --check` passed (T-20261026-1). The first animation
  run had four fixture errors from omitted pulse `hot` fields; fixed before the passing run.
- Publication: pending; the coordinating session owns terminal execution, commits and release. The wiki has
  source-grounded prose edits in four pages; output examples and version footers await the released-archive run.
- Skill freshness: everlast-resume and everwrite are current. wikiwright is due for refresh (2026-10-25);
  refresh is outside this repository's scope and remains with the coordinating session. The plugin's existing
  action-1 eval failure is an evidence-regex issue recorded in evergreen.json, unrelated to this gate fix.
## [2026-10-26] index | rebuilt (2 entries)

## 2026-10-26: 0.8.4 released; tag archive verified, wiki awaiting gates

The coordinating session merged PR #17 as `f3b448ed` and published
[v0.8.4](https://github.com/m4bwav/pixelwright/releases/tag/v0.8.4).
The released-tag wiki verifier exited 0 with no stderr on Windows (Python 3.14.6, numpy 2.5.2, Pillow 12.3.0),
using artwright 0.7.0. Its test sections show 55 animation tests (no skips), 37 make tests and structure checks
passing. Forge and smoke still report 3 unmatched flicker locations each; numerical gate examples stay as
recorded. The motion fix does not claim to track every particle.

Wiki command versions, runtime versions and test counts now match that transcript. Installation and Python 3.9
warning blocks keep their stated 0.8.2 provenance. Python 3.9, Linux, plugin installation and image regeneration
were not repeated for 0.8.4. Next: retain the new transcript, run wiki gates and publish; record the exact wiki
commit and live results, then merge the docs-only follow-up.

## 2026-10-26: 0.8.4 wiki published, follow-up complete

The [wiki](https://github.com/m4bwav/pixelwright/wiki) is published as commit
`8a425d338f817a0f89cbd6a20b83787578dfdf35`. Final checks: 11 pages, 0 errors; 206 output blocks checked,
0 missing, 1 historical-install skip; 1 snippet block, 6 commands, 0 missing; prose 0 strong and 41 weak.
The live check found 11 pages, 0 failures and 23 anchors, 0 broken.

This completes publication after [PR #17](https://github.com/m4bwav/pixelwright/pull/17), merge `f3b448ed`,
and [release v0.8.4](https://github.com/m4bwav/pixelwright/releases/tag/v0.8.4).
Earlier pending-publication entries above describe intermediate states and are superseded by this record.
The coordinating session retains the exact released-tag verifier transcript as
`ai-docs/notes/2026-10-26-wiki-verify-084.out.txt` with the docs-only follow-up.

The archive passed 55 animation tests (none skipped), 37 make tests and structure checks. `diffout` found
136 unchanged sections, 9 version/runtime/test-count changes and 3 removed installation/image sections.
The historical install transcript is explicitly marked; the fragile old warning block was removed.
Python 3.9, Linux, installation and image regeneration were not repeated.

No further runtime change or release is owed here. The forge still reports 3 unmatched flicker locations;
flicker is report-only unless capped, and cadence remains report-only. Calibration needs a hand-made pixel-art
set from the owner. Deferred effects and palette work remain deferred. The coordinating session owns the
docs-only record PR and worktree cleanup.
## [2026-10-26] index | rebuilt (2 entries)
