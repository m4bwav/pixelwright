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
