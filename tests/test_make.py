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


if __name__ == "__main__":
    unittest.main()
