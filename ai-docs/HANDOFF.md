# pixelwright handoff

## Current work

0.8.4 follow-up to the wiki findings, based on the 0.8.3 source. Changes are limited to flicker motion
matching, its tests, the fog warning and fixture, and the format of `flicker_at`. Source and manifest versions
both say 0.8.4. No effect or make output is meant to change.

## Next single action

Re-run `python tests/check_skills.py` after the records edits, then merge with a merge commit after CI passes,
release v0.8.4, and verify/update the wiki against the tag archive. Local validation passed: 55 animation tests
(13.473 seconds), 37 make tests, structure checks and `git diff --check` (T-20261026-1).
PR, release, old/new wiki-output comparison and wiki commit are pending.

## Limits

The motion check is a heuristic: it matches incoming and outgoing steps within 1 px. A spark over clear
sky may change colour; motion over opaque art needs matching RGBA. Unmatched motion may still count.
High fog with a sparse palette can still pass every make gate after collapsing colours; the recipe now
warns about this. No minimum-colour or contrast gate was added.

The first validation run found four fixture errors from missing pulse `hot` fields; fixed before the passing
run. The wiki working copy has prose edits in Gates, Animating-A-Sprite, Making-Pixel-Art and
Versions-And-Upgrading. Existing numerical output and footers still describe the earlier verified release
until the coordinating session runs the new release archive.

Report-only flicker and cadence thresholds still need a hand-made calibration set. Ramp building,
fractional shift, flame, Lloyd palette refinement and `false_contours` remain deferred.

## Records

- [Wiki note](notes/2026-10-24-github-wiki.md), findings 10 to 12.
- [Log](log.md), latest follow-up.
