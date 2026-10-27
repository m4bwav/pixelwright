---
title: GitHub wiki verified and published through 0.8.4
kind: note
date: 2026-10-24
verified: 2026-10-26
stale_after: 2027-04-24
tags: [wiki, docs, 0.6.0, 0.6.1, 0.6.2, 0.7.0, 0.8.2, 0.8.4, github]
summary: "eleven wiki pages verified against the 0.8.4 tag archive on Windows and published as 8a425d3; 206 checked outputs, zero missing, one historical-install skip; earlier cross-platform recordings, numbered findings and update procedure"
---

# GitHub wiki for 0.6.0 and 0.6.1

## Summary

Asked: write the GitHub wiki for the first public release, 0.6.0 (tag `v0.6.0`, released 2026-10-24 19:15 UTC), with the wikiwright skill (0.9.2), Steps 2 to 6 and 8, without publishing: the maintainer creates the wiki repository and publishes. Written: ten pages plus sidebar, footer and three pictures, from the README, CHANGELOG, AGENTS.md, the three skills and their references, `pxw.py` (its argparse and source), the tests and the CI workflow. Every output on the pages was printed by `2026-10-24-wiki-verify.py` (beside this note) against the released plugin as `claude plugin install` installs it. Gates: `wikiwright.py check` 0 errors, 0 warnings; `outputs` 161 checked, 0 missing; `snippets` 1 block checked, 0 missing, 5 commands; everwrite's `tells.py --wiki` 0 strong findings.

Pages: Home, Getting-Started, Making-Pixel-Art, Palettes, Animating-A-Sprite, Commands, Gates, Coming-From-Spritewright, FAQ, Development, plus `_Sidebar.md` and `_Footer.md`, and `images/` (render-2x.png, mushroom-make-8x.png, forge-use-8x.gif: drawn by the verification program, no real artwork; they live only in the wiki, never in this repository).

Update to 0.6.1 (same day, wikiwright Update mode): 0.6.1 (tag `v0.6.1`, commit `57fb409`, released 2026-10-24 19:56 UTC) makes the make gate call `aw.py pixel --scale 1`; artwright 0.4.1 (merged on its main branch, not tagged) no longer fails blend pixels at a stated `--scale 1`. The program was re-run against 0.6.1 with artwright 0.4.1's `aw.py` (the installed plugin copy) on all three set-ups. `diffout` against the 0.6.0 outputs showed version lines, the traceback's line numbers, `test_make.py` going from 23 to 24 tests, and "make with artwright" and "make full with artwright" turning from `ok: false` (blend pixels 1.76% and 3.12%) to `ok: true`. One case was added: artwright on the outlined box with `--scale 1` (clean, 11.11% still counted). Pages changed: Home, Getting-Started, Gates (artwright's verdict rewritten: resolved with pixelwright 0.6.1 plus artwright 0.4.1; the 0.6.0 failure kept as history, its numbers from the 0.6.0 output in commit `ba402ef`), FAQ, Coming-From-Spritewright, Development, sidebar, footer. Gates after the update: `check --version 0.6.1` 0 errors, 0 warnings; `outputs` 162 checked, 0 missing (all three outputs); `snippets` 1 checked, 0 missing; `tells.py --wiki` 0 strong. The images were byte-identical to the 0.6.0 run.

Update to 0.6.2 (same day, Update mode): 0.6.2 (tag `v0.6.2`, merge commit `49a8981`) prints a missing or unreadable input as one JSON object instead of a traceback, and `find_aw` looks under `CLAUDE_CONFIG_DIR` before `~/.claude`; artwright 0.4.2 (tag `v0.4.2`) skips runs touching a fully transparent pixel in `transitional_pixels`. The program ran against 0.6.2 with 0.4.2's `aw.py` on all three set-ups, each in a fresh venv with numpy and Pillow only (a run on the system Python, which has `tifffile`, ran the 4 `model_rotate` tests instead of skipping them; use a venv). `diffout`: 12 changed sections on each (versions, both box-black cases at 0.0%, "snap missing file" and "streams" now JSON on stdout, `test_make.py` 24 to 26 tests); Python 3.9's run also moved its Pillow warnings' line numbers (1759 to 1764). `claude plugin install` into a throwaway config gave a copy identical to `git archive v0.6.2` (only `.in_use` extra). Pages changed: Home, Getting-Started, Commands (exit codes, the missing-file example), Gates (the box-black history and both outputs), FAQ, Coming-From-Spritewright, Development, sidebar, footer. Gates: `check --version 0.6.2` 0 errors, 0 warnings; `outputs` 163 checked, 0 missing; `snippets` 1 checked, 0 missing; `tells.py --wiki` 0 strong. Published as wiki commit `76c84de`; `live` 10 pages, 0 failures, 13 anchors 0 broken; the three images 200 at their 0.6.0 sizes. On WSL, build the venv under a new `/tmp` name instead of removing the old one inside `wsl bash -lc` (Claude Code's removal check refuses an `rm -rf` in a `-c` script).

Update to 0.7.0 (2026-10-24 local, Update mode, skipping a separate 0.6.3 wiki): the owner approved releasing both merged versions, `v0.6.3` on `2901382` (review page items `display: full` and `kind: info`) and `v0.7.0` on `a3f02f5` (natural construction: `assemble` plan `"vocabulary": "natural"`, effect `site`); both tags carry hand-written releases dated 2026-10-25 UTC. The program ran with `--install` (Windows, Python 3.14.6 in a fresh venv, numpy 2.5.4, Pillow 13.0.0) and with `--plugin` on `git archive v0.7.0` (Windows Python 3.9.25 venv with numpy 2.0.2 and Pillow 11.3.0; Ubuntu on WSL, Python 3.14), all with artwright 0.4.2's `aw.py`. The throwaway install matched the archive (`diff -rq`, only `.in_use`). `diffout`: versions, `site` in every `doctor` effect list and in the unknown-effect error, `test_pxw.py` 41 to 44 and `test_make.py` 26 to 27; on 3.9 the Pillow warnings' line numbers moved (1764 to 1994 and others). Images byte-identical. Pages changed: Home (versions, the 0.6.3 and 0.7.0 sentence), Getting-Started (cache path, tag, `doctor` outputs, the 3.9 warning line), Animating-A-Sprite (a paragraph on the natural vocabulary and one on the 0.6.3 review items, both from the source docs and not run; `site` added to the not-run list; tests 44), Gates (the unknown-effect error), FAQ, Coming-From-Spritewright, Development (tests, release commit `a3f02f5`), sidebar, footer. Gates: `check --version 0.7.0` 0 errors, 0 warnings; `outputs` 163 checked, 0 missing on all three outputs; `snippets` 1 checked, 0 missing; `tells.py --wiki` 0 strong. Published as wiki commit `4e1d365`; `live` 10 pages, 0 failures, 13 anchors 0 broken; the three images 200 at their sizes. For the Linux run, copy artwright's `skills/` tree (not `aw.py` alone) and keep `--port 8799`, or the masked `aw` path and the review port differ from the saved output; and give `wsl bash -lc` absolute paths (`$PWD` resolved to the Windows working folder, not the folder `cd` named in the same script).

Update to 0.8.2 (2026-10-26, Update mode, with the owner's approval): `v0.8.2` on `18e320c` (released 2026-10-26 12:05 UTC) holds 0.7.1 to 0.8.1 too, none of which was tagged. The program gained `--old` (an extracted older release, run as `old-pxw.py`) and 38 new sections: `snap` on a smooth JPEG (0.8.2 and 0.7.0), `bg --holes` on a ring, `--dither-space linear` and `--max-step` on a flat grey, `clean --corners` on a stair-step line and on the chest, `swap` (map, unmapped colours, palette index, folder), `fog` at 0.4 and 0.8, a capped `max_flicker_pixels` and a `shift` with uneven cadence. Runs: `--install` on Windows, Python 3.14.7 (numpy 2.5.4, Pillow 13.0.0), with `--images`; `--plugin` on `git archive v0.8.2` on Windows Python 3.9.25 (numpy 2.0.2, Pillow 11.3.0) and on Ubuntu on WSL (Python 3.14.4); all with `--old` on `git archive v0.7.0` and artwright 0.7.0's `skills/` tree (tag `v0.7.0`, the newest; its cases printed what 0.4.2 printed). A separate throwaway install matched `git archive v0.8.2` (`diff -rq`, only `.in_use`). `diffout` against the 0.7.0 outputs, old cases only: versions; `swap` in the usage text; `palette --help` two lines longer; `enclosed_cleared: 0` in every background step; `drawn_outside_silhouette` and `flicker_pixels` (with `flicker_at`) in every animation's gates; tests 44 to 50 and 27 to 36. No `pass` or `ok` changed; the three images byte-identical. Pages changed: Home, Getting-Started, Making-Pixel-Art (too few edges, enclosed holes, corners, swap, fog), Palettes (linear light and the cap), Animating-A-Sprite, Commands (swap, new options, exit rows), Gates (two table rows, Flicker and cadence), FAQ (the snap question), Coming-From-Spritewright, Development (tests, CI commit, the eval sentence, which was stale), sidebar, footer; new page Versions-And-Upgrading. Pages were written with `{{CASE:label}}` placeholders filled from the saved output by a scratch script (L-155). Gates: `check --version 0.8.2` 0 errors, 0 warnings; `outputs` 211 checked, 0 missing over the three outputs; `snippets` 1 checked, 0 missing, 6 commands; `tells.py --wiki` 0 strong. Published as wiki commit `bea16e8`; `live` 11 pages, 0 failures, 22 anchors 0 broken; the three images 200 at their sizes. From Git Bash, `wsl bash -l /mnt/c/...` fails (MSYS rewrites the path); call `wsl` from PowerShell.

## 0.8.4 follow-up, verified archive and published wiki

[PR #17](https://github.com/m4bwav/pixelwright/pull/17) merged as `f3b448ed`.
[Release v0.8.4](https://github.com/m4bwav/pixelwright/releases/tag/v0.8.4) is live. It adds motion matching to
the flicker gate and documents `flicker_at` and the fog caveat. The 0.8.3 log-wall and plank-roof changes were
already shipped and were left intact.

The coordinating session ran the existing verifier against the released 0.8.4 tag archive using `--plugin`,
artwright 0.7.0 and port 8799. It exited 0 with no stderr. The transcript identifies Windows, Python 3.14.6,
numpy 2.5.2 and Pillow 12.3.0. Its test sections report 55 animation tests, 37 make tests and structure checks
passing, with no animation skips. The forge still reports 3 flicker locations and fails a cap of 0; its
locations are not matched by the heuristic. The smoke case still reports 3 too. These numerical examples
are unchanged. Motion matching is covered by the new synthetic regression fixtures, not a claim that every
moving spark is now excluded.

Wiki edits cover Home, Getting-Started, Making-Pixel-Art, Animating-A-Sprite, Gates, Coming-From-Spritewright,
FAQ, Development, Versions-And-Upgrading, sidebar and footer. Current command/version/test output was updated
from the new transcript. Getting-Started retains the explicitly historical 0.8.2 installation transcript,
with an `outputs: skip` reason pointing to its saved 0.8.2 evidence. The fragile warning block and its source
line number were removed; prose records the earlier Python 3.9 warning and the warning-free 0.8.4 run.
Python 3.9, Linux, plugin installation and image regeneration were not repeated for 0.8.4.

The [wiki](https://github.com/m4bwav/pixelwright/wiki) was published as commit
`8a425d338f817a0f89cbd6a20b83787578dfdf35`. Final gates reported by the coordinating session:

- `check`: 11 pages, 0 errors.
- `outputs`: 206 checked, 0 missing, 1 historical-install skip.
- `snippets`: 1 block, 6 commands, 0 missing.
- Prose: 0 strong findings, 41 weak findings.
- `live`: 11 pages, 0 failures; 23 anchors, 0 broken.

Verification transcript filename: `2026-10-26-wiki-verify-084.out.txt`, beside this note. The coordinating
session retains the exact released-tag transcript with the docs-only follow-up records.
`diffout` against the saved 0.8.2 Windows output reported 148 sections: 136 same, 9 changed and 3 removed.
Changes were versions, runtime versions and test counts; removed sections were the two installation sections
and image regeneration. The installer and images were not re-run. None of the recorded forge or smoke gate
numbers changed.

The first wiki gate pass reported 9 output mismatches while the page reconciliation was in progress.
The released transcript resolves the version, runtime and test-count mismatches; the historical install
recording is marked explicitly and the old warning block is removed. The final gate results above include
those corrections.

Flicker remains report-only unless an animation sets `max_flicker_pixels`; cadence remains report-only.
Calibrating thresholds needs a hand-made pixel-art set from the owner. The unmatched spark locations in the
forge are documented limits of the heuristic, rather than a claim of full particle tracking.

## Where the pages are

The wiki working copy `pixelwright.wiki/` (a sibling of this clone, outside this repository), branch `master`, remote `https://github.com/m4bwav/pixelwright.wiki.git`. The pages were drafted in `pixelwright.wiki-draft/` (a flat folder beside it) and copied in; edit the working copy from now on. Links between pages are plain markdown (`[Gates](Gates)`), no wikilinks.

## How it was published

The maintainer created the wiki repository (GitHub's placeholder Home, `de19923`). The pages were copied over it, committed as wiki commit `59f76a3` (a plain fast-forward) and pushed on 2026-10-24. `wikiwright.py live m4bwav/pixelwright pixelwright.wiki`: 10 pages, 0 failures; footer and sidebar render; anchors 13 links, 0 broken.

Images (`check` and `live` do not look at them): each answered 200 with its image type and the draft's byte size at `https://github.com/m4bwav/pixelwright/wiki/images/<file>` and `https://raw.githubusercontent.com/wiki/m4bwav/pixelwright/images/<file>` (render-2x.png 48,270 bytes, mushroom-make-8x.png 1,034, forge-use-8x.gif 5,396). GitHub rewrites Home's `images/x.png` to `wiki/images/x.png`, which resolves because `/wiki/Home` redirects (301) to `/wiki`; Making-Pixel-Art and Animating-A-Sprite keep `images/x.png`, which resolves under `/wiki/`. The images were not looked at in a browser.

## Updating the wiki later

1. `git -C pixelwright.wiki pull --ff-only`, then edit the pages.
2. Re-verify from a folder outside the repository: `python ai-docs/notes/2026-10-24-wiki-verify.py --plugin <extracted new release tag archive> --old <git archive v0.7.0> --aw <released artwright aw.py> --port <free port> > new.out.txt` (needs numpy and Pillow), then `python <wikiwright>/scripts/wikiwright.py diffout ai-docs/notes/2026-10-26-wiki-verify-084.out.txt new.out.txt`. Every difference is a page to fix (exit 1 means differences). The 0.8.4 baseline uses artwright v0.7.0 and port 8799. Retain the saved 0.8.2 outputs for the historical install evidence and earlier cross-platform claims; they are not current-version runs. Use `--install` only when intentionally re-verifying installation, and `--images <folder>` when regenerating images.
3. `wikiwright.py outputs pixelwright.wiki <every new output> --address ''`, `wikiwright.py snippets pixelwright.wiki ai-docs/notes/2026-10-24-wiki-verify.py`, `wikiwright.py check pixelwright.wiki --version <new>`, and everwrite's `tells.py --wiki`.
4. Commit, `git push`, `wikiwright.py live`, and fetch the three image URLs. Pages that name the version: `_Footer.md`, `_Sidebar.md` and Home (release link), Home (release history paragraph and the 0.8.2 paragraph, run version), Versions-And-Upgrading (release table, the upgrade section names 0.7.0 and 0.8.2: add a row and a new upgrade section), Making-Pixel-Art, Palettes, Commands and Gates ("since 0.8.0/0.8.1" notes, and the 0.7.0 smooth-render output), FAQ (the snap question, the newest pair), Getting-Started (cache path, tag, artwright version), Gates and FAQ (the version pair the artwright verdict needs), Coming-From-Spritewright (0.6.0 rename, "two runs of 0.6.1"), Development (installed copy, release commit `49a8981`), Commands (the 0.6.2 change to missing files), FAQ (the traceback question), and every `doctor` and `--version` output.

## How the examples were verified

- Program: `2026-10-24-wiki-verify.py` (stdlib, numpy, Pillow). It draws every fixture in code (an upscaled, blurred, noised mushroom "render" on a near-white ground; the same sprite at 5.5x; a gradient with no grid; a 12x12 chest; a 16x16 grass texture; two palette files; a 32x32 forge still with briefs and a plan), runs each page's command as a child process with HOME and USERPROFILE set to an empty folder, masks local paths (`<tmp>`, `<plugin>`, `<artwright>`, `<python>`, `<site-packages>`, `<claude-config>`) and refuses to print if the user name or home folder survives.
- Published package: `--install` ran `claude plugin marketplace add m4bwav/pixelwright` and `claude plugin install pixelwright@pixelwright` (Claude Code 2.1.281) into a throwaway `CLAUDE_CONFIG_DIR`. The installed copy matched `git archive v0.6.0`, and on the update `git archive v0.6.1`, file for file (`diff -rq`, only Claude Code's `.in_use` marker extra). The 3.9 and Linux runs used `--plugin` on those archives.
- Runs saved: `.out.txt` (Windows 11, Python 3.14.7, numpy 2.5.4, Pillow 13.0.0: what `pip install numpy pillow` gave on 2026-10-24), `.py39.out.txt` (Windows, Python 3.9.25, numpy 2.0.2, Pillow 11.3.0), `.linux.out.txt` (Ubuntu on WSL, Python 3.14.4, numpy 2.5.4, Pillow 13.0.0). `diffout` between them: only versions, Python 3.9's Pillow warnings, argparse wording and OS error text differ. An earlier run on numpy 2.5.2 and Pillow 12.3.0 printed the same reports.
- artwright: for 0.6.0, the v0.4.0 tag's `aw.py` (the tag's tarball, in scratch); for 0.6.1, 0.4.1's `aw.py` from the installed plugin cache (not tagged). Passed with `--aw`; every other case runs without artwright.
- Review page: served on port 8799 (8765 and 8766 were held by other servers), read back over HTTP, one POST to `/picks`, a second server on the same port; the server was stopped through its own process handle.
- Repository tests on the installed copy: `test_pxw.py` 41 tests OK (4 skipped: the `model_rotate` class, no `tifffile` in the fresh environment), `test_make.py` 23 OK on 0.6.0 and 24 on 0.6.1, `check_skills.py` ok. CI: the tests workflow passed on both release commits (`db32a8e`, `57fb409`).
- Not tested: macOS (CI only), other agents than Claude Code, the agent routes (asking Claude to make or animate), `claude plugin uninstall`, the effects `glint`, `dust`, `brighten`, `shift`, `rotate`, `model_rotate`, `bend`, `bands`, `scroll`, `fill`, `arc`, `drone`, `cart`, `external`, `review-extra.json`, PixelLab, the byte-identity claim against spritewright 0.5.0 (never released), engine import.
- Pages were built from source pages with placeholders filled from the saved output by a scratch script (L-155 in wikiwright), so no output was copied by hand.

## Facts verified while writing (not in the README)

- The install is from the repository as its own marketplace; the plugin lands in `plugins/cache/pixelwright/pixelwright/0.6.0/` of the Claude Code configuration folder. The release has no asset.
- Outputs are the same on Windows and Linux and on Python 3.9 and 3.14. On Python 3.9, Pillow 11.3.0 prints a `DeprecationWarning` on stderr for every image `pxw.py` writes (`Image.fromarray(..., "RGBA")`); Pillow 13.0.0 (2026-10-16) accepts the argument and both test suites pass on it.
- `snap` prints no `coherence` field when it finds no grid, and `coherence: [null, null]` when the scale is given.
- `uniform_blocks` reads 0.0 on a noisy render at the right scale and offset; 1.0 on a clean upscale.
- A 5.5x upscale snaps as 5.498 with the right native size.
- `make`'s default background step clears border-connected pixels on art with no flat ground: 4,030 of 12,288 pixels of a painted gradient.
- A recipe's `clean` object replaces the default `{"alpha": 128, "orphans": true}`, so orphans stay unless listed. The default orphan step also runs on hand-made art (20 of 256 grass pixels).
- `{"colours": N}` can return fewer than N (8 asked, 7 kept).
- `make`'s `.gpl` holds the colours used; `palette --gpl` writes the whole palette named after the output file's stem. Palette files come back sorted and de-duplicated.
- `tile`'s `ok` checks only new colours; the 1.5 seam limit is a `make` gate.
- `size_ok` can only be true: a sprite that does not fit is refused by the crop step first.
- A painted gradient quantised to 8 colours passes every make gate, artwright's included (0.4.0 and 0.4.1).
- artwright 0.4.0 fails outlined sprites from `make`: `pxw.py` stores transparent pixels as RGBA 0,0,0,0 and artwright's blend test reads their RGB, so a dark outline between transparency and a bright fill counts as a blend pixel (a 12x12 box: 11.11% blend with black transparency, 0% with white). Resolved for `make` by the pair pixelwright 0.6.1 (calls `--scale 1`) and artwright 0.4.1 (no blend failure at a stated scale 1); `aw.py pixel` without `--scale` still counts and fails these pixels.
- A missing input file ends in a Python traceback (exit 1, stderr) in most commands; argparse errors print usage on stderr, exit 2; `palette` with both or neither source prints JSON with exit 2. `<command> --help` lists arguments without descriptions.
- `find_aw` looked under `~/.claude/plugins` only, not under `CLAUDE_CONFIG_DIR` (fixed in 0.6.2).
- `review` binds 127.0.0.1, has a `--print-page` option, and an item picked anything but `redo` leaves the page.
- `make` and `frames` write their files even when a gate fails; `frames` writes every animation's sheet when one fails.
- The 4 `model_rotate` tests skip without `tifffile`; CI installs only numpy and Pillow, so CI skips them.
- (0.8.2) A smooth JPEG with no grid snapped at scale 57 into 13x13 under 0.7.0, with coherence 1.0 across and 0.0 down; 0.8.2 returns it at scale 1.
- (0.8.2) `bg --holes 4` on a ring cleared the 64-pixel hole and kept a 1-pixel patch of the ground colour; `enclosed_cleared` is printed (0) even without `--holes`.
- (0.8.2) Flat grey 128 dithered bayer4 on black and white: 75.0% white in `srgb`, 18.8% (3 of 16) in `linear`; with `--max-step 0.12` nothing is dithered (100% white, the nearest colour).
- (0.8.2) `--corners` on a doubled diagonal removed 5 pixels and kept both ends; on the chest's box outline it changed nothing.
- (0.8.2) `swap` with a partial map still writes the file and exits 1 with the unmapped colours.
- (0.8.2) `fog` 0.4 on the mushroom with 8 colours kept 6 colours (brightness spread 70.3 to 42.1); `fog` 0.8 with PICO-8 collapsed the sprite to one colour (spread 0.0), and every gate still passed.
- (0.8.2) `flicker_pixels` counted 3 pixels on the forge's `use` animation, all sparks in the sky; with `max_flicker_pixels: 0` the animation fails. `drawn_outside_silhouette` is 8 there (sparks over the transparent sky) and does not fail it.
- (0.8.2) A `shift` of 8 px over 6 frames with a linear curve reports `cadence_uneven` steps 2, 1, 2, 1, 2 and still passes.

## Inaccuracies found in the shipped docs

Status after 0.6.2: 2, 5, 6 and 9 fixed in 0.6.1; 3, 4, 7 and 8 fixed in 0.6.2 (4 by making a missing input print JSON and naming argparse's usage text as the exception; `find_aw` now reads `CLAUDE_CONFIG_DIR` too); 1 partly, by decision (the project name generalised and added to `.private-names.txt`; the maintainer's first name stays in CHANGELOG.md, LEARNINGS.md and effects.md). Line numbers below are as found in 0.6.0.

1. Project and personal names in public files, against AGENTS.md's "No project names" rule: a game project's name and the maintainer's first name in CHANGELOG.md:100 and :109, LEARNINGS.md (16 lines between 68 and 167), skills/pixelwright-animate/references/effects.md:46 and :51 (`git grep -n -w` for the name finds them all; the names are not repeated here). CHANGELOG.md also quotes "the art lead" five times (:55, :63, :71, :81, :90) with sprite names from that work. `.private-names.txt` does not list these, so `check_skills.py` passes.
2. CHANGELOG.md:21: "tests/test_make.py (new, 21 tests)"; it runs 23.
3. CHANGELOG.md:54: the 0.4.4 entry has the ID C-20261024-1, the same as the 0.6.0 entry at :15, and sits among the 2026-10-23 entries.
4. skills/pixelwright/SKILL.md:10-11, skills/pixelwright-make/SKILL.md:12, skills/pixelwright-animate/SKILL.md:12, AGENTS.md:16: "every command prints one JSON object". A missing input file gives a traceback; argparse errors give usage text on stderr; `--version` prints plain text.
5. skills/pixelwright-make/SKILL.md:27-29: says to read `coherence` after `snap` and that scale 1 means coherence under 0.5; with no grid found, `coherence` is not printed at all.
6. skills/pixelwright-make/SKILL.md:51: `<id>.gpl` is "its palette"; it holds only the colours the sprite uses.
7. skills/pixelwright-make/references/recipe.md:7-8: "Paths are relative to `--root`, then to the current folder"; `resolve()` tries `--root` and nothing else for a recipe (from the source; not run with a non-default `--root`).
8. skills/pixelwright-make/references/recipe.md:18: the `clean` default reads as if it merged with what you write; a written `clean` object replaces it and orphan removal stops.
9. skills/pixelwright-animate/references/brief.md:3 ("Checked 2026-10-23 against `pxw.py` 0.1.0") and effects.md:3 ("against `pxw.py` 0.5.0"): `pxw.py` first exists in 0.6.0; those versions were `sw.py`.

Found in the 0.8.2 pass (10 to 12 addressed in 0.8.4; tag archive verified and wiki published as `8a425d3`):

10. skills/pixelwright/scripts/pxw.py, the flicker gate's comment "things that move on do not count": a spark that moves more than one pixel a frame is counted (3 on the forge's `use`, all sparks). Either the comment or the test is off; the timing reference does not say which animations should cap it.
11. skills/pixelwright-make/references/recipe.md, `fog` row: "about 0.4 for a middle layer, 0.8 for the far one" carries no caveat; 0.8 with PICO-8 turned the whole mushroom into one colour and no gate noticed (the budget gate only caps colours).
12. skills/pixelwright-animate/SKILL.md (Step 3) says flicker pixels are "located in `flicker_at`" but not its form: up to 8 `[x, y]` pairs with no frame index, so a reader cannot tell which frame blinks. timing-and-gates.md does not mention it.
13. The wiki's own Development page said the make eval cases had not run in an A/B pass; TESTS.md records two passes on 2026-10-24 (fixed on the wiki).

## Gotchas

- Ports 8765 and 8766 were held by other sessions' review pages; pass `--port`.
- WSL's `/tmp` was cleared between runs (the venv vanished); build the venv in the same `wsl` call that runs the program.
- Another session had 0.6.1 changes uncommitted in this clone while the wiki was written; only the wiki files were committed.
- artwright run by hand without `--scale` still fails outlined `make` output on blend pixels; the make gate is fine because it passes `--scale 1`.

Related: see also [../log.md](../log.md).
