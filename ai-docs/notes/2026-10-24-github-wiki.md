---
title: GitHub wiki written for 0.6.0, updated to 0.6.1 and published
kind: note
date: 2026-10-24
verified: 2026-10-24
stale_after: 2027-04-24
tags: [wiki, docs, 0.6.0, 0.6.1, github]
summary: "the wiki's ten pages for pixelwright 0.6.1 (first written for 0.6.0), where they are, how every example was verified against the released plugin, the facts found on the way, the inaccuracies in the shipped docs, and how to update the wiki; read before touching the wiki or the files listed under inaccuracies"
---

# GitHub wiki for 0.6.0 and 0.6.1

## Summary

Asked: write the GitHub wiki for the first public release, 0.6.0 (tag `v0.6.0`, released 2026-10-24 19:15 UTC), with the wikiwright skill (0.9.2), Steps 2 to 6 and 8, without publishing: the maintainer creates the wiki repository and publishes. Written: ten pages plus sidebar, footer and three pictures, from the README, CHANGELOG, AGENTS.md, the three skills and their references, `pxw.py` (its argparse and source), the tests and the CI workflow. Every output on the pages was printed by `2026-10-24-wiki-verify.py` (beside this note) against the released plugin as `claude plugin install` installs it. Gates: `wikiwright.py check` 0 errors, 0 warnings; `outputs` 161 checked, 0 missing; `snippets` 1 block checked, 0 missing, 5 commands; everwrite's `tells.py --wiki` 0 strong findings.

Pages: Home, Getting-Started, Making-Pixel-Art, Palettes, Animating-A-Sprite, Commands, Gates, Coming-From-Spritewright, FAQ, Development, plus `_Sidebar.md` and `_Footer.md`, and `images/` (render-2x.png, mushroom-make-8x.png, forge-use-8x.gif: drawn by the verification program, no real artwork; they live only in the wiki, never in this repository).

Update to 0.6.1 (same day, wikiwright Update mode): 0.6.1 (tag `v0.6.1`, commit `57fb409`, released 2026-10-24 19:56 UTC) makes the make gate call `aw.py pixel --scale 1`; artwright 0.4.1 (merged on its main branch, not tagged) no longer fails blend pixels at a stated `--scale 1`. The program was re-run against 0.6.1 with artwright 0.4.1's `aw.py` (the installed plugin copy) on all three set-ups. `diffout` against the 0.6.0 outputs showed version lines, the traceback's line numbers, `test_make.py` going from 23 to 24 tests, and "make with artwright" and "make full with artwright" turning from `ok: false` (blend pixels 1.76% and 3.12%) to `ok: true`. One case was added: artwright on the outlined box with `--scale 1` (clean, 11.11% still counted). Pages changed: Home, Getting-Started, Gates (artwright's verdict rewritten: resolved with pixelwright 0.6.1 plus artwright 0.4.1; the 0.6.0 failure kept as history, its numbers from the 0.6.0 output in commit `ba402ef`), FAQ, Coming-From-Spritewright, Development, sidebar, footer. Gates after the update: `check --version 0.6.1` 0 errors, 0 warnings; `outputs` 162 checked, 0 missing (all three outputs); `snippets` 1 checked, 0 missing; `tells.py --wiki` 0 strong. The images were byte-identical to the 0.6.0 run.

## Where the pages are

The wiki working copy `pixelwright.wiki/` (a sibling of this clone, outside this repository), branch `master`, remote `https://github.com/m4bwav/pixelwright.wiki.git`. The pages were drafted in `pixelwright.wiki-draft/` (a flat folder beside it) and copied in; edit the working copy from now on. Links between pages are plain markdown (`[Gates](Gates)`), no wikilinks.

## How it was published

The maintainer created the wiki repository (GitHub's placeholder Home, `de19923`). The pages were copied over it, committed as wiki commit `59f76a3` (a plain fast-forward) and pushed on 2026-10-24. `wikiwright.py live m4bwav/pixelwright pixelwright.wiki`: 10 pages, 0 failures; footer and sidebar render; anchors 13 links, 0 broken.

Images (`check` and `live` do not look at them): each answered 200 with its image type and the draft's byte size at `https://github.com/m4bwav/pixelwright/wiki/images/<file>` and `https://raw.githubusercontent.com/wiki/m4bwav/pixelwright/images/<file>` (render-2x.png 48,270 bytes, mushroom-make-8x.png 1,034, forge-use-8x.gif 5,396). GitHub rewrites Home's `images/x.png` to `wiki/images/x.png`, which resolves because `/wiki/Home` redirects (301) to `/wiki`; Making-Pixel-Art and Animating-A-Sprite keep `images/x.png`, which resolves under `/wiki/`. The images were not looked at in a browser.

## Updating the wiki later

1. `git -C pixelwright.wiki pull --ff-only`, then edit the pages.
2. Re-verify from a folder outside the repository: `python ai-docs/notes/2026-10-24-wiki-verify.py --install --aw <artwright aw.py> --port <free port> --images <folder> > new.out.txt` (needs numpy, Pillow and `claude` on PATH), then `python <wikiwright>/scripts/wikiwright.py diffout ai-docs/notes/2026-10-24-wiki-verify.out.txt new.out.txt`. Every difference is a page to fix (exit 1 means differences). Do the same with `--plugin` on Python 3.9 and on Linux against `.py39.out.txt` and `.linux.out.txt`. Save the new outputs over the old.
3. `wikiwright.py outputs pixelwright.wiki <every new output> --address ''`, `wikiwright.py snippets pixelwright.wiki ai-docs/notes/2026-10-24-wiki-verify.py`, `wikiwright.py check pixelwright.wiki --version <new>`, and everwrite's `tells.py --wiki`.
4. Commit, `git push`, `wikiwright.py live`, and fetch the three image URLs. Pages that name the version: `_Footer.md`, `_Sidebar.md` and Home (release link), Home (0.6.0 first release, 0.6.1 change), Getting-Started (cache path `0.6.1/`, tag, artwright 0.4.1), Gates and FAQ (the version pair the artwright verdict needs), Coming-From-Spritewright (0.6.0 rename, "two runs of 0.6.1"), Development (installed copy, release commit `57fb409`), and every `doctor` and `--version` output.

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
- `find_aw` looks under `~/.claude/plugins` only, not under `CLAUDE_CONFIG_DIR`.
- `review` binds 127.0.0.1, has a `--print-page` option, and an item picked anything but `redo` leaves the page.
- `make` and `frames` write their files even when a gate fails; `frames` writes every animation's sheet when one fails.
- The 4 `model_rotate` tests skip without `tifffile`; CI installs only numpy and Pillow, so CI skips them.

## Inaccuracies found in the shipped docs

Status after 0.6.1 (the maintainer's fixes): 2, 5, 6 and 9 fixed; 1 partly (the project name generalised and added to `.private-names.txt`; the maintainer's first name stays in CHANGELOG.md, LEARNINGS.md and effects.md); 3, 4, 7 and 8 not fixed. Line numbers below are as found in 0.6.0.

1. Project and personal names in public files, against AGENTS.md's "No project names" rule: a game project's name and the maintainer's first name in CHANGELOG.md:100 and :109, LEARNINGS.md (16 lines between 68 and 167), skills/pixelwright-animate/references/effects.md:46 and :51 (`git grep -n -w` for the name finds them all; the names are not repeated here). CHANGELOG.md also quotes "the art lead" five times (:55, :63, :71, :81, :90) with sprite names from that work. `.private-names.txt` does not list these, so `check_skills.py` passes.
2. CHANGELOG.md:21: "tests/test_make.py (new, 21 tests)"; it runs 23.
3. CHANGELOG.md:54: the 0.4.4 entry has the ID C-20261024-1, the same as the 0.6.0 entry at :15, and sits among the 2026-10-23 entries.
4. skills/pixelwright/SKILL.md:10-11, skills/pixelwright-make/SKILL.md:12, skills/pixelwright-animate/SKILL.md:12, AGENTS.md:16: "every command prints one JSON object". A missing input file gives a traceback; argparse errors give usage text on stderr; `--version` prints plain text.
5. skills/pixelwright-make/SKILL.md:27-29: says to read `coherence` after `snap` and that scale 1 means coherence under 0.5; with no grid found, `coherence` is not printed at all.
6. skills/pixelwright-make/SKILL.md:51: `<id>.gpl` is "its palette"; it holds only the colours the sprite uses.
7. skills/pixelwright-make/references/recipe.md:7-8: "Paths are relative to `--root`, then to the current folder"; `resolve()` tries `--root` and nothing else for a recipe (from the source; not run with a non-default `--root`).
8. skills/pixelwright-make/references/recipe.md:18: the `clean` default reads as if it merged with what you write; a written `clean` object replaces it and orphan removal stops.
9. skills/pixelwright-animate/references/brief.md:3 ("Checked 2026-10-23 against `pxw.py` 0.1.0") and effects.md:3 ("against `pxw.py` 0.5.0"): `pxw.py` first exists in 0.6.0; those versions were `sw.py`.

## Gotchas

- Ports 8765 and 8766 were held by other sessions' review pages; pass `--port`.
- WSL's `/tmp` was cleared between runs (the venv vanished); build the venv in the same `wsl` call that runs the program.
- Another session had 0.6.1 changes uncommitted in this clone while the wiki was written; only the wiki files were committed.
- artwright run by hand without `--scale` still fails outlined `make` output on blend pixels; the make gate is fine because it passes `--scale 1`.

Related: see also [../log.md](../log.md).
