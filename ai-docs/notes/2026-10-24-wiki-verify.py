"""Wiki verification for pixelwright: every command and output on the wiki, run against the released plugin.

    python ai-docs/notes/2026-10-24-wiki-verify.py --install --aw <artwright aw.py> --port 8799 > new.out.txt
    python ai-docs/notes/2026-10-24-wiki-verify.py --plugin <installed plugin folder> --aw <artwright aw.py>

Run it from a folder outside the repository, with a Python that has numpy and Pillow (and `claude` on PATH for
--install). The saved runs of 2026-10-24: .out.txt (Windows, Python 3.14.7, numpy 2.5.4, Pillow 13.0.0, --install,
--images), .py39.out.txt (Windows, Python 3.9.25, numpy 2.0.2, Pillow 11.3.0, --plugin on `git archive v0.6.0`) and
.linux.out.txt (Ubuntu on WSL, Python 3.14.4, numpy 2.5.4, Pillow 13.0.0, --plugin on the same archive). --aw was
artwright 0.4.0's aw.py from the v0.4.0 tag. --port 8799 because other servers held 8765 and 8766 on that machine.
Compare a new run with wikiwright's `diffout`; prove the pages with its `outputs` and `snippets`.

The published package is the plugin as Claude Code installs it. With --install the program runs
`claude plugin marketplace add m4bwav/pixelwright` and `claude plugin install pixelwright@pixelwright` into a
throwaway CLAUDE_CONFIG_DIR (the user's own Claude Code settings are never touched) and uses that copy; with
--plugin it uses a copy already installed, or an extracted `git archive v0.6.0`. Nothing runs from a working tree.

Every fixture is drawn here in code: an upscaled, blurred and noised "AI render" of a small mushroom sprite on a
near-white ground, the same sprite at a fractional 5.5x, a smooth gradient with no grid, a reference sprite for
`from:` palettes, a grass texture for `tile`, two palette files, and a 32x32 forge still with briefs and a plan
for the animation commands. No real artwork is used.

Output sections are '## label' lines, as wikiwright's diffout and outputs read them. Each case prints the page's
command after '$ ', its stdout, its stderr, then '$ echo $?' and the exit code. Commands on the pages read
`python pxw.py ...`; here pxw.py is the plugin's skills/pixelwright/scripts/pxw.py and sw.py the shim in
skills/pixelwright-animate/scripts/. Children run with HOME and USERPROFILE set to an empty folder, so artwright is
found only where a case names it (PIXELWRIGHT_AW). Masks: the scratch folder is <tmp>, the plugin folder <plugin>,
artwright's folder <artwright>, the review page's save time <time>. The program refuses to print its output if the
user name or home folder survives the masking. With --images DIR it also writes the wiki's pictures there.
"""
import argparse
import getpass
import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

BS = chr(92)
ap = argparse.ArgumentParser()
ap.add_argument("--install", action="store_true", help="install the plugin with claude into a throwaway config")
ap.add_argument("--plugin", help="an installed or extracted pixelwright folder")
ap.add_argument("--aw", help="artwright's aw.py from a release, for the aw_pixel gate cases")
ap.add_argument("--images", help="write the wiki's pictures into this folder")
ap.add_argument("--port", type=int, default=8765)
A = ap.parse_args()

WORK = os.path.realpath(tempfile.mkdtemp(prefix="pxwwiki_"))
RUN = os.path.join(WORK, "run")
HOMEDIR = os.path.join(WORK, "home")
os.makedirs(RUN)
os.makedirs(HOMEDIR)
OUT = []
REAL_HOME = os.path.expanduser("~")


def show(label, text):
    OUT.append("## " + label)
    OUT.append(text.rstrip())
    OUT.append("")


def forms(path):
    return [path.replace(BS, BS * 2), path, path.replace(BS, "/")]


MASKS = []  # (path, placeholder), longest first


def mask(text):
    for path, name in sorted(MASKS, key=lambda t: -len(t[0])):
        for f in forms(path):
            text = text.replace(f, name)
    text = re.sub(r'"updated": "[0-9T:-]+"', '"updated": "<time>"', text)
    return text.rstrip()


def env_for(extra=None):
    e = {k: v for k, v in os.environ.items() if k not in ("PIXELWRIGHT_AW", "SPRITEWRIGHT_AW")}
    e.update(HOME=HOMEDIR, USERPROFILE=HOMEDIR, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    e.update(extra or {})
    return e


def argv(command):
    args = shlex.split(command)
    flags = []
    if args[0] == "python":
        args = args[1:]
        while args and args[0].startswith("-") and args[0] != "-":
            flags.append(args.pop(0))
        if args and args[0] == "pxw.py":
            args[0] = PXW
        elif args and args[0] == "sw.py":
            args[0] = SHIM
        return [sys.executable] + flags + args
    return args


def case(label, command, cwd=None, env=None, shown=None):
    """Run one page command as the page shows it, from <tmp>/run (or cwd)."""
    p = subprocess.run(argv(command), cwd=cwd or RUN, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=env_for(env))
    lines = ["$ " + (shown or command)]
    if p.stdout.strip():
        lines.append(mask(p.stdout))
    if p.stderr.strip():
        lines.append(mask(p.stderr))
    lines += ["$ echo $?", str(p.returncode)]
    show(label, "\n".join(lines))
    return p


def write(rel, text):
    path = os.path.join(RUN, rel)
    os.makedirs(os.path.dirname(path) or RUN, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return path


def write_json(rel, obj, label):
    text = json.dumps(obj)
    write(rel, text + "\n")
    show(label, text)


def write_file(rel, text, label):
    """A recipe, brief or plan exactly as a page shows it: written verbatim, printed, and parsed."""
    write(rel, text.strip("\n") + "\n")
    show(label, text.strip("\n"))
    return json.loads(text)


def save(a, rel):
    path = os.path.join(RUN, rel)
    os.makedirs(os.path.dirname(path) or RUN, exist_ok=True)
    Image.fromarray(a.astype(np.uint8), "RGBA").save(path)
    return path


def load(rel):
    return np.array(Image.open(os.path.join(RUN, rel)).convert("RGBA"))


def colours(a):
    return len(np.unique(a[a[..., 3] > 0][:, :3], axis=0))


# ---- the plugin under test
if A.install:
    cfg = os.path.join(WORK, "claude-config")
    claude = shutil.which("claude")
    for label, cmd in (("install: marketplace", "claude plugin marketplace add m4bwav/pixelwright"),
                       ("install: plugin", "claude plugin install pixelwright@pixelwright")):
        p = subprocess.run([claude] + cmd.split()[1:], cwd=RUN, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=dict(os.environ, CLAUDE_CONFIG_DIR=cfg))
        show(label, "\n".join(["$ " + cmd, (p.stdout + p.stderr).strip(), "$ echo $?", str(p.returncode)]))
    cache = Path(cfg) / "plugins" / "cache" / "pixelwright" / "pixelwright"
    PLUGIN = str(sorted(cache.iterdir())[-1])
    v = subprocess.run([claude, "--version"], capture_output=True, text=True).stdout.strip()
    MASKS.append((cfg, "<claude-config>"))
else:
    PLUGIN = os.path.realpath(A.plugin)
    v = "not used (--plugin)"
MASKS += [(PLUGIN, "<plugin>"), (WORK, "<tmp>"), (str(Path(np.__file__).parents[1]), "<site-packages>"),
          (sys.base_prefix, "<python>"), (sys.prefix, "<python>")]
PXW = os.path.join(PLUGIN, "skills", "pixelwright", "scripts", "pxw.py")
SHIM = os.path.join(PLUGIN, "skills", "pixelwright-animate", "scripts", "sw.py")
AW = os.path.realpath(A.aw) if A.aw else None
if AW:
    MASKS.append((str(Path(AW).parents[3]), "<artwright>"))
manifest = json.loads(Path(PLUGIN, ".claude-plugin", "plugin.json").read_text(encoding="utf-8"))
show("installed", "\n".join([
    "pixelwright %s from %s" % (manifest["version"], "claude plugin install" if A.install else "--plugin"),
    "Claude Code %s" % v,
    "Python %s, numpy %s, Pillow %s on %s" % (sys.version.split()[0], np.__version__, Image.__version__,
                                               "Windows" if os.name == "nt" else sys.platform),
    "artwright aw.py %s" % (subprocess.run([sys.executable, AW, "--version"], capture_output=True,
                                           text=True).stdout.strip() if AW else "not given"),
]))

# ---- fixtures, drawn in code
INK, CAP, CAPHI, SPOT = [40, 24, 36], [200, 52, 56], [236, 104, 96], [248, 240, 226]
STEM, STEMSH, GROUND = [232, 214, 180], [184, 158, 128], [244, 242, 236]


def mushroom():
    """A 20x20 mushroom: dark outline, red cap with a highlight and three spots, a cream stem with a shaded side."""
    a = np.zeros((20, 20, 4), np.uint8)
    yy, xx = np.mgrid[0:20, 0:20]
    cap_out = (((xx - 9.5) / 9.6) ** 2 + ((yy - 8.5) / 8.0) ** 2 <= 1) & (yy <= 10)
    stem_out = (xx >= 6) & (xx <= 13) & (yy >= 9) & (yy <= 19)
    a[cap_out | stem_out] = INK + [255]
    cap_in = (((xx - 9.5) / 8.4) ** 2 + ((yy - 8.5) / 6.9) ** 2 <= 1) & (yy <= 9)
    stem_in = (xx >= 7) & (xx <= 12) & (yy >= 11) & (yy <= 18)
    a[stem_in] = STEM + [255]
    a[stem_in & (xx >= 11)] = STEMSH + [255]
    a[cap_in] = CAP + [255]
    a[cap_in & (yy <= 4) & (xx <= 9)] = CAPHI + [255]
    for y, x in ((3, 11), (6, 4), (6, 14)):
        a[y:y + 2, x:x + 2] = SPOT + [255]
    return a


def render(a, s=6, off=4, pad=8, seed=11):
    """What an image model hands back: the sprite at 6x on a 4 px offset over a near-white ground, blurred, noised."""
    big = np.repeat(np.repeat(a, s, 0), s, 1)
    h, w = big.shape[:2]
    c = np.zeros((h + off + pad, w + off + pad, 4), np.uint8)
    c[...] = GROUND + [255]
    m = big[..., 3] > 0
    c[off:off + h, off:off + w][m] = big[m]
    b = np.array(Image.fromarray(c, "RGBA").filter(ImageFilter.GaussianBlur(1.0))).astype(np.int16)
    b[..., :3] += np.random.default_rng(seed).integers(-6, 7, b[..., :3].shape).astype(np.int16)
    return np.clip(b, 0, 255).astype(np.uint8)


def fractional(a):
    """The sprite at 5.5x, nearest neighbour, on the same ground: blocks of 5 and 6 pixels alternate."""
    g = np.zeros_like(a)
    g[...] = GROUND + [255]
    g[a[..., 3] > 0] = a[a[..., 3] > 0]
    return np.array(Image.fromarray(g, "RGBA").resize((110, 110), Image.NEAREST))


def gradient():
    """A smooth 128x96 painted gradient with a little noise: no pixel grid anywhere."""
    yy, xx = np.mgrid[0:96, 0:128].astype(np.float64)
    a = np.zeros((96, 128, 4), np.float64)
    a[..., 0] = 40 + 180 * xx / 127
    a[..., 1] = 60 + 120 * yy / 95
    a[..., 2] = 200 - 120 * xx / 127
    a[..., :3] += np.random.default_rng(5).normal(0, 2, (96, 128, 3))
    a[..., 3] = 255
    return np.clip(np.round(a), 0, 255)


def chest():
    """A 12x12 chest in the set's colours, for from: palettes."""
    a = np.zeros((12, 12, 4), np.uint8)
    a[1:11, 1:11] = INK + [255]
    a[2:10, 2:10] = [164, 100, 34, 255]
    a[4:6, 2:10] = CAP + [255]
    a[6, 5:7] = SPOT + [255]
    a[3, 3:9] = [120, 64, 30, 255]
    return a


def grass():
    """A 16x16 grass texture that does not wrap: denser on the left than on the right."""
    rng = np.random.default_rng(3)
    a = np.zeros((16, 16, 4), np.uint8)
    a[...] = [56, 140, 64, 255]
    yy, xx = np.mgrid[0:16, 0:16]
    dark = rng.random((16, 16)) < 0.45 * (1 - xx / 16)
    light = rng.random((16, 16)) < 0.25 * (yy / 16)
    a[dark] = [36, 100, 48, 255]
    a[light] = [110, 180, 80, 255]
    return a


STONE, STONED, DARK = [110, 108, 116], [72, 70, 80], [40, 30, 34]
FIRE, FIREHI = [236, 120, 32], [252, 200, 80]


def forge():
    """A 32x32 forge still: stone body with mortar lines, a dark mouth with a fire, a chimney, clear sky above."""
    a = np.zeros((32, 32, 4), np.uint8)
    a[14:32, 4:28] = STONE + [255]
    a[14:32:4, 4:28] = STONED + [255]
    a[4:14, 19:24] = STONED + [255]
    a[4:6, 18:25] = STONE + [255]
    a[21:30, 11:21] = DARK + [255]
    a[24:30, 12:20] = FIRE + [255]
    a[26:30, 14:18] = FIREHI + [255]
    return a


M = mushroom()
save(render(M), "render.png")
save(fractional(M), "frac.png")
save(gradient(), "painting.png")
save(chest(), "chest.png")
save(grass(), "grass.png")
save(forge(), "forge.png")
show("fixtures", "\n".join("%s: %dx%d, %d colours" % (n, *Image.open(os.path.join(RUN, n)).size, colours(load(n)))
                          for n in ("render.png", "frac.png", "painting.png", "chest.png", "grass.png",
                                    "forge.png")))
write("mine.hex", "1a1c2c\n5d275d\nb13e53\nef7d57\nffcd75\nf4f4f4\n")
write("mine.gpl", "GIMP Palette\nName: mine\nColumns: 4\n#\n 26  28  44\tink\n177  62  83\tred\n"
                  "239 125  87\torange\n244 244 244\twhite\n")
show("file: mine.hex", Path(RUN, "mine.hex").read_text(encoding="utf-8"))
show("file: mine.gpl", Path(RUN, "mine.gpl").read_text(encoding="utf-8"))

# ---- Getting started
case("version", "python pxw.py --version")
case("help", "python pxw.py --help")
case("help snap", "python pxw.py snap --help")
case("doctor", "python pxw.py doctor")
case("doctor without numpy", "python -S pxw.py doctor", shown="python pxw.py doctor")

# ---- Home and Making pixel art: the render
write_json("recipe.json", {"id": "mushroom", "input": "render.png", "palette": 8,
                           "crop": {"pad": 1, "size": "32x32"}}, "file: recipe.json")
case("make", "python pxw.py make recipe.json out")
made = load("out/mushroom.png")
show("make: result", "out/mushroom.png: %dx%d, %d colours, alpha values %s; files in out: %s" % (
    made.shape[1], made.shape[0], colours(made), sorted(int(v) for v in np.unique(made[..., 3])),
    ", ".join(sorted(os.listdir(os.path.join(RUN, "out"))))))
clear = made[made[..., 3] == 0]
show("make: transparent pixels", "out/mushroom.png: %d transparent pixels, stored as %s" % (
    len(clear), sorted({tuple(int(v) for v in px) for px in clear})))
show("file: out/mushroom.gpl",Path(RUN, "out", "mushroom.gpl").read_text(encoding="utf-8"))

case("snap render", "python pxw.py snap render.png snapped.png")
case("snap fractional", "python pxw.py snap frac.png frac-snapped.png")
case("snap painting", "python pxw.py snap painting.png painting-snapped.png")
case("snap forced", "python pxw.py snap render.png forced.png --scale 6 --offset 4,4")
case("bg", "python pxw.py bg snapped.png cleared.png")
case("bg transparent", "python pxw.py bg cleared.png cleared2.png")
case("palette pico-8", "python pxw.py palette cleared.png pico.png --palette pico-8")
case("clean", "python pxw.py clean pico.png clean.png --orphans --outline selective")
case("crop", "python pxw.py crop clean.png crop.png --pad 1 --size 32x32")
case("crop pow2", "python pxw.py crop clean.png crop2.png --size pow2")
case("crop too small", "python pxw.py crop clean.png tiny.png --size 16x16")

write_file("recipe-full.json", """
{"id": "mushroom", "input": "render.png", "palette": {"colours": 8},
 "clean": {"orphans": true, "thin": true, "outline": "selective", "light": "top-left"},
 "crop": {"pad": 1, "size": "32x32", "anchor": "bottom"}}
""", "file: recipe-full.json")
case("make full", "python pxw.py make recipe-full.json out-full")
write_json("recipe-clean-only.json", {"id": "mushroom", "input": "render.png", "palette": 8,
                                      "clean": {"outline": "auto"}}, "file: recipe-clean-only.json")
case("make clean without orphans", "python pxw.py make recipe-clean-only.json out-clean")
write_json("recipe-big.json", {"id": "mushroom", "input": "render.png", "palette": "pico-8",
                               "crop": {"size": "16x16"}}, "file: recipe-big.json")
case("make crop too small", "python pxw.py make recipe-big.json out-big")
write_json("recipe-painting.json", {"id": "painting", "input": "painting.png", "palette": 8},
           "file: recipe-painting.json")
case("make painting", "python pxw.py make recipe-painting.json out-painting")

# ---- Palettes
case("palettes", "python pxw.py palettes")
case("palette gpl", "python pxw.py palette cleared.png q.png --palette pico-8 --gpl pico.gpl")
show("file: pico.gpl", Path(RUN, "pico.gpl").read_text(encoding="utf-8"))
case("palette hex", "python pxw.py palette cleared.png hex.png --palette mine.hex")
case("palette gpl file", "python pxw.py palette cleared.png gpl.png --palette mine.gpl")
case("palette from", "python pxw.py palette cleared.png set.png --palette from:chest.png")
case("palette colours", "python pxw.py palette cleared.png six.png --colours 6")
case("palette dither", "python pxw.py palette painting.png dithered.png --palette pico-8 --dither bayer4")
case("palette plain", "python pxw.py palette painting.png banded.png --palette pico-8")
case("palette both", "python pxw.py palette cleared.png x.png --palette pico-8 --colours 6")
case("palette missing", "python pxw.py palette cleared.png x.png --palette sweetie-16")
case("palette bad dither", "python pxw.py palette cleared.png x.png --palette pico-8 --dither floyd")
write_file("recipe-set.json", """
{"sprites": [
  {"id": "mushroom", "input": "render.png", "palette": "from:chest.png", "crop": {"pad": 1, "size": "32x32"}},
  {"id": "chest", "input": "chest.png", "snap": false, "palette": "from:chest.png"}
]}
""", "file: recipe-set.json")
case("make set", "python pxw.py make recipe-set.json out-set")

# ---- tiles
case("tile", "python pxw.py tile grass.png grass-tile.png")
write_json("recipe-tile.json", {"id": "grass", "input": "grass.png", "snap": False, "background": "none",
                                "palette": "from:grass.png", "tile": True}, "file: recipe-tile.json")
case("make tile", "python pxw.py make recipe-tile.json out-tile")

# ---- Gates: budget, and artwright's verdict
write_json("recipe-budget.json", {"id": "mushroom", "input": "render.png", "palette": "pico-8", "budget": 4},
           "file: recipe-budget.json")
case("make over budget", "python pxw.py make recipe-budget.json out-budget")
if AW:
    case("doctor with artwright", "python pxw.py doctor", env={"PIXELWRIGHT_AW": AW})
    case("make with artwright", "python pxw.py make recipe.json out-aw", env={"PIXELWRIGHT_AW": AW})
    case("make full with artwright", "python pxw.py make recipe-full.json out-full-aw", env={"PIXELWRIGHT_AW": AW})
    case("make painting with artwright", "python pxw.py make recipe-painting.json out-painting-aw",
         env={"PIXELWRIGHT_AW": AW})
    # why the outlined sprite fails: artwright reads the colour of transparent pixels, which pxw.py stores as
    # RGBA 0,0,0,0, so a dark outline between transparency and a bright fill measures as a blend pixel
    box = np.zeros((12, 12, 4), np.uint8)
    box[1:11, 1:11] = INK + [255]
    box[2:10, 2:10] = CAP + [255]
    save(box, "box-black.png")
    box[box[..., 3] == 0] = [255, 255, 255, 0]
    save(box, "box-white.png")
    for name in ("box-black.png", "box-white.png"):
        p = subprocess.run([sys.executable, AW, "pixel", name], cwd=RUN, capture_output=True, text=True,
                           encoding="utf-8", env=env_for())
        item = json.loads(p.stdout)["items"][0]
        show("artwright: " + name, "%s: transparent pixels stored as %s, transitional_pixels %s, problems %s" % (
            name, [int(v) for v in load(name)[0, 0]], item["transitional_pixels"], item["problems"]))

# ---- Animating a sprite
BRIEF = write_file("brief.json", """
{
  "id": "forge",
  "still": "forge.png",
  "motion": "Use: the fire flares and sparks leave the chimney. Idle: the fire flickers. Place: powers on.",
  "extraColours": [[255, 250, 220]],
  "regions": {
    "fire":  {"rects": [[11, 21, 21, 30]], "select": "warm"},
    "front": {"rects": [[4, 14, 28, 32]]},
    "sky":   {"rects": [[0, 0, 32, 14]], "alpha": true}
  },
  "animations": {
    "use": {"frames": 10, "focal": "fire", "fps": 12, "tracks": [
      {"effect": "pulse", "region": "fire", "hot": [255, 250, 220],
       "curve": [0, 0.5, 1, 1, 0.8, 0.6, 0.4, 0.2, 0.1, 0]},
      {"effect": "spill", "region": "front", "source": [12, 24, 20, 30], "tint": [90, 50, 10], "radius": 8,
       "curve": [0, 0.5, 1, 1, 0.8, 0.6, 0.4, 0.2, 0.1, 0]},
      {"effect": "sparks", "region": "sky", "source": [19, 3, 24, 4], "bornFrames": [1, 2, 3],
       "colours": [[255, 250, 220], [255, 150, 40], [200, 70, 20]]}
    ]},
    "idle": {"frames": 8, "rest": "none", "focal": "fire", "tracks": [
      {"effect": "pulse", "region": "fire", "hot": [255, 250, 220],
       "curve": [0.2, 0.6, 1, 0.6, 0.2, 0.5, 0.9, 0.5]}
    ]},
    "place": {"frames": 8, "focal": "fire", "tracks": [
      {"effect": "darken", "region": "front", "curve": [1, 1, 0.9, 0.7, 0.4, 0.6, 0.2, 0]}
    ]}
  }
}
""", "file: brief.json")
case("grid", "python pxw.py grid forge.png grid.png")
case("mask", "python pxw.py mask brief.json mask.png")
case("frames", "python pxw.py frames brief.json out-anim")
show("frames: files", "\n".join(sorted(p.relative_to(Path(RUN, "out-anim")).as_posix()
                                       for p in Path(RUN, "out-anim").rglob("*") if p.is_file())))
g = json.loads(Path(RUN, "out-anim", "forge.gates.json").read_text(encoding="utf-8"))
show("file: out-anim/forge.gates.json (use)", json.dumps(g["use"], indent=2))
show("file: out-anim/forge.gates.json (idle)", json.dumps(g["idle"], indent=2))
sheet = load("out-anim/forge-use-10f.png")
still = load("forge.png")
show("frames: checks", "\n".join([
    "sheet forge-use-10f.png: %dx%d" % (sheet.shape[1], sheet.shape[0]),
    "frame 0 equals forge.png byte for byte: %s" % bool((sheet[:, :32] == still).all()),
    "frames outside the regions changed: %d pixels" % int(sum(
        ((sheet[:, i * 32:(i + 1) * 32] != still).any(-1) & ~np.pad(np.ones((18, 24), bool), ((14, 0), (4, 4)))
         & ~np.pad(np.ones((14, 32), bool), ((0, 18), (0, 0)))).sum() for i in range(10))),
]))
case("frames only", "python pxw.py frames brief.json out-use --only use")
case("frames again", "python pxw.py frames brief.json out-again --only use")
same = Path(RUN, "out-use", "forge-use-10f.png").read_bytes() == Path(RUN, "out-again",
                                                                       "forge-use-10f.png").read_bytes()
show("frames: two runs", "out-use/forge-use-10f.png and out-again/forge-use-10f.png identical: %s" % same)
case("shim", "python sw.py frames brief.json out-shim --only use")
case("shim version", "python sw.py --version")
if AW:
    case("shim doctor with old variable", "python sw.py doctor", env={"SPRITEWRIGHT_AW": AW})
show("shim: same sheet", "out-shim/forge-use-10f.png identical to out-use/forge-use-10f.png: %s" % (
    Path(RUN, "out-shim", "forge-use-10f.png").read_bytes() == Path(RUN, "out-use", "forge-use-10f.png").read_bytes()))
case("contact", "python pxw.py contact out-anim/forge-use-10f.png contact.png --frames 10")
case("pack", "python pxw.py pack strip.png out-anim/forge-use-10f/f00.png out-anim/forge-use-10f/f03.png")
case("pack sizes differ", "python pxw.py pack bad.png forge.png chest.png")

# construction in front of place
case("buildup", "python pxw.py buildup brief.json brief-built.json")
case("frames buildup", "python pxw.py frames brief-built.json out-built --only place")
write_file("plan.json", """
{"frames": 8,
 "regions": {"p_chimney": {"rects": [[18, 4, 25, 14]]}, "p_body": {"rects": [[4, 14, 28, 32]]}},
 "steps": [{"part": "p_body", "how": "weld", "dir": "up", "at": [0, 5]},
           {"part": "p_chimney", "how": "crane", "at": [3, 8]}]}
""", "file: plan.json")
case("assemble", "python pxw.py assemble brief.json brief-assembled.json --plan plan.json")
case("frames assembled", "python pxw.py frames brief-assembled.json out-assembled --only place")
write_json("plan-short.json", {"frames": 4, "regions": {"p_chimney": {"rects": [[18, 4, 25, 14]]}},
                               "steps": [{"part": "p_chimney", "how": "crane", "at": [0, 4]}]},
           "file: plan-short.json")
case("assemble uncovered", "python pxw.py assemble brief.json brief-partial.json --plan plan-short.json")

# failing gates and errors
def variant(rel, key, text, label):
    """brief.json with one part replaced by the text a page shows (its "animations" or one more region)."""
    b = json.loads(json.dumps(BRIEF))
    part = json.loads(text)
    if key == "animations":
        b["animations"] = part
    else:
        b["regions"].update(part)
    write(rel, json.dumps(b) + "\n")
    show(label, text.strip("\n"))


variant("brief-weak.json", "animations", """
{"use": {"frames": 6, "focal": "fire", "tracks": [
  {"effect": "pulse", "region": "fire", "hot": [255, 250, 220], "strength": 0.05,
   "curve": [0, 0.5, 1, 1, 0.5, 0]}]}}
""", "file: brief-weak.json animations")
case("frames weak", "python pxw.py frames brief-weak.json out-weak")
variant("brief-rest.json", "animations", """
{"use": {"frames": 6, "focal": "fire", "tracks": [
  {"effect": "pulse", "region": "fire", "hot": [255, 250, 220], "curve": [1, 1, 0.8, 0.5, 0.2, 0.1]}]}}
""", "file: brief-rest.json animations")
case("frames rest", "python pxw.py frames brief-rest.json out-rest")
variant("brief-odd.json", "animations", """
{"use": {"frames": 4, "tracks": [{"effect": "wobble", "region": "fire"}]}}
""", "file: brief-odd.json animations")
case("frames unknown effect", "python pxw.py frames brief-odd.json out-odd")
variant("brief-smoke.json", "animations", """
{"smoke": {"frames": 8, "rest": "none", "focal": "sky", "tracks": [
  {"effect": "puffs", "region": "sky", "source": [21, 4], "bornFrames": [0, 4], "life": 8,
   "colours": [[214, 210, 220], [168, 164, 176]], "seed": 5}]}}
""", "file: brief-smoke.json animations")
case("frames smoke loop", "python pxw.py frames brief-smoke.json out-smoke")
g = json.loads(Path(RUN, "out-smoke", "forge.gates.json").read_text(encoding="utf-8"))
show("file: out-smoke/forge.gates.json (smoke)", json.dumps(g["smoke"], indent=2))
variant("brief-empty.json", "regions", """
{"screen": {"rects": [[4, 14, 10, 20]], "select": "cool"}}
""", "file: brief-empty.json extra region")
case("mask empty", "python pxw.py mask brief-empty.json mask2.png")
case("snap missing file", "python pxw.py snap nothing.png x.png")
case("no command", "python pxw.py")
lines = []
for cmd in ("python pxw.py", "python pxw.py palette cleared.png x.png --palette pico-8 --dither floyd",
            "python pxw.py palette cleared.png x.png --palette pico-8 --colours 6",
            "python pxw.py crop clean.png tiny.png --size 16x16", "python pxw.py snap nothing.png x.png"):
    p = subprocess.run(argv(cmd), cwd=RUN, capture_output=True, text=True, encoding="utf-8", env=env_for())
    lines.append("%s: exit %d, stdout %d lines, stderr %d lines" % (
        cmd, p.returncode, len(p.stdout.splitlines()), len(p.stderr.splitlines())))
show("streams", "\n".join(lines))

# ---- review page
batch = Path(RUN, "batch", "forge")
batch.mkdir(parents=True)
shutil.copy(os.path.join(RUN, "forge.png"), batch / "forge.png")
(batch / "brief.json").write_text(json.dumps(BRIEF), encoding="utf-8")
case("frames for review", "python pxw.py frames batch/forge/brief.json batch/forge/out --root batch/forge")
with socket.socket() as probe:
    if probe.connect_ex(("127.0.0.1", A.port)) == 0:
        sys.exit("port %d is busy; pass --port" % A.port)
cmd = "python pxw.py review batch --port %d" % A.port
srv = subprocess.Popen(argv(cmd), cwd=RUN, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                       encoding="utf-8", env=env_for())
first = srv.stdout.readline()
url = "http://127.0.0.1:%d/" % A.port
page = urllib.request.urlopen(url, timeout=10).read().decode("utf-8")
titles = re.findall(r"<h2>(.*?) <span>(.*?)</span></h2>", page)
gate_lines = re.findall(r"<p class=gate>(.*?)</p>", page)
req = urllib.request.Request(url + "picks", data=json.dumps(
    {"forge/use": {"pick": "keep"}, "forge/idle": {"pick": "redo", "note": "slower flicker"}}).encode("utf-8"),
    method="POST", headers={"Content-Type": "application/json"})
status = urllib.request.urlopen(req, timeout=10).status
busy = subprocess.run(argv(cmd), cwd=RUN, capture_output=True, text=True, encoding="utf-8", env=env_for())
page2 = urllib.request.urlopen(url, timeout=10).read().decode("utf-8")
srv.terminate()  # by its own process handle, never by image name
srv.wait(timeout=10)
show("review", "\n".join(["$ " + cmd, mask(first)] +
                         ["section: %s, %s" % t for t in titles] + ["gate line: " + gl for gl in gate_lines]))
show("review: picks saved", "POST /picks answered %d\n%s" % (status, mask(
    Path(RUN, "batch", "picks.json").read_text(encoding="utf-8"))))
show("review: after picks", "\n".join("section: %s, %s" % t
                                      for t in re.findall(r"<h2>(.*?) <span>(.*?)</span></h2>", page2)))
show("review busy port", "\n".join(["$ " + cmd, mask(busy.stdout), "$ echo $?", str(busy.returncode)]))

# ---- a CI check over make reports (Gates page)
CI_SNIPPET = '''
import json
import sys
from pathlib import Path

failed = []
for path in sorted(Path("out-set").glob("*.make.json")) + sorted(Path("out-budget").glob("*.make.json")):
    report = json.loads(path.read_text(encoding="utf-8"))
    if not report["ok"]:
        failed.append(path.as_posix())
print("failed:", failed or "none")
sys.exit(1 if failed else 0)
'''
write("check_makes.py", CI_SNIPPET.strip() + "\n")
case("ci check", "python check_makes.py")

# ---- Development: the repository's own tests, from the installed copy
for label, cmd in (("tests: animation", "python tests/test_pxw.py"), ("tests: make", "python tests/test_make.py"),
                   ("tests: structure", "python tests/check_skills.py")):
    p = subprocess.run([sys.executable] + cmd.split()[1:], cwd=PLUGIN, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env_for())
    tail = [ln for ln in (p.stdout + p.stderr).strip().splitlines() if ln.strip()][-2:]
    tail = [re.sub(r"Ran ([0-9]+) tests? in [0-9.]+s", r"Ran \1 tests in <s>s", ln) for ln in tail]
    show(label, "\n".join(["$ " + cmd] + [mask(ln) for ln in tail] + ["$ echo $?", str(p.returncode)]))

# ---- pictures for the wiki
if A.images:
    img = Path(A.images)
    img.mkdir(parents=True, exist_ok=True)
    r = Image.open(os.path.join(RUN, "render.png"))
    r.resize((r.width * 2, r.height * 2), Image.NEAREST).save(img / "render-2x.png")
    m = Image.open(os.path.join(RUN, "out", "mushroom.png"))
    m.resize((m.width * 8, m.height * 8), Image.NEAREST).save(img / "mushroom-make-8x.png")
    sh = Image.open(os.path.join(RUN, "out-anim", "forge-use-10f.png")).convert("RGBA")
    frames = []
    for i in range(10):
        f = Image.new("RGBA", (32, 32), (34, 34, 42, 255))
        f.alpha_composite(sh.crop((i * 32, 0, (i + 1) * 32, 32)))
        frames.append(f.convert("RGB").resize((256, 256), Image.NEAREST))
    frames += [frames[0]] * 6
    frames[0].save(img / "forge-use-8x.gif", save_all=True, append_images=frames[1:], duration=83, loop=0)
    gif = Image.open(img / "forge-use-8x.gif")
    show("images", "render-2x.png, mushroom-make-8x.png, forge-use-8x.gif written; the GIF stores %d ms a frame "
                   "(83 asked)" % gif.info["duration"])

# ---- leak guard: the user name as a path part, or the home folder, must not survive the masks
text = "\n".join(OUT) + "\n"
user = re.escape(getpass.getuser())
leak = re.search(r"(?i)[/\\]" + user + r"(?:[/\\\"']|$)", text) or any(f in text for f in forms(REAL_HOME))
if leak:
    at = leak.start() if hasattr(leak, "start") else min(text.find(f) for f in forms(REAL_HOME) if f in text)
    sys.exit("refusing to print: the user name or home folder survived the masking (section %s)"
             % text[:at].rsplit("\n## ", 1)[-1].split("\n", 1)[0])
sys.stdout.reconfigure(encoding="utf-8", newline="\n")
sys.stdout.write(text)
shutil.rmtree(WORK, ignore_errors=True)
