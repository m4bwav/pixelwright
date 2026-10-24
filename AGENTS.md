# Agent rules for pixelwright

Rules for any AI agent (Claude Code, Copilot, Cursor, Codex, Gemini CLI) working in this repository. `CLAUDE.md`
imports this file.

Read [README.md](README.md) first. Three skills live in [skills/](skills/): the hub `pixelwright` (with the one CLI,
`scripts/pxw.py`), `pixelwright-make` and `pixelwright-animate` (with the `sw.py` shim for the old name). The
evergreen unit sits at the repository root: RESEARCH, CHANGELOG, LEARNINGS, TESTS, `evals/evals.json`,
MAINTENANCE and `evergreen.json`.

## Rules

- Evergreen unit in pointer mode: before editing a skill, read `evergreen.json`. If `next_due` has passed or
  `contradiction` is set, say so and refresh after the task. Every edit to a SKILL.md or a reference gets a
  CHANGELOG entry with its reason (`R-`, `L-`, `T-` ids, or "user request").
- `pxw.py` stays Python 3.9+ with numpy and Pillow only, prints one JSON object per command (except `review`,
  which serves), exits 1 on a failed check and 2 on a usage error, makes no network calls, and runs on Windows,
  macOS and Linux.
- Every new effect, command or gate gets an offline test (`tests/test_pxw.py` for animation, `tests/test_make.py`
  for make) with its fixture drawn in code, and the test must fail when the behaviour breaks. A change to an
  existing effect or make step must keep its output byte-identical unless the CHANGELOG says why it changed
  (projects rely on reproducible sheets and sprites).
- artwright-pixel is the judge: call `aw.py pixel` as a gate, never copy its checks into `pxw.py`.
- No images in the repository except `.github/images/banner.jpg`. No project names, machine names, absolute paths
  or credentials in any file. `tests/check_skills.py` also flags every name listed in `.private-names.txt` (one per
  line, untracked); keep the client and people names of projects that use this plugin there.
- Skills stay under 200 lines with a description of at most 1,024 characters that names the siblings that own
  nearby requests (comfyui-gen renders stills; artwright-pixel measures).
- Before committing: `python tests/test_pxw.py`, `python tests/test_make.py` and `python tests/check_skills.py`.
- Versions: when a packaged file changes, bump `.claude-plugin/plugin.json` and `VERSION` in `pxw.py` together, and
  add CHANGELOG release notes. Tags and releases need the owner's go-ahead.
- No AI attribution anywhere: no AI co-author trailers and no AI credit lines in commits, pull requests
  or files.
