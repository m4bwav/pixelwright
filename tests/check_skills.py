"""Structure and public-safety checks for the pixelwright repository. Standard library only.

Run from the repository root: python tests/check_skills.py
Checks: the plugin manifest and its version against pxw.py; each skill's frontmatter, description and body length;
relative links in every markdown file; every reference reachable from SKILL.md; LF line endings; no images (but the
README banner); no
home-folder paths, no keys, no AI attribution; the evergreen companions.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT = {".md", ".py", ".json", ".yml", ".yaml", ".txt"}
IMAGES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
SKIP_DIRS = {".git", "__pycache__", "evals-results", "ai-docs"}
SKIP_FILES = {".private-names.txt"}
BANNER = ".github/images/banner.jpg"
DESC_MAX = 1024
BODY_MAX = 200
problems = []


def rel(p):
    return p.relative_to(ROOT).as_posix()


def files():
    for p in ROOT.rglob("*"):
        if p.is_file() and not (set(p.relative_to(ROOT).parts) & SKIP_DIRS) and p.name not in SKIP_FILES:
            yield p


def check_manifest():
    m = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    for k in ("name", "version", "description", "skills", "license"):
        if not m.get(k):
            problems.append("plugin.json missing %s" % k)
    pxw = (ROOT / "skills" / "pixelwright" / "scripts" / "pxw.py").read_text(encoding="utf-8")
    v = re.search(r'VERSION = "([^"]+)"', pxw)
    if not v or v.group(1) != m.get("version"):
        problems.append("pxw.py VERSION must match plugin.json version")


def check_skills():
    for sk in sorted((ROOT / "skills").iterdir()):
        md = sk / "SKILL.md"
        if not md.is_file():
            problems.append("%s has no SKILL.md" % rel(sk))
            continue
        text = md.read_text(encoding="utf-8")
        fm = re.match(r"---\n(.*?)\n---\n", text, re.S)
        if not fm:
            problems.append("%s: no frontmatter" % rel(md))
            continue
        name = re.search(r"^name: (.+)$", fm.group(1), re.M)
        desc = re.search(r"^description: (.+)$", fm.group(1), re.M)
        if not name or name.group(1).strip() != sk.name:
            problems.append("%s: name must equal the folder name" % rel(md))
        if not desc or len(desc.group(1)) > DESC_MAX:
            problems.append("%s: description missing or over %d characters" % (rel(md), DESC_MAX))
        body = text[fm.end():].splitlines()
        if len(body) > BODY_MAX:
            problems.append("%s: body %d lines (max %d)" % (rel(md), len(body), BODY_MAX))
        refs = sk / "references"
        if refs.is_dir():
            for r in refs.glob("*.md"):
                if "references/%s" % r.name not in text:
                    problems.append("%s not linked from SKILL.md" % rel(r))


def check_files():
    home = re.compile(r"[A-Za-z]:[\\/]+Users[\\/]|/home/[a-z]|/Users/[a-z]|[A-Za-z]:/m4bwa", re.I)
    key = re.compile(r"(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|Bearer [A-Za-z0-9]{20,})")
    attribution = re.compile(r"Co-Authored-By|Generated with (Claude|Copilot)", re.I)
    # names that must never go public (projects, people) live in an untracked file, so this check does not leak them
    private = ROOT / ".private-names.txt"
    names = [n.strip() for n in private.read_text(encoding="utf-8").splitlines() if n.strip()] if private.is_file() else []
    named = re.compile("|".join(re.escape(n) for n in names), re.I) if names else None
    for p in files():
        if p.suffix.lower() in IMAGES and rel(p) != BANNER:
            problems.append("image in repository: %s" % rel(p))
        if p.suffix.lower() not in TEXT or p.name == "check_skills.py":
            continue
        raw = p.read_bytes()
        if b"\r\n" in raw:
            problems.append("CRLF line endings: %s" % rel(p))
        text = raw.decode("utf-8", "replace")
        for rx, what in ((home, "absolute home path"), (key, "credential"), (attribution, "AI attribution"),
                         (named, "private name")):
            if rx and rx.search(text):
                problems.append("%s in %s" % (what, rel(p)))
        if p.suffix == ".md":
            for target in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", text):
                if "://" in target or target.startswith("mailto:"):
                    continue
                if not (p.parent / target).exists():
                    problems.append("broken link in %s: %s" % (rel(p), target))


def check_companions():
    for f in ("README.md", "RESEARCH.md", "CHANGELOG.md", "LEARNINGS.md", "TESTS.md", "MAINTENANCE.md",
              "evergreen.json", "evals/evals.json", "LICENSE", "SECURITY.md", "AGENTS.md", "CLAUDE.md"):
        if not (ROOT / f).is_file():
            problems.append("missing %s" % f)


check_manifest()
check_skills()
check_files()
check_companions()
if problems:
    print("\n".join(problems))
    sys.exit(1)
print("ok")
