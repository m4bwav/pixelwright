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
