---
title: GitHub wiki written for 0.6.0 (draft, not yet published)
kind: note
date: 2026-10-24
verified: 2026-10-24
stale_after: 2027-04-24
tags: [wiki, docs, 0.6.0, github]
summary: "the wiki's ten pages for pixelwright 0.6.0, where the draft is, how every example was verified against the released plugin, the facts found on the way, the inaccuracies in the shipped docs, and how to publish and update the wiki; read before touching the wiki or the files listed under inaccuracies"
---

# GitHub wiki for 0.6.0

## Summary

Asked: write the GitHub wiki for the first public release, 0.6.0 (tag `v0.6.0`, released 2026-10-24 19:15 UTC), with the wikiwright skill (0.9.2), Steps 2 to 6 and 8, without publishing: the maintainer creates the wiki repository and publishes. Written: ten pages plus sidebar, footer and three pictures, from the README, CHANGELOG, AGENTS.md, the three skills and their references, `pxw.py` (its argparse and source), the tests and the CI workflow. Every output on the pages was printed by `2026-10-24-wiki-verify.py` (beside this note) against the released plugin as `claude plugin install` installs it. Gates: `wikiwright.py check` 0 errors, 0 warnings; `outputs` 161 checked, 0 missing; `snippets` 1 block checked, 0 missing, 5 commands; everwrite's `tells.py --wiki` 0 strong findings.

Pages: Home, Getting-Started, Making-Pixel-Art, Palettes, Animating-A-Sprite, Commands, Gates, Coming-From-Spritewright, FAQ, Development, plus `_Sidebar.md` and `_Footer.md`, and `images/` (render-2x.png, mushroom-make-8x.png, forge-use-8x.gif: drawn by the verification program, no real artwork; they live only in the wiki, never in this repository).

## Where the pages are

`pixelwright.wiki-draft/`, a sibling of this clone (outside this repository): a flat folder of `.md` files with LF endings and an `images/` folder. It is not a git working copy. Links between pages are plain markdown (`[Gates](Gates)`), no wikilinks.

## How it was published

Not published. On 2026-10-24 `git ls-remote https://github.com/m4bwav/pixelwright.wiki.git` already answered (`refs/heads/master`), so the wiki repository exists. To publish: `python <wikiwright>/scripts/wikiwright.py preflight m4bwav/pixelwright --clone pixelwright.wiki` (a sibling of this clone), copy the draft's files and `images/` into that working copy over the placeholder, commit ("pixelwright 0.6.0 wiki: ten pages, sidebar, footer, images"), `git push`, then `wikiwright.py live m4bwav/pixelwright pixelwright.wiki` and write its line here. Check by eye that the three images render: `check` and `live` do not look at image links.

This repository's commit for the note, the program and its outputs was made locally and not pushed; the maintainer pushes.

## Updating the wiki later

1. `git -C pixelwright.wiki pull --ff-only`, then edit the pages.
2. Re-verify from a folder outside the repository: `python ai-docs/notes/2026-10-24-wiki-verify.py --install --aw <artwright aw.py> --port <free port> --images <folder> > new.out.txt` (needs numpy, Pillow and `claude` on PATH), then `python <wikiwright>/scripts/wikiwright.py diffout ai-docs/notes/2026-10-24-wiki-verify.out.txt new.out.txt`. Every difference is a page to fix (exit 1 means differences). Do the same with `--plugin` on Python 3.9 and on Linux against `.py39.out.txt` and `.linux.out.txt`. Save the new outputs over the old.
3. `wikiwright.py outputs pixelwright.wiki <every new output> --address ''`, `wikiwright.py snippets pixelwright.wiki ai-docs/notes/2026-10-24-wiki-verify.py`, `wikiwright.py check pixelwright.wiki --version <new>`, and everwrite's `tells.py --wiki`.
4. Commit, `git push`, `wikiwright.py live`. Pages that name the version: `_Footer.md`, Home (first public release, tag), Getting-Started (cache path `0.6.0/`, doctor output), Commands, Coming-From-Spritewright (0.6.0 rename), Development (release commit `db32a8e`), and every `doctor`/`--version` output.

0.6.1 is in preparation in the working tree (the make gate passes `--scale 1` to artwright). When it ships, the Gates page's "artwright's verdict" section must be re-run: its outputs will change.

## How the examples were verified

- Program: `2026-10-24-wiki-verify.py` (stdlib, numpy, Pillow). It draws every fixture in code (an upscaled, blurred, noised mushroom "render" on a near-white ground; the same sprite at 5.5x; a gradient with no grid; a 12x12 chest; a 16x16 grass texture; two palette files; a 32x32 forge still with briefs and a plan), runs each page's command as a child process with HOME and USERPROFILE set to an empty folder, masks local paths (`<tmp>`, `<plugin>`, `<artwright>`, `<python>`, `<site-packages>`, `<claude-config>`) and refuses to print if the user name or home folder survives.
- Published package: `--install` ran `claude plugin marketplace add m4bwav/pixelwright` and `claude plugin install pixelwright@pixelwright` (Claude Code 2.1.281) into a throwaway `CLAUDE_CONFIG_DIR`. The installed copy matched `git archive v0.6.0` file for file (`diff -rq`, only Claude Code's `.in_use` marker extra).
- Runs saved: `.out.txt` (Windows 11, Python 3.14.7, numpy 2.5.4, Pillow 13.0.0: what `pip install numpy pillow` gave on 2026-10-24), `.py39.out.txt` (Windows, Python 3.9.25, numpy 2.0.2, Pillow 11.3.0), `.linux.out.txt` (Ubuntu on WSL, Python 3.14.4, numpy 2.5.4, Pillow 13.0.0). `diffout` between them: only versions, Python 3.9's Pillow warnings, argparse wording and OS error text differ. An earlier run on numpy 2.5.2 and Pillow 12.3.0 printed the same reports.
- artwright: the v0.4.0 tag's `aw.py` (downloaded as the tag's tarball into scratch), passed with `--aw`; every other case runs without artwright.
- Review page: served on port 8799 (8765 and 8766 were held by other servers), read back over HTTP, one POST to `/picks`, a second server on the same port; the server was stopped through its own process handle.
- Repository tests on the installed copy: `test_pxw.py` 41 tests OK (4 skipped: the `model_rotate` class, no `tifffile` in the fresh environment), `test_make.py` 23 OK, `check_skills.py` ok. CI on the release commit: six jobs, all green.
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
- A painted gradient quantised to 8 colours passes every make gate, artwright 0.4.0's included.
- artwright 0.4.0 fails outlined sprites from `make`: `pxw.py` stores transparent pixels as RGBA 0,0,0,0 and artwright's blend test reads their RGB, so a dark outline between transparency and a bright fill counts as a blend pixel (a 12x12 box: 11.11% blend with black transparency, 0% with white). This is separate from the false-grid fix being prepared for 0.6.1.
- A missing input file ends in a Python traceback (exit 1, stderr) in most commands; argparse errors print usage on stderr, exit 2; `palette` with both or neither source prints JSON with exit 2. `<command> --help` lists arguments without descriptions.
- `find_aw` looks under `~/.claude/plugins` only, not under `CLAUDE_CONFIG_DIR`.
- `review` binds 127.0.0.1, has a `--print-page` option, and an item picked anything but `redo` leaves the page.
- `make` and `frames` write their files even when a gate fails; `frames` writes every animation's sheet when one fails.
- The 4 `model_rotate` tests skip without `tifffile`; CI installs only numpy and Pillow, so CI skips them.

## Inaccuracies found in the shipped docs

All wait for the maintainer; none was changed.

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

Related: see also [../log.md](../log.md).
