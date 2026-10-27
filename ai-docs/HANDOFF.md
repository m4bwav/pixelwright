# pixelwright handoff

## Current work

0.8.4 is released from merged PR #17 (`f3b448ed`). The wiki is published as `8a425d3`.
The follow-up was based on the 0.8.3 source and limited to flicker motion
matching, its tests, the fog warning and fixture, and the format of `flicker_at`. Source and manifest versions
both say 0.8.4. No effect or make output is meant to change.

## Next single action

Commit these publication records and the exact `2026-10-26-wiki-verify-084.out.txt` transcript in the
coordinating session's docs-only follow-up PR, regenerate INDEX, and merge after its checks pass.
No further runtime fix or release is owed by this follow-up.

The released-tag verifier passed on Windows with Python 3.14.6, numpy 2.5.2 and Pillow 12.3.0:
55 animation tests, 37 make tests, structure checks, exit 0 and no stderr.
Wiki gates: 11 pages, 0 check errors; 206 outputs checked, 0 missing, 1 historical-install skip;
1 snippet block, 6 commands, 0 missing; prose 0 strong and 41 weak findings.
Live: 11 pages, 0 failures, 23 anchors, 0 broken.

## Limits

The motion check is a heuristic: it matches incoming and outgoing steps within 1 px. A spark over clear
sky may change colour; motion over opaque art needs matching RGBA. Unmatched motion may still count.
High fog with a sparse palette can still pass every make gate after collapsing colours; the recipe now
warns about this. No minimum-colour or contrast gate was added.

The first validation run found four fixture errors from missing pulse `hot` fields; fixed before the passing
run. The wiki pages and footer now describe 0.8.4. The forge example still counts 3 unmatched flicker locations
and still fails a cap of 0. The historical 0.8.2 install is explicitly marked and points to its saved
evidence. The old warning block and its fragile source line number were removed.
Python 3.9 and Linux were not re-run for this update.

Flicker is report-only unless an animation sets `max_flicker_pixels`; cadence remains report-only.
Threshold calibration still needs a hand-made pixel-art set from the owner. Ramp building,
fractional shift, flame, Lloyd palette refinement and `false_contours` remain deferred.

## Records

- [Wiki note](notes/2026-10-24-github-wiki.md), findings 10 to 12.
- [Log](log.md), latest follow-up.
- [Merged PR #17](https://github.com/m4bwav/pixelwright/pull/17).
- [Release v0.8.4](https://github.com/m4bwav/pixelwright/releases/tag/v0.8.4).
- [Published wiki](https://github.com/m4bwav/pixelwright/wiki), commit
  `8a425d338f817a0f89cbd6a20b83787578dfdf35`.
