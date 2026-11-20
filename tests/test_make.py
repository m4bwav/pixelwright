"""Offline tests for pxw.py's make commands (snap, bg, palette, clean, crop, tile, make). Fixtures are drawn in code;
nothing is downloaded and no image is committed.

Run from the repository root: python tests/test_make.py
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
PXW = ROOT / "skills" / "pixelwright" / "scripts" / "pxw.py"
SHIM = ROOT / "skills" / "pixelwright-animate" / "scripts" / "sw.py"
sys.path.insert(0, str(PXW.parent))
import pxw  # noqa: E402

INK = [24, 20, 37]
RED = [190, 38, 51]
PINK = [224, 111, 139]
GLASS = [178, 220, 239]
CORK = [164, 100, 34]
SKY = [120, 170, 230]


def draw_sprite():
    """A 16x16 potion: cork, glass neck, round red body with a pink highlight, a one-pixel dark outline, clear
    background. No orphan pixels, so cleaning leaves it alone."""
    a = np.zeros((16, 16, 4), np.uint8)
    yy, xx = np.mgrid[0:16, 0:16]
    body = (yy - 10) ** 2 + (xx - 7.5) ** 2 <= 30
    a[body] = INK + [255]
    a[((yy - 10) ** 2 + (xx - 7.5) ** 2 <= 18)] = RED + [255]
    a[8:10, 4:6] = PINK + [255]
    a[2:6, 5:11] = INK + [255]
    a[3:6, 6:10] = GLASS + [255]
    a[1:3, 6:10] = CORK + [255]
    a[0, 6:10] = INK + [255]
    return a


def upscale(a, s, offset=0, bg=None, pad=0):
    """Nearest upscale by s on a canvas, shifted by offset, on a solid background (or transparent)."""
    big = np.repeat(np.repeat(a, s, 0), s, 1)
    h, w = big.shape[:2]
    c = np.zeros((h + offset + pad, w + offset + pad, 4), np.uint8)
    if bg is not None:
        c[...] = bg + [255]
    m = big[..., 3] > 0
    view = c[offset:offset + h, offset:offset + w]
    view[m] = big[m]
    return c


def tight(a):
    ys, xs = np.nonzero(a[..., 3])
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def save(a, path):
    Image.fromarray(a.astype(np.uint8), "RGBA").save(path)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.sprite = draw_sprite()
        save(self.sprite, self.dir / "potion.png")

    def tearDown(self):
        self.tmp.cleanup()

    def run_pxw(self, *args, script=PXW):
        r = subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True,
                           cwd=self.dir)
        return r.returncode, json.loads(r.stdout) if r.stdout.strip().startswith("{") else r.stdout + r.stderr

    def load(self, name):
        return np.array(Image.open(self.dir / name).convert("RGBA"))



class TestErrors(Base):
    def test_missing_input_prints_one_json_object(self):
        code, res = self.run_pxw("snap", "nowhere.png", "s.png")
        self.assertEqual(code, 1)
        self.assertFalse(res["ok"])
        self.assertIn("nowhere.png", res["error"])

    def test_find_aw_looks_in_claude_config_dir_first(self):
        aw = self.dir / "cfg" / "plugins" / "cache" / "artwright" / "scripts" / "aw.py"
        aw.parent.mkdir(parents=True)
        aw.write_text("")
        old = {k: pxw.os.environ.pop(k, None) for k in ("PIXELWRIGHT_AW", "SPRITEWRIGHT_AW", "CLAUDE_CONFIG_DIR")}
        try:
            pxw.os.environ["CLAUDE_CONFIG_DIR"] = str(self.dir / "cfg")
            self.assertEqual(pxw.find_aw(), aw)
        finally:
            pxw.os.environ.pop("CLAUDE_CONFIG_DIR", None)
            pxw.os.environ.update({k: v for k, v in old.items() if v is not None})

class TestSnap(Base):
    def test_clean_integer_upscale_comes_back_exactly(self):
        save(upscale(self.sprite, 4), self.dir / "big.png")
        code, res = self.run_pxw("snap", "big.png", "s.png")
        self.assertEqual(code, 0, res)
        self.assertEqual(res["scale"], [4, 4])
        self.assertTrue(np.array_equal(self.load("s.png"), self.sprite))

    def test_blurred_noisy_offset_render_snaps_back_after_make(self):
        """The AI-render case: scale 5, a 3 px offset, a solid sky, a blur and noise. The make pipeline (snap,
        background, palette from the original's colours, binary alpha, tight crop) must return the sprite exactly."""
        big = upscale(self.sprite, 5, offset=3, bg=SKY, pad=2)
        img = Image.fromarray(big, "RGBA").filter(ImageFilter.GaussianBlur(1.0))
        a = np.array(img).astype(np.int16)
        rng = np.random.default_rng(7)
        a[..., :3] += rng.integers(-6, 7, a[..., :3].shape).astype(np.int16)
        save(np.clip(a, 0, 255), self.dir / "render.png")
        rec = {"id": "potion", "input": "render.png", "palette": {"name": "from:potion.png"},
               "clean": {"alpha": 128}, "crop": {"pad": 0}}
        (self.dir / "r.json").write_text(json.dumps(rec))
        code, res = self.run_pxw("make", "r.json", "out", "--no-aw")
        self.assertEqual(code, 0, res)
        self.assertAlmostEqual(res["steps"]["snap"]["scale"][0], 5, places=1)
        self.assertTrue(np.array_equal(self.load("out/potion.png"), tight(self.sprite)))

    def test_real_model_render_comes_back_exactly(self):
        """outcome-make-3's input: a Z-Image img2img render with the model's own off-grid shading at about 29.25 px
        per art pixel. make must return the sprite check_make_real.py holds, pixel for pixel."""
        subprocess.run([sys.executable, str(ROOT / "evals" / "fixtures" / "outcome3_fixture.py"), str(self.dir)],
                       check=True, capture_output=True)
        rec = {"id": "potion-clean", "input": "render.png", "palette": "from:ref.png", "crop": {"pad": 0}}
        (self.dir / "r.json").write_text(json.dumps(rec))
        code, res = self.run_pxw("make", "r.json", ".", "--no-aw")
        self.assertEqual(code, 0, res)
        r = subprocess.run([sys.executable, str(ROOT / "evals" / "check_make_real.py"), str(self.dir)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_fractional_scale_is_found(self):
        n = int(round(16 * 5.35))
        big = np.array(Image.fromarray(self.sprite, "RGBA").resize((n, n), Image.NEAREST))
        out, info = pxw.snap_grid(big)
        self.assertAlmostEqual(info["scale"][0], 5.35, delta=0.06)
        self.assertEqual(info["native"], [16, 16])
        self.assertTrue(np.array_equal(out, self.sprite))

    def test_native_pixel_art_is_left_alone(self):
        out, info = pxw.snap_grid(self.sprite)
        self.assertEqual(info["scale"], [1, 1])
        self.assertTrue(np.array_equal(out, self.sprite))

    def test_given_scale_and_offset(self):
        save(upscale(self.sprite, 3, offset=2, pad=1), self.dir / "big.png")
        code, res = self.run_pxw("snap", "big.png", "s.png", "--scale", 3, "--offset", "2,2")
        self.assertEqual(code, 0, res)
        self.assertTrue(np.array_equal(tight(self.load("s.png")), tight(self.sprite)))


class TestPalette(Base):
    def gradient(self):
        a = np.zeros((8, 64, 4), np.uint8)
        a[..., 0] = np.linspace(0, 255, 64)[None].astype(np.uint8)
        a[..., 1] = 40
        a[..., 3] = 255
        return a

    def test_named_palette_only_uses_its_colours(self):
        save(self.gradient(), self.dir / "g.png")
        code, res = self.run_pxw("palette", "g.png", "q.png", "--palette", "pico-8")
        self.assertEqual(code, 0, res)
        pico = {tuple(pxw.parse_rgb(h)) for h in pxw.PALETTES["pico-8"]}
        used = {tuple(c) for c in pxw.opaque_colours(self.load("q.png")).tolist()}
        self.assertTrue(used <= pico, used - pico)

    def test_extract_n_colours_is_deterministic(self):
        save(self.gradient(), self.dir / "g.png")
        self.run_pxw("palette", "g.png", "a.png", "--colours", 4, "--gpl", "a.gpl")
        self.run_pxw("palette", "g.png", "b.png", "--colours", 4)
        self.assertLessEqual(len(pxw.opaque_colours(self.load("a.png"))), 4)
        self.assertTrue(np.array_equal(self.load("a.png"), self.load("b.png")))
        self.assertEqual(len(pxw.load_palette(str(self.dir / "a.gpl"))), 4)

    def test_ordered_dither_mixes_neighbours_and_stays_in_palette(self):
        g = self.gradient()
        pal = np.array([[0, 40, 0], [255, 40, 0]], np.uint8)
        flat = pxw.quantise(g, pal)
        dith = pxw.quantise(g, pal, "bayer4")
        mid = dith[:, 24:40, 0]
        self.assertEqual(len(np.unique(flat[:, 24:40, 0][:, :4])), 1)
        self.assertGreater(len(np.unique(mid)), 1)
        self.assertTrue(set(np.unique(dith[..., 0])) <= {0, 255})

    def test_palette_files(self):
        (self.dir / "p.hex").write_text("ff0000\n00ff00\n#0000ff\n")
        (self.dir / "p.gpl").write_text("GIMP Palette\nName: t\nColumns: 2\n#\n255   0   0\tred\n  0 255   0\tgreen\n")
        self.assertEqual(len(pxw.load_palette(str(self.dir / "p.hex"))), 3)
        self.assertEqual(len(pxw.load_palette(str(self.dir / "p.gpl"))), 2)
        self.assertEqual(len(pxw.load_palette("from:potion.png", str(self.dir))), 5)

    def test_usage_error_without_a_palette(self):
        code, _ = self.run_pxw("palette", "potion.png", "q.png")
        self.assertEqual(code, 2)


class TestClean(Base):
    def test_background_clears_only_what_touches_the_border(self):
        a = np.zeros((12, 12, 4), np.uint8)
        a[...] = SKY + [255]
        a[3:9, 3:9] = INK + [255]
        a[5:7, 5:7] = SKY + [255]  # a window of sky colour inside the outline stays
        b, info = pxw.remove_background(a)
        self.assertEqual(info["colour"], SKY)
        self.assertEqual(b[0, 0, 3], 0)
        self.assertEqual(b[5, 5, 3], 255)
        self.assertEqual(int((b[..., 3] > 0).sum()), 36)

    def test_orphans_take_their_neighbours_colour_and_lone_specks_go(self):
        a = np.zeros((10, 10, 4), np.uint8)
        a[2:7, 2:7] = RED + [255]
        a[4, 4] = PINK + [255]
        a[9, 9] = INK + [255]
        b, n = pxw.remove_orphans(a)
        self.assertEqual(n, 2)
        self.assertEqual(list(b[4, 4]), RED + [255])
        self.assertEqual(b[9, 9, 3], 0)

    def test_outline_auto_and_selective(self):
        a = np.zeros((10, 10, 4), np.uint8)
        a[2:8, 2:8] = RED + [255]
        pal = np.array([RED, PINK, INK, [120, 20, 30], [150, 30, 40]], np.uint8)
        b, n = pxw.outline(a, "auto", pal)
        self.assertEqual(n, 20)
        self.assertEqual(list(b[2, 4, :3]), INK)
        self.assertEqual(list(b[4, 4, :3]), RED)
        s, _ = pxw.outline(a, "selective", pal, "top-left")
        L = lambda c: pxw.oklab(c)[0]
        lit, shade = s[2, 4, :3], s[7, 4, :3]
        self.assertLess(L(lit), L(RED))
        self.assertLess(L(shade), L(lit))

    def test_thin_removes_the_inner_pixel_of_a_doubled_outline(self):
        a = np.zeros((12, 12, 4), np.uint8)
        a[1:11, 1:11] = INK + [255]
        a[3:9, 3:9] = RED + [255]
        b, n = pxw.thin_outline(a)
        self.assertEqual(n, 28)  # the inner ring of a 10 px square
        self.assertEqual(list(b[1, 5, :3]), INK)
        self.assertEqual(list(b[2, 5, :3]), RED)

    def test_clean_command_binarises_alpha(self):
        a = self.sprite.copy()
        a[0, 0] = [10, 10, 10, 90]
        a[15, 15] = [10, 10, 10, 200]
        save(a, self.dir / "soft.png")
        code, res = self.run_pxw("clean", "soft.png", "c.png")
        self.assertEqual(code, 0, res)
        al = self.load("c.png")[..., 3]
        self.assertTrue(np.isin(al, (0, 255)).all())
        self.assertEqual(al[0, 0], 0)
        self.assertEqual(al[15, 15], 255)


class TestCropTile(Base):
    def test_crop_sizes(self):
        code, res = self.run_pxw("crop", "potion.png", "c.png", "--size", "pow2", "--pad", 1)
        self.assertEqual(code, 0, res)
        self.assertEqual(res["canvas"], [32, 32])  # 16 px tall plus a pad each side
        self.assertEqual(self.load("c.png")[-1].sum(), 0)  # bottom anchor keeps the pad row clear
        code, res = self.run_pxw("crop", "potion.png", "c2.png", "--size", "24x20")
        self.assertEqual(res["canvas"], [24, 20])
        self.assertTrue(np.array_equal(tight(self.load("c2.png")), tight(self.sprite)))
        code, res = self.run_pxw("crop", "potion.png", "c3.png", "--size", "8x8")
        self.assertEqual(code, 1)

    def test_tile_wraps_without_new_colours(self):
        rng = np.random.default_rng(3)
        a = np.zeros((16, 16, 4), np.uint8)
        a[..., 3] = 255
        a[..., :3] = [[RED, PINK, INK][v] for v in rng.integers(0, 3, 16)]  # stripes across x
        a[:, :8, :3] = np.array(GLASS)  # a hard seam at the wrap edge
        save(a, self.dir / "t.png")
        code, res = self.run_pxw("tile", "t.png", "w.png")
        self.assertEqual(code, 0, res)
        self.assertEqual(res["new_colours"], 0)
        self.assertLess(res["seam_ratio"], res["seam_ratio_before"])
        self.assertLessEqual(res["seam_ratio"], 1.5)

    def test_fit_counts_tiles_flips_and_colours(self):
        cell = np.zeros((8, 8, 4), np.uint8)
        cell[..., 3] = 255
        cell[:, :4, :3] = RED  # left half red, right half black: its mirror is a new tile without --flip
        a = np.concatenate([cell, cell[:, ::-1]], axis=1)
        save(a, self.dir / "f.png")
        code, res = self.run_pxw("fit", "f.png", "--target", "gb")
        self.assertEqual((code, res["unique_tiles"], res["max_colours_per_cell"]), (0, 2, 2), res)
        code, res = self.run_pxw("fit", "f.png", "--tiles", 1)
        self.assertEqual(code, 1, res)
        code, res = self.run_pxw("fit", "f.png", "--tiles", 1, "--flip")
        self.assertEqual((code, res["unique_tiles"]), (0, 1), res)
        a[0, 0, :3], a[0, 1, :3], a[0, 2, :3] = PINK, INK, GLASS  # five colours in one cell
        save(a, self.dir / "g.png")
        code, res = self.run_pxw("fit", "g.png", "--target", "nes")
        self.assertEqual((code, res["cells_over"], res["areas_over"]), (1, [[0, 0]], [[0, 0]]), res)
        code, res = self.run_pxw("fit", "g.png", "--cell", 5)
        self.assertEqual(code, 1, res)


class TestPadDirs(Base):
    def test_pad_unpad_round_trip(self):
        code, res = self.run_pxw("pad", "potion.png", "p.png")
        self.assertEqual(code, 0, res)
        self.assertEqual(res["scale"], 60)  # (1024 - 64) // 16
        x0, y0, x1, y1 = res["box"]
        can = self.load("p.png")
        self.assertEqual(can.shape[:2], (1024, 1024))
        self.assertEqual(can[0, 0, :3].tolist(), [0, 0, 0])
        # a stand-in edit model: blur, then halve the canvas size
        Image.open(self.dir / "p.png").convert("RGB").filter(ImageFilter.GaussianBlur(2)).resize(
            (512, 512), Image.BILINEAR).save(self.dir / "e.png")
        code, res = self.run_pxw("unpad", "e.png", "u.png", "--box", "p.json")
        self.assertEqual(code, 0, res)
        u = self.load("u.png")
        self.assertEqual(u.shape[:2], (16, 16))
        op = self.sprite[..., 3] > 0
        diff = np.abs(u[..., :3].astype(int) - self.sprite[..., :3].astype(int)).sum(-1)
        self.assertGreater((diff[op] < 30).mean(), 0.85)
        self.assertTrue((u[~op, 3] == 0).all())  # the border went back to transparent
        code, res = self.run_pxw("pad", "potion.png", "q.png", "--canvas", 40)
        self.assertEqual(code, 1)

    def ring(self, bad=None):
        im = Image.new("RGB", (768, 768), (255, 255, 255))
        from PIL import ImageDraw
        d = ImageDraw.Draw(im)
        for i in range(9):
            x, y = (i % 3) * 256, (i // 3) * 256
            if i == 4 and bad != "centre":
                continue
            d.ellipse((x + 90, y + 40, x + 166, y + 216), fill=(40, 120, 60))
            if bad == "two" and i == 0:
                d.ellipse((x + 10, y + 10, x + 40, y + 40), fill=(40, 120, 60))
            if bad == "edge" and i == 8:
                d.rectangle((x + 200, y + 100, x + 256, y + 140), fill=(40, 120, 60))
        im.save(self.dir / f"ring-{bad}.png")
        return f"ring-{bad}.png"

    def test_dirs_gate(self):
        code, res = self.run_pxw("dirs", self.ring(), "f")
        self.assertEqual(code, 0, res)
        self.assertEqual(sorted(Path(p).stem for p in res["frames"]),
                         sorted(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]))
        for bad, cell in (("centre", "centre"), ("two", "NW"), ("edge", "SE")):
            code, res = self.run_pxw("dirs", self.ring(bad), "g" + bad)
            self.assertEqual(code, 1, bad)
            self.assertEqual(res["failed"], [cell])


    def quad(self, same=False):
        im = Image.new("RGB", (512, 512), (230, 20, 20))
        from PIL import ImageDraw
        d = ImageDraw.Draw(im)
        for i in range(4):
            x, y = (i % 2) * 256, (i // 2) * 256
            if i == 2 and not same:  # back view: a different silhouette from the front
                d.polygon([(x + 128, y + 30), (x + 200, y + 220), (x + 56, y + 220)], fill=(40, 120, 60))
            elif i == 0 or same:
                d.ellipse((x + 90, y + 40, x + 166, y + 216), fill=(40, 120, 60))
            else:  # side views: a different silhouette
                d.rectangle((x + 60, y + 100, x + 200, y + 160), fill=(40, 120, 60))
        im.save(self.dir / f"quad-{same}.png")
        return f"quad-{same}.png"

    def test_dirs_2x2(self):
        code, res = self.run_pxw("dirs", self.quad(), "q", "--grid", "2x2")
        self.assertEqual(code, 0, res)
        self.assertEqual(sorted(Path(p).stem for p in res["frames"]), ["E", "N", "S", "W"])
        self.assertIn(["E", "W", 1.0], res["repeated"])  # the side pair
        self.assertNotIn("S", sum((r[:2] for r in res["repeated"]), []))
        code, res = self.run_pxw("dirs", self.quad(True), "q2", "--grid", "2x2", "--names", "a,b,c,d")
        self.assertEqual(code, 0, res)
        self.assertIn("a", sum((r[:2] for r in res["repeated"]), []))
        code, res = self.run_pxw("dirs", self.quad(), "q3", "--grid", "2x2", "--names", "a,b")
        self.assertEqual(code, 1)

    def test_dirs_6x4_sheet(self):
        from PIL import ImageDraw
        im = Image.new("RGBA", (192, 192), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for i in range(24):
            x, y = (i % 6) * 32, (i // 6) * 48
            d.rectangle((x + 10, y + 6, x + 21, y + 40 + (i % 6 == 1)), fill=(40, 120, 60, 255))
        im.save(self.dir / "sheet.png")
        code, res = self.run_pxw("dirs", "sheet.png", "s", "--grid", "6x4")
        self.assertEqual(code, 0, res)
        self.assertEqual(len(res["frames"]), 24)
        self.assertEqual(res["cell"], [32, 48])
        self.assertEqual(res["walk_baselines"]["down"], [40, 41, 40])
        self.assertIn("up_hurt", res["cells"])
        d.rectangle((32 * 5 + 20, 48 * 3 + 10, 32 * 6 - 1, 48 * 3 + 20), fill=(40, 120, 60, 255))
        im.save(self.dir / "sheet2.png")
        code, res = self.run_pxw("dirs", "sheet2.png", "s2", "--grid", "6x4")
        self.assertEqual(code, 1)
        self.assertEqual(res["failed"], ["up_hurt"])


class TestMake(Base):
    def test_gate_fails_over_budget_and_writes_the_report(self):
        rec = {"id": "p", "input": "potion.png", "budget": 3, "crop": {"pad": 1, "size": "pow2"}}
        (self.dir / "r.json").write_text(json.dumps(rec))
        code, res = self.run_pxw("make", "r.json", "out", "--no-aw")
        self.assertEqual(code, 1)
        self.assertFalse(res["gates"]["within_budget"])
        self.assertTrue((self.dir / "out" / "p.make.json").is_file())
        self.assertTrue((self.dir / "out" / "p.gpl").is_file())
        prev = Image.open(self.dir / "out" / "p.x4.png")
        self.assertEqual(prev.size, (128, 128))

    def test_selective_outline_recipe_passes_its_gates(self):
        rec = {"id": "p", "input": "potion.png", "palette": "pico-8",
               "clean": {"orphans": True, "outline": "selective"}, "crop": {"pad": 1, "size": "32x32"}}
        (self.dir / "r.json").write_text(json.dumps(rec))
        code, res = self.run_pxw("make", "r.json", "out", "--no-aw")
        self.assertEqual(code, 0, res)
        self.assertEqual(res["gates"]["colours_outside_palette"], 0)
        self.assertTrue(res["gates"]["size_ok"])

    def test_several_sprites_in_one_recipe(self):
        recs = {"sprites": [{"id": "a", "input": "potion.png"}, {"id": "b", "input": "potion.png", "palette": 4}]}
        (self.dir / "r.json").write_text(json.dumps(recs))
        code, res = self.run_pxw("make", "r.json", "out", "--no-aw")
        self.assertEqual(code, 0, res)
        self.assertEqual([s["id"] for s in res["sprites"]], ["a", "b"])

    def test_artwright_verdict_fails_the_make(self):
        """aw.py pixel nests its verdict under items; a 'not clean' verdict must fail the gate."""
        stub = self.dir / "aw.py"
        stub.write_text('import json\nprint(json.dumps({"items": [{"clean_pixel_art": False, '
                        '"problems": ["blend pixels"]}], "ok": False}))\n')
        (self.dir / "r.json").write_text(json.dumps({"id": "p", "input": "potion.png"}))
        r = subprocess.run([sys.executable, str(PXW), "make", "r.json", "out"], capture_output=True, text=True,
                           cwd=self.dir, env=dict(__import__("os").environ, PIXELWRIGHT_AW=str(stub)))
        res = json.loads(r.stdout)
        self.assertEqual(r.returncode, 1, res)
        self.assertEqual(res["gates"]["aw_pixel"]["problems"], ["blend pixels"])

    def test_artwright_is_told_the_output_is_native(self):
        """make writes one pixel per art pixel; aw.py must judge at scale 1, not search a small sprite for a grid."""
        stub = self.dir / "aw.py"
        stub.write_text('import json, sys\nok = sys.argv[sys.argv.index("--scale") + 1] == "1" '
                        'if "--scale" in sys.argv else False\n'
                        'print(json.dumps({"items": [{"clean_pixel_art": ok, "problems": [] if ok else '
                        '["false grid"]}], "ok": ok}))\n')
        (self.dir / "r.json").write_text(json.dumps({"id": "p", "input": "potion.png"}))
        r = subprocess.run([sys.executable, str(PXW), "make", "r.json", "out"], capture_output=True, text=True,
                           cwd=self.dir, env=dict(__import__("os").environ, PIXELWRIGHT_AW=str(stub)))
        res = json.loads(r.stdout)
        self.assertEqual(r.returncode, 0, res)
        self.assertIs(res["gates"]["aw_pixel"]["clean_pixel_art"], True)

    def test_median_cut_spends_no_colours_on_twins(self):
        """A big near-black area with noise must not take several of the N colours."""
        rng = np.random.default_rng(1)
        black = np.clip(rng.integers(0, 4, (900, 3)), 0, 255)
        px = np.concatenate([black, np.tile([[190, 40, 50]], (60, 1)), np.tile([[160, 100, 40]], (20, 1)),
                             np.tile([[230, 230, 230]], (20, 1))]).astype(np.uint8)
        pal = pxw.median_cut(px, 6)
        lab = pxw.oklab(pal)
        d = np.linalg.norm(lab[:, None] - lab[None], axis=2) + np.eye(len(pal))
        self.assertGreaterEqual(d.min(), 0.03)
        self.assertTrue(any(np.abs(pal.astype(int) - [160, 100, 40]).max(1) < 8))  # the small brown survives

    def test_old_sw_name_still_runs(self):
        code, res = self.run_pxw("doctor", script=SHIM)
        self.assertEqual(res["version"], pxw.VERSION)


class TestRound2(Base):
    """Fixes and steps from the 2026-10-25 book pass (grid significance, enclosed holes, linear dither, contrast cap,
    swap, pixel-perfect corners, fog)."""

    def test_smooth_jpeg_has_no_grid(self):
        """A smooth render saved as JPEG has one or two strong edges; a period through them is chance, not a grid
        (it used to snap at scale 17 or 57 into mush)."""
        import io
        src = np.random.default_rng(0).integers(0, 256, (96, 96, 3), dtype=np.uint8)
        im = Image.fromarray(src).resize((768, 768), Image.BICUBIC).filter(ImageFilter.GaussianBlur(6))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=55)
        buf.seek(0)
        out, info = pxw.snap_grid(np.array(Image.open(buf).convert("RGBA")))
        self.assertEqual(info["scale"], [1, 1])
        self.assertEqual(out.shape[:2], (768, 768))

    def test_a_dozen_random_edges_are_no_grid(self):
        """Twelve colour bands at random places: some period always lines a few of them up (coherence above the old
        0.5 line), but not above 2.8/sqrt(12)."""
        rng = np.random.default_rng(3)
        a = np.zeros((40, 300, 4), np.uint8)
        a[..., 3] = 255
        for i, x in enumerate(sorted(rng.choice(np.arange(5, 295), 12, replace=False))):
            a[:, x:, :3] = (i * 40 % 256, 255 - i * 20, 90)
        self.assertEqual(pxw.snap_grid(a)[1]["scale"], [1, 1])

    def test_enclosed_background_cleared_only_when_asked(self):
        r = np.zeros((32, 32, 4), np.uint8)
        r[...] = [255, 0, 255, 255]
        r[8:24, 8:24] = [40, 60, 200, 255]
        r[12:20, 12:20] = [255, 0, 255, 255]  # the hole of a ring
        r[9, 9] = [255, 0, 255, 255]  # a one-pixel highlight of the background colour
        b, info = pxw.remove_background(r)
        self.assertEqual(int(b[15, 15, 3]), 255)
        b, info = pxw.remove_background(r, holes=4)
        self.assertEqual(int(b[15, 15, 3]), 0)
        self.assertEqual(int(b[9, 9, 3]), 255)
        self.assertEqual(info["enclosed_cleared"], 64)

    def ramp(self):
        g = np.zeros((16, 64, 4), np.uint8)
        g[..., 3] = 255
        for i in range(16):
            g[:, i * 4:(i + 1) * 4, :3] = i * 17
        return g

    def test_linear_dither_keeps_the_light(self):
        """Each grey step dithered on black and white must average to its own linear light (within a Bayer step)."""
        g, pal = self.ramp(), np.array([[0, 0, 0], [255, 255, 255]], np.uint8)
        for space, ok in (("linear", True), ("srgb", False)):
            q = pxw.quantise(g, pal, "bayer4", space)
            err = max(abs((q[:, i * 4:(i + 1) * 4, 0] == 255).mean() - pxw._linear(np.array([i * 17]))[0])
                      for i in range(16))
            self.assertEqual(err < 0.04, ok, (space, err))

    def test_dither_cap_keeps_far_pairs_apart(self):
        g = self.ramp()
        bw = np.array([[0, 0, 0], [255, 255, 255]], np.uint8)
        self.assertTrue(np.array_equal(pxw.quantise(g, bw, "bayer4", max_step=0.12), pxw.quantise(g, bw)))
        greys = np.array([[110, 110, 110], [128, 128, 128]], np.uint8)  # about 0.05 apart in OKLab lightness
        flat = np.full((8, 8, 4), 119, np.uint8)
        flat[..., 3] = 255
        q = pxw.quantise(flat, greys, "bayer4", "linear", max_step=0.12)
        self.assertEqual(len(pxw.opaque_colours(q)), 2)

    def test_swap_round_trip_and_unmapped_colour(self):
        save(draw_sprite(), self.dir / "p.png")
        cols = [pxw._hex(c) for c in pxw.opaque_colours(draw_sprite())]
        fwd = {c: "%06x" % (int(c, 16) ^ 0x0f0f0f) for c in cols}
        (self.dir / "f.json").write_text(json.dumps(fwd))
        (self.dir / "b.json").write_text(json.dumps({v: k for k, v in fwd.items()}))
        code, res = self.run_pxw("swap", "p.png", "q.png", "--map", "f.json")
        self.assertEqual(code, 0, res)
        self.assertFalse(np.array_equal(self.load("q.png"), draw_sprite()))
        self.run_pxw("swap", "q.png", "r.png", "--map", "b.json")
        self.assertTrue(np.array_equal(self.load("r.png"), draw_sprite()))
        (self.dir / "part.json").write_text(json.dumps(dict(list(fwd.items())[:2])))
        code, res = self.run_pxw("swap", "p.png", "s.png", "--map", "part.json")
        self.assertEqual(code, 1)
        self.assertEqual(len(res["unmapped"]), len(cols) - 2)

    def test_swap_by_palette_index_keeps_file_order(self):
        a = np.zeros((2, 2, 4), np.uint8)
        a[0, 0], a[1, 1] = [250, 0, 0, 255], [0, 0, 250, 255]
        save(a, self.dir / "a.png")
        (self.dir / "from.hex").write_text("fa0000\n0000fa\n")
        (self.dir / "to.hex").write_text("00fa00\n101010\n")
        code, _ = self.run_pxw("swap", "a.png", "b.png", "--from", "from.hex", "--to", "to.hex")
        b = self.load("b.png")
        self.assertEqual(code, 0)
        self.assertEqual(b[0, 0, :3].tolist(), [0, 250, 0])
        self.assertEqual(b[1, 1, :3].tolist(), [16, 16, 16])

    def test_corners_fix_stair_steps_but_not_real_corners(self):
        a = np.zeros((10, 14, 4), np.uint8)
        for i in range(6):  # a diagonal drawn with doubled steps: two pixels a row, each row one to the right
            a[i, i:i + 2] = INK + [255]
        line = (a[..., 3] > 0).sum()
        b, n = pxw.fix_corners(a)
        self.assertGreater(n, 0)
        on = b[..., 3] > 0
        self.assertTrue(on[0, 0] and on[5, 6])  # both ends kept
        ys, xs = np.nonzero(on)
        for y, x in zip(ys, xs):  # still one 8-connected line with no L-corner left
            self.assertFalse(on[y, x + 1] and y + 1 < 10 and on[y + 1, x + 1] and not on[y + 1, x]
                             if x + 1 < 14 else False)
        self.assertEqual(int(on.sum()), line - n)
        sq = np.zeros((8, 8, 4), np.uint8)
        sq[1:7, 1:7] = INK + [255]
        sq[2:6, 2:6] = RED + [255]
        self.assertEqual(pxw.fix_corners(sq)[1], 0)
        clean = np.zeros((6, 6, 4), np.uint8)
        for i in range(6):
            clean[i, i] = INK + [255]
        self.assertEqual(pxw.fix_corners(clean)[1], 0)

    def test_fog_lowers_contrast_and_stays_in_palette(self):
        save(draw_sprite(), self.dir / "p.png")
        rec = {"id": "far", "input": "p.png", "snap": False, "palette": "pico-8",
               "fog": {"colour": "194,195,199", "amount": 0.8}}
        (self.dir / "r.json").write_text(json.dumps(rec))
        code, res = self.run_pxw("make", "r.json", "out", "--no-aw")
        self.assertEqual(code, 0, res)
        self.assertEqual(res["gates"]["colours_outside_palette"], 0)
        lum = lambda a: (a[a[..., 3] > 0][:, :3] @ [0.2126, 0.7152, 0.0722]).std()
        self.assertLess(lum(self.load("out/far.png")), 0.5 * lum(draw_sprite()))

    def test_heavy_fog_can_collapse_a_sparse_palette_without_failing(self):
        a = np.zeros((8, 8, 4), np.uint8)
        a[1:7, 1:4] = [255, 0, 77, 255]
        a[1:7, 4:7] = [0, 228, 54, 255]
        save(a, self.dir / "p.png")
        rec = {"id": "far", "input": "p.png", "snap": False, "background": "none", "clean": False,
               "palette": "pico-8", "fog": {"colour": "255,241,232", "amount": 0.99}}
        (self.dir / "r.json").write_text(json.dumps(rec))
        code, res = self.run_pxw("make", "r.json", "out", "--no-aw")
        self.assertEqual(code, 0, res)
        self.assertEqual(res["gates"]["colours"], 1)
        self.assertTrue(res["gates"]["within_budget"])
        self.assertEqual(res["gates"]["colours_outside_palette"], 0)
        self.assertTrue(np.array_equal(self.load("out/far.png")[..., 3], a[..., 3]))


class TestFont(Base):
    """pxw.py font: a 3x1 atlas of 5x5 glyphs drawn at 4x, the third cell empty (a skipped letter)."""

    def atlas(self):
        A = ["01110", "10001", "11111", "10001", "10001"]
        I = ["111", "010", "010", "010", "111"]
        im = np.zeros((20, 60, 3), np.uint8)
        for col, g in ((0, A), (1, I)):
            for y, row in enumerate(g):
                for x, b in enumerate(row):
                    if b == "1":
                        im[y * 4:(y + 1) * 4, col * 20 + x * 4:col * 20 + (x + 1) * 4] = 255
        Image.fromarray(im).save(self.dir / "atlas.png")

    def test_atlas_to_ttf(self):
        try:
            from fontTools.ttLib import TTFont
        except ImportError:
            self.skipTest("fontTools not installed")
        self.atlas()
        code, res = self.run_pxw("font", "atlas.png", "f.ttf", "--grid", "3x1", "--chars", "AIB", "--px", "5x5")
        self.assertEqual(code, 1)
        self.assertEqual(res["missing"], ["B"])
        self.assertEqual(res["glyphs"], 2)
        f = TTFont(self.dir / "f.ttf")
        cmap = f.getBestCmap()
        self.assertIn(ord("A"), cmap)
        glyf = f["glyf"]
        a = glyf[cmap[ord("A")]]
        self.assertEqual(a.numberOfContours, 8)  # one contour per row run: 1+2+1+2+2
        self.assertEqual(f["hmtx"][cmap[ord("I")]][0], 4 * 200)  # trimmed to 3 px ink + 1 gap
        self.assertEqual(glyf[cmap[ord("B")]].numberOfContours, 0)
        code, res = self.run_pxw("font", "atlas.png", "g.ttf", "--grid", "3x1", "--chars", "AI ", "--px", "5x5")
        self.assertEqual(code, 0, res)

    def test_too_many_chars(self):
        self.atlas()
        code, res = self.run_pxw("font", "atlas.png", "f.ttf", "--grid", "3x1", "--chars", "ABCD")
        self.assertEqual(code, 1)


class TestNormals(Base):
    def disc(self):
        y, x = np.mgrid[:20, :20]
        a = np.zeros((20, 20, 4), np.uint8)
        a[(x - 9.5) ** 2 + (y - 9.5) ** 2 < 64] = [200, 60, 60, 255]
        return a

    def test_disc_reads_as_a_dome_and_keeps_alpha(self):
        save(self.disc(), self.dir / "d.png")
        code, res = self.run_pxw("normals", "d.png", "out", "--relit")
        self.assertEqual(code, 0, res)
        self.assertTrue(0.5 < res["mean_normal_z"] < 0.97, res)
        n = self.load("out/d_n.png")
        self.assertTrue(np.array_equal(n[..., 3], self.disc()[..., 3]))
        self.assertEqual(n[0, 0, :3].tolist(), [128, 128, 255])
        self.assertLess(n[10, 3, 0], 100)   # left rim faces left
        self.assertGreater(n[10, 16, 0], 156)
        self.assertGreater(n[3, 10, 1], 156)  # top rim faces up (OpenGL green)
        self.assertTrue((self.dir / "out/d_relit.png").exists())
        code, res = self.run_pxw("normals", "d.png", "dx", "--green-down")
        self.assertLess(self.load("dx/d_n.png")[3, 10, 1], 100)

    def test_sheet_cells_are_independent(self):
        d = self.disc()
        save(np.concatenate([d, d], axis=1), self.dir / "s.png")
        code, res = self.run_pxw("normals", "s.png", "out", "--frame-size", "20x20")
        self.assertEqual(code, 0, res)
        self.assertEqual(res["cells"], 2)
        n = self.load("out/s_n.png")
        self.assertTrue(np.array_equal(n[:, :20], n[:, 20:]))
        code, res = self.run_pxw("normals", "s.png", "out", "--frame-size", "15x20")
        self.assertEqual(code, 1)


class OverlapTest(unittest.TestCase):
    """overlap: repaint silhouette vs the guide render; raw and bbox-fitted IoU, warn 0.85, fail 0.70."""

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.dir = Path(self.td.name)
        g = np.zeros((80, 80, 4), np.uint8)
        g[20:60, 25:55] = [150, 150, 150, 255]  # clay crate with alpha
        save(g, self.dir / "guide.png")

    def tearDown(self):
        self.td.cleanup()

    def paint(self, name, box):
        a = np.zeros((80, 80, 4), np.uint8)
        a[...] = [250, 250, 250, 255]  # flat background, no alpha: keyed from the border
        y0, y1, x0, x1 = box
        a[y0:y1, x0:x1] = [140, 80, 30, 255]
        a[y0 + 8:y0 + 12, x0 + 4:x1 - 4] = [250, 250, 250, 255]  # a light plank stripe: a hole the fill closes
        save(a, self.dir / name)

    def run_overlap(self, *names):
        r = subprocess.run([sys.executable, str(PXW), "overlap", str(self.dir / "guide.png")] +
                           [str(self.dir / n) for n in names], capture_output=True, text=True)
        return r.returncode, json.loads(r.stdout)

    def test_pass_warn_fail(self):
        self.paint("same.png", (20, 60, 25, 55))
        self.paint("thin.png", (20, 60, 25, 47))      # IoU 0.73: warn band
        self.paint("moved.png", (2, 22, 2, 17))       # half size, off-centre: fails raw, fits back
        code, res = self.run_overlap("same.png", "thin.png", "moved.png")
        self.assertEqual(code, 1)
        v = {r["file"]: r for r in res["results"]}
        self.assertEqual(v["same.png"]["verdict"], "pass")
        self.assertGreater(v["same.png"]["iou"], 0.97)
        self.assertEqual(v["thin.png"]["verdict"], "warn")
        self.assertEqual(v["moved.png"]["verdict"], "fail")
        self.assertGreater(v["moved.png"]["iou_fit"], 0.9)
        self.assertIn("fitted", v["moved.png"]["note"])
        self.assertEqual(res["failed"], ["moved.png"])
        code, res = self.run_overlap("same.png")
        self.assertEqual(code, 0)
        self.assertTrue(res["ok"])


class ShadowTest(unittest.TestCase):
    """shadow: feet anchor on the lowest opaque row's centre, shadow centred under it, engine pivots."""

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.dir = Path(self.td.name)
        a = np.zeros((40, 30, 4), np.uint8)
        a[5:30, 8:22] = [120, 70, 30, 255]   # a post
        a[30:34, 10:16] = [90, 50, 20, 255]  # an off-centre foot: the lowest row is x 10..15
        save(a, self.dir / "prop.png")

    def tearDown(self):
        self.td.cleanup()

    def run_shadow(self, *args, src="prop.png"):
        r = subprocess.run([sys.executable, str(PXW), "shadow", str(self.dir / src), str(self.dir / "out")] +
                           list(args), capture_output=True, text=True)
        return r.returncode, json.loads(r.stdout)

    def test_anchor_and_soft_shadow(self):
        code, res = self.run_shadow()
        self.assertEqual(code, 0, res)
        self.assertEqual(res["pixel"], [13.0, 34.0])
        j = json.loads((self.dir / "out" / "prop_anchor.json").read_text())
        self.assertEqual(j["engines"]["unity"]["pivot"], [round(13 / 30, 4), round(1 - 34 / 40, 4)])
        self.assertEqual(j["engines"]["phaser"]["setOrigin"], [round(13 / 30, 4), 0.85])
        self.assertEqual(j["engines"]["godot"]["offset"], [2.0, -14.0])
        al = np.array(Image.open(self.dir / "out" / "prop_shadow.png"))[..., 3].astype(float)
        self.assertGreater(len(np.unique(al)), 3)  # soft
        ys, xs = np.mgrid[0:al.shape[0], 0:al.shape[1]]
        cx = (al * xs).sum() / al.sum() + 0.5 + j["shadow"]["offset"][0]
        cy = (al * ys).sum() / al.sum() + 0.5 + j["shadow"]["offset"][1]
        self.assertAlmostEqual(cx, 13.0, delta=0.5)
        self.assertAlmostEqual(cy, 34.0, delta=0.5)

    def test_pixel_cast_and_guide(self):
        code, res = self.run_shadow("--style", "pixel", "--shape", "cast", "--opacity", "0.5")
        self.assertEqual(code, 0, res)
        al = np.array(Image.open(self.dir / "out" / "prop_shadow.png"))[..., 3]
        self.assertEqual(set(np.unique(al)) - {0}, {128})
        flat = np.zeros((40, 30, 4), np.uint8)
        flat[...] = [250, 250, 250, 255]
        flat[10:36, 4:12] = [20, 20, 20, 255]
        save(flat, self.dir / "guide.png")
        code, res = self.run_shadow("--guide", str(self.dir / "guide.png"))
        self.assertEqual(res["pixel"], [8.0, 36.0])

    def test_empty_fails(self):
        save(np.zeros((8, 8, 4), np.uint8), self.dir / "empty.png")
        code, res = self.run_shadow(src="empty.png")
        self.assertEqual(code, 1)
        self.assertFalse(res["ok"])


class TestPa20(Base):
    """Technique harvest pa20: JASC palettes, RotSprite, FS dither, ramps, palette sort, tilesets, sheet tags,
    thick outlines, onion skin."""

    def test_jasc_pal_header_is_skipped(self):
        (self.dir / "t.pal").write_text("JASC-PAL\n0100\n3\n255 0 0\n0 255 0\n0 0 255\n", encoding="utf-8")
        pal = pxw.load_palette(str(self.dir / "t.pal"), ordered=True)
        self.assertEqual(pal.tolist(), [[255, 0, 0], [0, 255, 0], [0, 0, 255]])

    def diag(self):
        a = np.zeros((24, 24, 4), np.uint8)
        yy, xx = np.mgrid[:24, :24]
        a[(abs(xx - yy) <= 2) & (xx > 3) & (xx < 20)] = [200, 200, 220, 255]
        a[(abs(xx - yy) == 3) & (xx > 2) & (xx < 21)] = INK + [255]
        return a

    @staticmethod
    def orphans(a):
        k = pxw._key(a)
        p = np.pad(k, 1, constant_values=-1)
        same = sum((p[1 + dy:p.shape[0] - 1 + dy, 1 + dx:p.shape[1] - 1 + dx] == k) for dy, dx in pxw.N4)
        return int(((same == 0) & (a[..., 3] > 0)).sum())

    def test_scale2x_keeps_colours_and_doubles(self):
        a = self.diag()
        b = pxw.scale2x(a)
        self.assertEqual(b.shape, (48, 48, 4))
        self.assertEqual(len(pxw.opaque_colours(b)), len(pxw.opaque_colours(a)))
        self.assertTrue((pxw.scale2x(np.full((3, 3, 4), 7, np.uint8)) == 7).all())

    def test_rotsprite_leaves_fewer_orphans_than_nearest(self):
        a = self.diag()
        save(a, self.dir / "d.png")
        code, res = self.run_pxw("rotate", "d.png", "r.png", "--deg", "30")
        self.assertEqual(code, 0, res)
        self.assertEqual(res["new_colours"], 0)
        near = pxw.rotate_sprite(a, 30, method="nearest")
        self.assertLess(self.orphans(self.load("r.png")), self.orphans(near))
        self.assertTrue((pxw.rotate_sprite(a, 0) == a).all())

    def test_fs_dither_stays_in_palette_and_strength_zero_is_plain(self):
        g = np.zeros((8, 32, 4), np.uint8)
        g[..., :3] = np.linspace(0, 255, 32)[None, :, None].astype(np.uint8)
        g[..., 3] = 255
        g[0, 0, 3] = 0
        pal = np.array([[0, 0, 0], [128, 128, 128], [255, 255, 255]], np.uint8)
        fs = pxw.quantise(g, pal, "fs")
        self.assertTrue(set(map(tuple, pxw.opaque_colours(fs).tolist())) <= set(map(tuple, pal.tolist())))
        self.assertEqual(fs[0, 0, 3], 0)
        self.assertFalse((fs == pxw.quantise(g, pal)).all())
        self.assertTrue((pxw.quantise(g, pal, "fs", strength=0) == pxw.quantise(g, pal)).all())
        # mean tone tracks the gradient better than plain nearest
        err = lambda q: abs(q[1:, :, 0].astype(float).mean(0) - g[1:, :, 0].mean(0)).mean()
        self.assertLess(err(fs), err(pxw.quantise(g, pal)))

    def test_atkinson_dither_is_quieter_than_fs(self):
        g = np.zeros((16, 64, 4), np.uint8)
        g[..., :3] = np.linspace(0, 255, 64)[None, :, None].astype(np.uint8)
        g[..., 3] = 255
        pal = np.array([[0, 0, 0], [64, 64, 64], [128, 128, 128], [192, 192, 192], [255, 255, 255]], np.uint8)
        at, fs = pxw.quantise(g, pal, "atkinson"), pxw.quantise(g, pal, "fs")
        self.assertTrue(set(map(tuple, pxw.opaque_colours(at).tolist())) <= set(map(tuple, pal.tolist())))
        self.assertFalse((at == fs).all())
        lone = lambda q: sum(int(all((q[y, x, 0] != q[y + dy, x + dx, 0]) for dy, dx in pxw.N4))
                             for y in range(1, 15) for x in range(1, 63))
        self.assertLess(lone(at), lone(fs))
        save(g, self.dir / "g.png")
        code, res = self.run_pxw("palette", "g.png", "a.png", "--palette", "pico-8", "--dither", "atkinson")
        self.assertEqual(code, 0, res)

    def test_swap_ramp_and_step(self):
        (self.dir / "ramp.hex").write_text("101010\n505050\n909090\nd0d0d0\nffffff\n", encoding="utf-8")
        code, res = self.run_pxw("swap", "potion.png", "g.png", "--ramp", "ramp.hex")
        self.assertEqual(code, 0, res)
        g = self.load("g.png")
        self.assertEqual(tuple(g[g[..., 3] > 0][:, :3][np.argmin(pxw.oklab(g[g[..., 3] > 0][:, :3])[:, 0])]),
                         (16, 16, 16))
        self.assertTrue((g[..., 3] == self.sprite[..., 3]).all())
        mask = np.zeros_like(self.sprite)
        mask[8:16] = 255
        save(mask, self.dir / "m.png")
        pal = np.array([INK, [100, 20, 30], RED, PINK, GLASS, CORK], np.uint8)
        (self.dir / "p.hex").write_text("\n".join(pxw._hex(c) for c in pal), encoding="utf-8")
        code, res = self.run_pxw("swap", "potion.png", "s.png", "--step", "-1", "--mask", "m.png", "--palette", "p.hex")
        s = self.load("s.png")
        red = (self.sprite[..., :3] == RED).all(-1)
        self.assertTrue((s[8:][red[8:]][:, :3] == [100, 20, 30]).all())
        self.assertTrue((s[:8] == self.sprite[:8]).all())
        self.assertEqual(pxw.ramp_step(pal, np.array(RED, np.uint8), 1).tolist(), PINK)

    def test_palette_sort(self):
        pal = np.array([[255, 255, 255], [255, 0, 0], [0, 0, 0], [0, 0, 255]], np.uint8)
        self.assertEqual(pxw.sort_palette(pal, "luma")[0].tolist(), [0, 0, 0])
        hue = pxw.sort_palette(pal, "hue").tolist()
        self.assertEqual(hue[:2], [[0, 0, 0], [255, 255, 255]])  # greys first
        self.assertEqual(pxw.sort_palette(pal, "sat")[-1].tolist() in ([255, 0, 0], [0, 0, 255]), True)
        code, res = self.run_pxw("palette", "potion.png", "q.png", "--palette", "pico-8", "--gpl", "q.gpl")
        labs = pxw.oklab(np.array([pxw.parse_rgb(h) for h in res["palette"]]))[:, 0]
        self.assertTrue((np.diff(labs) >= 0).all())

    def test_tileset_dedupes_with_flips(self):
        rng = np.random.default_rng(3)
        base = [rng.integers(0, 255, (8, 8, 4)).astype(np.uint8) for _ in range(4)]
        for b in base:
            b[..., 3] = 255
        img = np.zeros((32, 32, 4), np.uint8)
        for i in range(16):
            t = base[i % 4]
            t = t[:, ::-1] if i % 3 == 1 else t[::-1] if i % 3 == 2 else t
            img[(i // 4) * 8:(i // 4 + 1) * 8, (i % 4) * 8:(i % 4 + 1) * 8] = t
        save(img, self.dir / "map.png")
        code, res = self.run_pxw("tileset", "map.png", "ts", "--cell", "8", "--flip")
        self.assertEqual(code, 0, res)
        self.assertEqual(res["tiles"], 4)
        m = json.loads((self.dir / "ts" / "tilemap.json").read_text())
        tiles = self.load("ts/tiles.png")
        for i, (t, fx, fy) in enumerate(m["map"]):  # rebuild the map from tiles + flags
            tile = tiles[(t // m["columns"]) * 8:(t // m["columns"] + 1) * 8, (t % m["columns"]) * 8:(t % m["columns"] + 1) * 8]
            tile = tile[:, ::-1] if fx else tile
            tile = tile[::-1] if fy else tile
            self.assertTrue((tile == img[(i // 4) * 8:(i // 4 + 1) * 8, (i % 4) * 8:(i % 4 + 1) * 8]).all())
        code, res = self.run_pxw("tileset", "map.png", "ts2", "--cell", "8")
        self.assertGreater(res["tiles"], 4)

    def test_tags_extrude_and_sequence(self):
        self.assertEqual(pxw.tag_sequence([pxw.parse_tag("idle:0-3:pingpong", 4)], 4), [0, 1, 2, 3, 2, 1])
        self.assertEqual(pxw.tag_sequence([pxw.parse_tag("a:1-2:reverse:2", 4)], 4), [2, 1, 2, 1])
        self.assertEqual(pxw.tag_sequence([pxw.parse_tag("b:0-2:pingpong_reverse", 3)], 3), [2, 1, 0, 1])
        self.assertEqual(pxw.tag_sequence([], 3), [0, 1, 2])
        f = [np.full((4, 4, 4), v, np.uint8) for v in (10, 200)]
        sheet, rects = pxw.extrude_sheet(f, 2)
        self.assertEqual(sheet.shape, (8, 16, 4))
        self.assertEqual(rects[1], dict(x=10, y=2, w=4, h=4))
        self.assertTrue((sheet[:, 8:] == 200).all() and (sheet[:, :8] == 10).all())
        frames = []
        for i in range(4):
            a = np.zeros((16, 16, 4), np.uint8)
            a[..., :3] = [255, 0, 255]
            a[..., 3] = 255
            a[4:12, 4 + i % 2:12 + i % 2] = RED + [255]
            save(a, self.dir / f"f{i}.png")
            frames.append(f"f{i}.png")
        code, res = self.run_pxw("anim", *frames, "an", "--scale", "1", "--extrude", "1", "--tag", "loop:0-3:pingpong:2",
                                 "--name", "x")
        self.assertEqual(code, 0, res)
        meta = json.loads((self.dir / "an" / "x_sheet.json").read_text())
        self.assertEqual(meta["meta"]["frameTags"][0], {"name": "loop", "from": 0, "to": 3, "direction": "pingpong",
                                                        "repeat": "2"})
        self.assertEqual(meta["frames"][1]["x"], 19)
        self.assertEqual(self.load("an/x_sheet.png").shape[:2], (18, 72))

    def test_thick_outline_shapes(self):
        a = np.zeros((16, 20, 4), np.uint8)
        a[4:12, 4:16] = RED + [255]
        n = {s: int(pxw.outline_band(a, 2, s).sum()) for s in ("square", "circle", "diamond")}
        self.assertEqual(n["square"], 96)
        self.assertLess(n["diamond"], n["square"])
        self.assertEqual(int(pxw.outline_band(a, 2, "square", inside=True).sum()), 64)
        save(a, self.dir / "b.png")
        code, res = self.run_pxw("clean", "b.png", "o.png", "--outline", "0,0,0", "--outline-width", "2")
        o = self.load("o.png")
        self.assertEqual(res["outlined"], n["diamond"])
        self.assertTrue((o[4:12, 4:16, :3] == RED).all())  # outside band leaves the sprite alone
        self.assertEqual(tuple(o[2, 8]), (0, 0, 0, 255))
        code, res = self.run_pxw("clean", "potion.png", "p.png", "--outline", "auto")
        self.assertEqual(code, 0)  # default 1 px path unchanged

    def test_review_page_has_onion_and_tag_player(self):
        (self.dir / "review-extra.json").write_text(json.dumps([dict(key="k", title="t", sheet_json="an/x_sheet.json",
                                                                     images=[])]), encoding="utf-8")
        r = subprocess.run([sys.executable, str(PXW), "review", str(self.dir), "--print-page"], capture_output=True,
                           text=True)
        self.assertIn("class=player", r.stdout)
        self.assertIn("onion", r.stdout)
        self.assertIn("globalAlpha = 0.3", r.stdout)
        self.assertIn("pingpong", r.stdout)
        self.assertIn("an/x_sheet.json", r.stdout)


def _drifting_upscale(kind, n=32, seed=7):
    """A 32x32 sprite on 16 colours, upscaled with cells of varying width: random 7-9 px (jitter) or 8 +- 0.9
    on a slow sine (drift). A uniform grid cannot fit either."""
    rng = np.random.default_rng(seed)
    pal = rng.integers(0, 256, (16, 3)).astype(np.uint8)
    f = np.kron(rng.random((n // 4, n // 4)), np.ones((4, 4))) + rng.random((n, n)) * 0.35
    gt = np.dstack([pal[(f * 37).astype(int) % 16], np.full((n, n), 255, np.uint8)])
    if kind == "jitter":
        wx, wy = rng.integers(7, 10, n), rng.integers(7, 10, n)
    else:
        wx = wy = np.diff(np.round(np.cumsum(np.r_[0, 8 + 0.9 * np.sin(np.arange(n) / 5)]))).astype(int)
    cx, cy = np.r_[0, np.cumsum(wx)], np.r_[0, np.cumsum(wy)]
    xi = np.searchsorted(cx, np.arange(cx[-1]), side="right") - 1
    yi = np.searchsorted(cy, np.arange(cy[-1]), side="right") - 1
    return gt, gt[yi][:, xi]


class TestElastic(Base):
    def check(self, kind):
        gt, big = _drifting_upscale(kind, seed=4)
        out, info = pxw.snap_grid(big)
        self.assertEqual(info["grid"], "elastic")  # auto: the uniform fit is weak
        self.assertEqual(info["native"], [32, 32])
        match = (np.abs(out[..., :3].astype(int) - gt[..., :3]).max(-1) <= 24).mean()
        self.assertGreaterEqual(match, 0.98)
        off, oi = pxw.snap_grid(big, elastic=False)
        self.assertEqual(oi["grid"], "uniform")
        self.assertTrue(oi["native"] != [32, 32] or
                        (np.abs(off[..., :3].astype(int) - gt[..., :3]).max(-1) <= 24).mean() < match)

    def test_jitter(self):
        self.check("jitter")

    def test_drift(self):
        self.check("drift")

    def test_uniform_grid_stays_uniform_and_cli_flag(self):
        save(upscale(self.sprite, 4), self.dir / "big.png")
        code, res = self.run_pxw("snap", "big.png", "s.png")
        self.assertEqual((code, res["grid"]), (0, "uniform"))
        code, res = self.run_pxw("snap", "big.png", "e.png", "--elastic", "on")
        self.assertEqual((code, res["grid"], res["native"]), (0, "elastic", [16, 16]))
        self.assertTrue(np.array_equal(self.load("e.png"), self.load("s.png")))


class TestStack(Base):
    def test_stack_turns_slices_without_new_colours(self):
        sl = np.zeros((4 * 8, 8, 4), np.uint8)
        cols = [[200, 40, 40], [40, 200, 40], [40, 40, 200], [230, 230, 60]]
        for z in range(4):
            sl[z * 8 + 2:z * 8 + 6, 1:7] = cols[z] + [255]
        save(sl, self.dir / "slices.png")
        code, res = self.run_pxw("stack", "slices.png", "sheet.png", "--angles", 8, "--gif", "t.gif")
        self.assertEqual(code, 0, res)
        self.assertEqual((res["slices"], res["new_colours"]), (4, 0))
        fw, fh = res["frame"]
        self.assertEqual((fw, fh), (12, 15))  # ceil(hypot(8, 8)) wide, + 3 layers of 1 px up
        sheet = self.load("sheet.png")
        self.assertEqual(sheet.shape[:2], (fh, fw * 8))
        f0, f2 = sheet[:, :fw], sheet[:, 2 * fw:3 * fw]
        # the top slice is drawn last and highest; a quarter turn makes the long bar stand upright
        top = np.argwhere((f0[..., :3] == cols[3]).all(-1))
        self.assertEqual(top[:, 0].min(), 2 + 2)
        bar = np.argwhere((f2[..., :3] == cols[3]).all(-1))
        self.assertGreater(np.ptp(bar[:, 0]), np.ptp(bar[:, 1]))
        self.assertTrue((self.dir / "t.gif").exists())


class TestRamp(Base):
    def test_hue_ramp_leans_and_is_not_chalky(self):
        for base in ([190, 38, 51], [74, 154, 58], [42, 91, 215], [224, 192, 64]):
            ramp = pxw.hue_ramp(base, 5)
            lab = pxw.oklab(ramp.astype(float))
            self.assertTrue((np.diff(lab[:, 0]) > 0).all(), base)  # dark to light
            self.assertFalse(pxw.ramp_report(ramp)["ramp_chalky"], base)
        ramp = pxw.hue_ramp([74, 154, 58], 5)  # green: lights lean toward yellow, darks toward blue
        self.assertGreater(ramp[-1][0], ramp[-1][2])
        self.assertGreater(ramp[0][2], ramp[0][0])

    def test_check_flags_a_chalky_ramp_and_passes_a_good_one(self):
        (self.dir / "chalky.hex").write_text("3a1020\n8a2030\nc84050\nf0d8dc\n", encoding="utf-8")
        code, res = self.run_pxw("ramp", "--check", "chalky.hex")
        self.assertEqual(code, 1, res)
        self.assertTrue(res["ramp_chalky"])
        code, res = self.run_pxw("ramp", "--base", "4a9a3a", "--steps", 4, "--gpl", "g.gpl")
        self.assertEqual(code, 0, res)
        (self.dir / "good.hex").write_text("\n".join(res["steps"]), encoding="utf-8")
        code, res = self.run_pxw("ramp", "--check", "good.hex")
        self.assertEqual(code, 0, res)
        self.assertFalse(res["ramp_chalky"])
        self.assertTrue((self.dir / "g.gpl").exists())


def draw_fighter(sword=False, colour=(40, 90, 200)):
    """A 10x20 standing figure: head, body, two legs with feet at the bottom row; with sword=True a blade raised on
    the right widens the box without moving the feet."""
    w = 16 if sword else 10
    a = np.zeros((20, w, 4), np.uint8)
    a[1:6, 3:7] = [230, 190, 150, 255]
    a[6:14, 2:8] = list(colour) + [255]
    a[14:20, 2:4] = INK + [255]
    a[14:20, 6:8] = INK + [255]
    if sword:
        a[0:12, 12:14] = [200, 200, 210, 255]
        a[8:10, 8:12] = [200, 200, 210, 255]
    return a


class TestActionInputs(Base):
    def setUp(self):
        super().setUp()
        save(draw_fighter(), self.dir / "stance.png")
        save(draw_fighter(sword=True), self.dir / "swing.png")

    def test_stance_on_strip_loop_closed(self):
        code, res = self.run_pxw("action-inputs", "stance.png", "out")
        self.assertEqual(code, 0, res)
        self.assertEqual(res["size"], [1056, 608])
        self.assertEqual(res["scale"], 16)  # 304 // 19 opaque rows
        self.assertTrue(res["loop_closed"])
        f, l = self.load("out/action_first.png"), self.load("out/action_last.png")
        self.assertEqual(f.shape[:2], (608, 1056))
        self.assertTrue((f == l).all())
        g, k = res["ground_y"], res["scale"]
        x0, y0, x1, y1 = res["boxes"][0]
        self.assertEqual(y1, g)  # feet on the ground line
        self.assertEqual((x0 + x1) / 2, 528)  # symmetric feet at the centre
        self.assertEqual(f[g - k:g, x0:x0 + 2 * k, :3].reshape(-1, 3).tolist(), [INK] * (2 * k * k))  # whole-number scale
        self.assertEqual(f[g - 1, x0 + 2 * k, :3].tolist(), f[g - 1, 0, :3].tolist())  # strip shows between the legs
        bgc, flc = f[5, 5, :3].tolist(), f[g, 5, :3].tolist()
        self.assertEqual(bgc, [255, 0, 255])
        self.assertEqual(flc, [204, 0, 204])  # strip darker than the background, across the width
        self.assertEqual(f[g, 1050, :3].tolist(), flc)
        self.assertEqual(len(np.unique(f[..., :3].reshape(-1, 3), axis=0)), 5)  # bg, strip, 3 sprite colours: nothing new
        side = json.loads((self.dir / "out" / "action_inputs.json").read_text())
        self.assertIn("only the character moves", side["prompt"])

    def test_end_pose_keeps_scale_ground_and_feet(self):
        code, res = self.run_pxw("action-inputs", "stance.png", "out", "--last", "swing.png", "--size", "h3-768")
        self.assertEqual(code, 0, res)
        self.assertFalse(res["loop_closed"])
        (a0, _, a1, ay), (b0, _, b1, by) = res["boxes"]
        self.assertEqual(ay, by)
        self.assertEqual(a0, b0)  # feet at the same x although the sword widens the box
        self.assertGreater(b1, a1)
        f, l = self.load("out/action_first.png"), self.load("out/action_last.png")
        self.assertEqual(f.shape[:2], (768, 1344))
        self.assertFalse((f == l).all())

    def test_key_overlap_gate_and_sizes(self):
        save(draw_fighter(colour=(250, 10, 240)), self.dir / "pink.png")
        code, res = self.run_pxw("action-inputs", "pink.png", "out")
        self.assertEqual(code, 1, res)
        self.assertGreater(res["key_overlap"][0], 0.02)
        code, res = self.run_pxw("action-inputs", "pink.png", "out", "--bg", "00ff00", "--size", "1000x600")
        self.assertEqual(code, 0, res)
        self.assertEqual(res["size"], [992, 576])
        self.assertEqual(res["rounded_from"], [1000, 600])
        code, res = self.run_pxw("action-inputs", "stance.png", "out", "--size", "h3-608-portrait")
        self.assertEqual(res["size"], [608, 1056])
        code, res = self.run_pxw("action-inputs", "stance.png", "out", "--size", "40x32")
        self.assertEqual(code, 1, res)


if __name__ == "__main__":
    unittest.main()
