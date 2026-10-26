"""Offline tests for pxw.py's animation commands (the old sw.py). Fixtures are drawn in code; nothing is
downloaded and no image is committed.

Run from the repository root: python tests/test_pxw.py
"""
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SW = ROOT / "skills" / "pixelwright" / "scripts" / "pxw.py"
sys.path.insert(0, str(SW.parent))
import pxw as sw  # noqa: E402

WARM = [230, 120, 30]
METAL = [110, 110, 120]
DARK = [60, 60, 70]
CYAN = [40, 190, 230]


def draw_still(path):
    """A 32x32 machine: grey body, a warm lamp, a cyan cell column, a 2-colour stripe band, a small arm,
    transparent sky above."""
    a = np.zeros((32, 32, 4), dtype=np.uint8)
    a[12:32, 4:28] = METAL + [255]
    a[12:32, 4:28:3] = DARK + [255]
    a[14:18, 8:12] = WARM + [255]
    a[16:28, 20:24] = CYAN + [255]
    a[29:31, 4:28] = DARK + [255]
    a[29:31, 4:28:4] = WARM + [255]
    a[8:12, 14:17] = DARK + [255]
    Image.fromarray(a, "RGBA").save(path)
    return a


def brief(**anims):
    return {"id": "machine", "still": "machine.png", "motion": "test machine",
            "extraColours": [[255, 240, 200]],
            "regions": {
                "lamp": {"rects": [[8, 14, 12, 18]], "select": "warm"},
                "cells": {"rects": [[20, 16, 24, 28]]},
                "belt": {"rects": [[4, 29, 28, 31]]},
                "arm": {"rects": [[14, 8, 17, 12]]},
                "armzone": {"rects": [[14, 6, 17, 12]], "alpha": True},
                "body": {"rects": [[4, 12, 28, 32]]},
                "sky": {"rects": [[0, 0, 32, 12]], "alpha": True},
            },
            "animations": anims}


PULSE = {"frames": 6, "focal": "lamp",
         "tracks": [{"effect": "pulse", "region": "lamp", "hot": [255, 240, 200], "strength": 1.0,
                     "curve": [0, 0.6, 1, 1, 0.5, 0]}]}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.still = draw_still(self.dir / "machine.png")

    def tearDown(self):
        self.tmp.cleanup()

    def run_sw(self, *args):
        r = subprocess.run([sys.executable, str(SW), *map(str, args)], capture_output=True, text=True, cwd=self.dir)
        return r.returncode, json.loads(r.stdout) if r.stdout.strip().startswith("{") else r.stdout

    def frames(self, b):
        (self.dir / "b.json").write_text(json.dumps(b))
        code, res = self.run_sw("frames", "b.json", "out", "--no-aw")
        gates = json.loads((self.dir / "out" / "machine.gates.json").read_text())
        return code, res, gates

    def sheet(self, name):
        return np.array(Image.open(self.dir / "out" / f"{name}.png").convert("RGBA"))


class TestFrames(Base):
    def test_pulse_passes_and_rest_is_still(self):
        code, res, g = self.frames(brief(use=PULSE))
        self.assertEqual(code, 0, res)
        self.assertTrue(g["use"]["pass"])
        sheet = self.sheet("machine-use-6f")
        self.assertEqual(sheet.shape, (32, 32 * 6, 4))
        self.assertTrue((sheet[:, :32] == self.still).all())
        self.assertFalse((sheet[:, 64:96] == self.still).all())
        for f in ("machine-use-6f.preview.png", "machine-use-6f.contact.png", "machine-use-6f/f05.png"):
            self.assertTrue((self.dir / "out" / f).is_file(), f)

    def test_place_rest_is_last_frame(self):
        anim = json.loads(json.dumps(PULSE))
        anim["tracks"][0]["curve"] = [1, 1, 0.8, 0.5, 0.2, 0]
        code, res, g = self.frames(brief(place=anim))
        self.assertEqual(g["place"]["rest_frame"], 5)
        self.assertTrue(g["place"]["rest_frame_identical"])

    def test_rest_not_identical_fails(self):
        anim = json.loads(json.dumps(PULSE))
        anim["tracks"][0]["curve"] = [1] * 6
        code, res, g = self.frames(brief(use=anim))
        self.assertEqual(code, 1)
        self.assertFalse(g["use"]["rest_frame_identical"])
        self.assertFalse(g["use"]["pass"])

    def test_sparks_in_listed_sky_region_pass(self):
        anim = {"frames": 4, "focal": "lamp", "tracks": [
            {"effect": "pulse", "region": "lamp", "hot": [255, 240, 200], "curve": [0, 1, 1, 0]},
            {"effect": "sparks", "region": "sky", "source": [14, 10, 16, 11], "bornFrames": [1],
             "colours": [[255, 240, 200]], "count": 6}]}
        code, res, g = self.frames(brief(use=anim))
        self.assertEqual(g["use"]["changed_outside_mask"], 0)
        self.assertTrue(g["use"]["pass"], g["use"])

    def test_one_pixel_outside_mask_counts(self):
        s = sw.Sprite(brief(use=PULSE), str(self.dir))
        frames = sw.build_frames(s, PULSE)
        frames[2][0, 0] = [1, 2, 3, 255]  # one pixel in the sky, outside every track's region
        g = sw.gates(s, PULSE, frames, 0)
        self.assertEqual(g["changed_outside_mask"], 1)
        self.assertEqual(g["alpha_changed_outside_alpha_regions"], 1)
        self.assertEqual(g["new_colours"], 1)
        self.assertFalse(g["pass"])

    def test_new_colour_fails(self):
        s = sw.Sprite(brief(use=PULSE), str(self.dir))
        frames = sw.build_frames(s, PULSE)
        frames[2][15, 9, :3] = [1, 2, 3]
        g = sw.gates(s, PULSE, frames, 0)
        self.assertEqual(g["new_colours"], 1)
        self.assertFalse(g["pass"])

    def test_subtle_is_not_noticeable(self):
        anim = json.loads(json.dumps(PULSE))
        anim["tracks"][0].update(strength=0.05, curve=[0, 0.2, 0.2, 0.2, 0.2, 0])
        code, res, g = self.frames(brief(use=anim))
        self.assertFalse(g["use"]["noticeable"])
        self.assertFalse(g["use"]["pass"])

    def test_threshold_override(self):
        anim = json.loads(json.dumps(PULSE))
        anim["tracks"][0].update(strength=0.05, curve=[0, 0.2, 0.2, 0.2, 0.2, 0])
        anim["noticeable"] = {"share": 0.0, "luma": 0}
        code, res, g = self.frames(brief(use=anim))
        self.assertTrue(g["use"]["noticeable"])

    def test_legacy_use_place_keys_and_cardid(self):
        b = brief()
        del b["animations"]
        b["use"] = PULSE
        b["cardId"] = b.pop("id")
        code, res, g = self.frames(b)
        self.assertEqual(code, 0, res)
        self.assertIn("use", g)

    def test_unknown_effect_is_an_error(self):
        (self.dir / "b.json").write_text(json.dumps(brief(use={"frames": 2, "tracks": [
            {"effect": "wobble", "region": "lamp"}]})))
        code, res = self.run_sw("frames", "b.json", "out", "--no-aw")
        self.assertEqual(code, 1)
        self.assertIn("unknown effect", res["error"])


class TestEffects(Base):
    def make(self, anim):
        s = sw.Sprite(brief(x=anim), str(self.dir))
        return s, sw.build_frames(s, anim)

    def test_every_effect_stays_in_palette_and_mask(self):
        tracks = {
            "spill": {"effect": "spill", "region": "body", "source": [8, 14, 12, 18], "tint": [60, 30, 0]},
            "darken": {"effect": "darken", "region": "body"},
            "glint": {"effect": "glint", "region": "cells", "hot": [255, 240, 200], "curve": [0, 0.5, 0.9, 1]},
            "dust": {"effect": "dust", "region": "body", "band": [24, 32], "colour": [150, 140, 125],
                     "curve": [1, 0.7, 0.3, 0]},
            "fill": {"effect": "fill", "region": "cells", "hot": [255, 240, 200], "curve": [0, 0.4, 0.8, 1]},
            "scroll": {"effect": "scroll", "region": "belt", "period": 4, "curve": [0, 0.25, 0.5, 0.75]},
        }
        for name, t in tracks.items():
            with self.subTest(name):
                anim = {"frames": 4, "focal": t["region"], "tracks": [t], "noticeable": {"share": 0, "luma": 0}}
                s, frames = self.make(anim)
                g = sw.gates(s, anim, frames, None)
                self.assertEqual(g["changed_outside_mask"], 0, name)
                self.assertEqual(g["new_colours"], 0, name)

    def test_scroll_full_period_returns_to_still(self):
        anim = {"frames": 5, "tracks": [{"effect": "scroll", "region": "belt", "period": 4,
                                         "curve": [0, 0.25, 0.5, 0.75, 1.0]}]}
        s, frames = self.make(anim)
        self.assertTrue((frames[4] == self.still).all())
        self.assertFalse((frames[1] == self.still).all())
        # content only changes phase: the belt keeps the same colour counts
        belt = s.regions["belt"]
        self.assertEqual(sorted(map(tuple, frames[1][belt].tolist())), sorted(map(tuple, self.still[belt].tolist())))

    def test_shift_moves_part_whole_pixels(self):
        anim = {"frames": 3, "tracks": [{"effect": "shift", "part": "arm", "region": "armzone", "by": [0, -2],
                                         "behind": "clear", "curve": [0, 1, 0]}]}
        s, frames = self.make(anim)
        self.assertTrue((frames[1][6:10, 14:17, :3] == DARK).all())
        self.assertTrue((frames[1][10:12, 14:17, 3] == 0).all())
        self.assertTrue((frames[2] == self.still).all())

    def test_rotate_zero_is_identity_on_part(self):
        anim = {"frames": 2, "tracks": [{"effect": "rotate", "part": "arm", "region": "armzone", "pivot": [15.5, 12],
                                         "curve": [0, 0]}]}
        s, frames = self.make(anim)
        self.assertTrue((frames[0][8:12, 14:17] == self.still[8:12, 14:17]).all())

    def test_puffs_and_sparks_draw_only_in_zone(self):
        anim = {"frames": 6, "tracks": [
            {"effect": "puffs", "region": "sky", "source": [15, 8], "bornFrames": [0, 2],
             "colours": [[200, 200, 210], [150, 150, 160]]},
            {"effect": "sparks", "region": "sky", "source": [14, 8, 17, 9], "bornFrames": [1, 2],
             "colours": [[255, 240, 200]]}]}
        s, frames = self.make(anim)
        for f in frames:
            diff = (f != self.still).any(-1)
            self.assertFalse((diff & ~s.regions["sky"]).any())
        self.assertTrue(any((f != self.still).any() for f in frames))

    def test_external_paste_keeps_outside_region(self):
        ext = np.tile(np.array([255, 0, 255, 255], dtype=np.uint8), (32, 64, 1))  # magenta, 2 frames
        Image.fromarray(ext, "RGBA").save(self.dir / "ext.png")
        anim = {"frames": 2, "tracks": [{"effect": "external", "region": "lamp", "sheet": "ext.png"}]}
        s, frames = self.make(anim)
        lamp = s.regions["lamp"]
        self.assertTrue((frames[0][~lamp] == self.still[~lamp]).all())
        # magenta snapped to the lamp's warm ramp, never pasted raw
        self.assertFalse((frames[0][lamp][:, :3] == [255, 0, 255]).all(-1).any())

    def test_external_soft_keep_keeps_the_sheets_alpha(self):
        ext = np.zeros((32, 32, 4), dtype=np.uint8)
        ext[:, :] = [255, 200, 40, 90]
        Image.fromarray(ext, "RGBA").save(self.dir / "soft.png")
        t = {"effect": "external", "region": "lamp", "sheet": "soft.png"}
        s, hard = self.make({"frames": 1, "tracks": [t]})
        _, soft = self.make({"frames": 1, "tracks": [dict(t, soft="keep")]})
        lamp = s.regions["lamp"]
        # hardened, alpha 90 becomes a hole; kept, every lamp pixel carries the sheet's alpha 90
        self.assertTrue((hard[0][lamp][:, 3] == 0).all())
        self.assertTrue((soft[0][lamp][:, 3] == 90).all())
        self.assertTrue((soft[0][~lamp] == self.still[~lamp]).all())

    def test_bend_sways_hem_keeps_rail_and_fills_behind(self):
        a = np.zeros((20, 20, 4), dtype=np.uint8)
        a[:, :] = [120, 80, 40, 255]
        a[4:16, 8:12] = [230, 225, 210, 255]
        Image.fromarray(a, "RGBA").save(self.dir / "cloth.png")
        b = {"id": "cloth", "still": "cloth.png", "regions": {
            "cloth": {"rects": [[8, 4, 12, 16]]}, "sway": {"rects": [[6, 4, 14, 16]]}}}
        anim = {"frames": 2, "tracks": [{"effect": "bend", "region": "sway", "part": "cloth", "amp": 2,
                                         "curve": [0, 1]}]}
        s = sw.Sprite(b, str(self.dir))
        frames = sw.build_frames(s, anim)
        self.assertTrue((frames[0] == a).all())
        f = frames[1]
        self.assertTrue((f[4] == a[4]).all())
        self.assertTrue((f[15, 10:14, :3] == [230, 225, 210]).all())
        # the hem's old left edge shows the wall beside it, not a hole or a stretched cloth
        self.assertTrue((f[15, 8:10] == [120, 80, 40, 255]).all())
        self.assertTrue((f[..., 3] == 255).all())
        diff = (f != a).any(-1)
        self.assertFalse((diff & ~s.regions["sway"]).any())

    def test_brighten_lifts_both_tones_and_keeps_their_order(self):
        a = np.zeros((8, 8, 4), dtype=np.uint8)
        a[:, :] = [40, 40, 40, 255]
        a[2:6, 2:6] = [150, 60, 20, 255]
        a[2:6:2, 2:6:2] = [200, 90, 30, 255]
        Image.fromarray(a, "RGBA").save(self.dir / "oven.png")
        b = {"id": "oven", "still": "oven.png", "regions": {"fire": {"rects": [[2, 2, 6, 6]]}},
             "extraColours": [[210, 110, 35], [250, 140, 40], [255, 160, 50], [255, 200, 120]]}
        s = sw.Sprite(b, str(self.dir))
        lit = sw.build_frames(s, {"frames": 1, "tracks": [{"effect": "brighten", "region": "fire", "gain": 0.6}]})[0]
        fire = s.regions["fire"]
        litCols = {tuple(c) for c in lit[fire][:, :3]}
        self.assertEqual(len(litCols), 2)
        self.assertFalse(litCols & {(150, 60, 20), (200, 90, 30)})
        self.assertGreater(lit[2, 2, :3].astype(int).sum(), lit[2, 3, :3].astype(int).sum())
        self.assertTrue((lit[~fire] == a[~fire]).all())

    def test_brighten_hotspot_is_hottest_and_whitest_at_its_centre(self):
        a = np.zeros((12, 12, 4), dtype=np.uint8)
        a[:, :] = [40, 40, 40, 255]
        a[1:11, 1:11] = [150, 70, 30, 255]
        Image.fromarray(a, "RGBA").save(self.dir / "oven.png")
        ramp = [[150 + 10 * j, 70 + 18 * j, 30 + 22 * j] for j in range(1, 6)] + [[175, 80, 33]]
        b = {"id": "oven", "still": "oven.png", "regions": {"fire": {"rects": [[1, 1, 11, 11]]}},
             "extraColours": ramp}
        s = sw.Sprite(b, str(self.dir))
        t = {"effect": "brighten", "region": "fire", "gain": 0.8, "hotspot": [3, 3], "radius": 8, "floor": 0.2,
             "tint": [1.0, 0.7, 0.4], "coreTint": [1.0, 1.0, 1.0]}
        lit = sw.build_frames(s, {"frames": 1, "tracks": [t]})[0].astype(int)
        near, far = lit[3, 3, :3], lit[10, 10, :3]
        self.assertGreater(near.sum(), far.sum())
        # the core is whiter: its blue rises closer to its red than at the rim
        self.assertLess(near[0] - near[2], far[0] - far[2])
        # the floor keeps the far wall lit, a little
        self.assertGreater(far.sum(), 250)
        self.assertTrue((lit[0] == a[0]).all())

    def test_soft_over_keeps_a_wall_under_a_moved_soft_rim(self):
        a = np.zeros((6, 10, 4), dtype=np.uint8)
        a[:, 6:] = [120, 80, 40, 255]
        a[1:5, 2:4] = [230, 225, 210, 255]
        a[1:5, 4] = [230, 225, 210, 60]
        Image.fromarray(a, "RGBA").save(self.dir / "rim.png")
        b = {"id": "rim", "still": "rim.png", "regions": {
            "cloth": {"rects": [[2, 1, 5, 5]]}, "zone": {"rects": [[2, 1, 8, 5]], "alpha": True}},
             "extraColours": [[150, 105, 65]]}
        s = sw.Sprite(b, str(self.dir))
        t = {"effect": "shift", "region": "zone", "part": "cloth", "by": [2, 0], "behind": "clear", "curve": [1]}
        hard = sw.build_frames(s, {"frames": 1, "tracks": [t]})[0]
        soft = sw.build_frames(s, {"frames": 1, "tracks": [dict(t, soft="over")]})[0]
        # replaced, the rim punches a near-transparent hole in the wall; composited, the wall stays solid
        self.assertEqual(int(hard[2, 6, 3]), 60)
        self.assertEqual(int(soft[2, 6, 3]), 255)
        self.assertTrue((soft[2, 6, :3] == [150, 105, 65]).all())
        # opaque cloth pixels still move exactly, and the rim over clear air keeps its own alpha
        self.assertTrue((soft[2, 4:6] == [230, 225, 210, 255]).all())
        self.assertTrue((soft[2, 2:4, 3] == 0).all())

    def test_behind_grow_fills_the_hole_with_the_ground_around_it(self):
        rng = np.random.default_rng(2)
        a = np.zeros((24, 24, 4), dtype=np.uint8)
        a[..., 3] = 255
        a[..., 0] = 180 + rng.integers(0, 4, (24, 24)) * 12
        a[..., 1] = 150 + rng.integers(0, 4, (24, 24)) * 8
        a[..., 2] = 100
        a[9:15, 8:16, :3] = [70, 75, 90]
        Image.fromarray(a, "RGBA").save(self.dir / "pit.png")
        b = {"id": "pit", "still": "pit.png", "regions": {
            "block": {"rects": [[8, 9, 16, 15]]}, "zone": {"rects": [[8, 6, 16, 15]]}}}
        s = sw.Sprite(b, str(self.dir))
        t = {"effect": "shift", "region": "zone", "part": "block", "by": [0, -3], "behind": "grow", "curve": [1]}
        f = sw.build_frames(s, {"frames": 1, "tracks": [t]})[0]
        again = sw.build_frames(sw.Sprite(b, str(self.dir)), {"frames": 1, "tracks": [t]})[0]
        bare = f[12:15, 8:16, :3].reshape(-1, 3)
        ground = {tuple(c) for c in a[..., :3].reshape(-1, 3)} - {(70, 75, 90)}
        # every bare pixel is a ground colour, the patch keeps the ground's variety, and the block moved intact
        self.assertTrue(all(tuple(c) in ground for c in bare))
        self.assertGreater(len({tuple(c) for c in bare}), 4)
        self.assertTrue((f[6:12, 8:16, :3] == [70, 75, 90]).all())
        self.assertTrue((f == again).all())

    def test_bands_drift_along_dir_and_loop(self):
        a = np.zeros((8, 16, 4), dtype=np.uint8)
        a[:, :] = [40, 40, 40, 255]
        a[2:6, 2:14] = [150, 170, 200, 255]
        Image.fromarray(a, "RGBA").save(self.dir / "loom.png")
        ramp = [[150 - 15 * j, 170 - 17 * j, 200 - 20 * j] for j in range(1, 5)]
        b = {"id": "loom", "still": "loom.png", "regions": {"cloth": {"rects": [[2, 2, 14, 6]]}},
             "extraColours": ramp}
        s = sw.Sprite(b, str(self.dir))
        t = {"effect": "bands", "region": "cloth", "period": 6, "gain": -0.3, "curve": [0, 0.25, 1]}
        frames = sw.build_frames(s, {"frames": 3, "tracks": [t]})
        cloth = s.regions["cloth"]

        def darkest(f):
            return int(f[3, 2:14, :3].astype(int).sum(-1).argmin()) + 2

        # a band sits on every multiple of the period; a quarter cycle later it has moved 1.5 px along dir
        self.assertIn(darkest(frames[0]), (6, 12))
        self.assertGreater(frames[1][3, 6, :3].astype(int).sum(), frames[0][3, 6, :3].astype(int).sum())
        self.assertLess(frames[1][3, 8, :3].astype(int).sum(), a[3, 8, :3].astype(int).sum())
        # k = 1 is the same picture as k = 0: one full cycle
        self.assertTrue((frames[2] == frames[0]).all())
        for f in frames:
            self.assertTrue((f[~cloth] == a[~cloth]).all())
            self.assertTrue((f[..., :3][cloth].astype(int) <= a[..., :3][cloth].astype(int)).all())

    def test_loop_seam_gate(self):
        anim = {"frames": 4, "rest": "none", "noticeable": {"share": 0, "luma": 0},
                "tracks": [{"effect": "scroll", "region": "belt", "period": 4, "curve": [0, 0.25, 0.5, 0.75]}]}
        s, frames = self.make(anim)
        g = sw.gates(s, anim, frames, None)
        self.assertTrue(g["loop_seam_ok"])
        # a level that creeps up a little each frame and drops to empty at the wrap: the seam is the big jump
        ramp = {"frames": 4, "rest": "none", "noticeable": {"share": 0, "luma": 0},
                "tracks": [{"effect": "fill", "region": "cells", "curve": [0.25, 0.4, 0.55, 0.7]}]}
        s, frames = self.make(ramp)
        g = sw.gates(s, ramp, frames, None)
        self.assertFalse(g["loop_seam_ok"], g)


try:
    import tifffile
except ImportError:
    tifffile = None

WHEEL_ID = [255, 0, 0]
PLATE_GREEN = [0, 200, 0]


def draw_wheel_render(folder, frames=7, nSym=4, occlude0=False):
    """A 64x64 render of a disc in the XY plane turning about Z, seen at an angle (screen y = 0.6 Y): per frame an
    ID PNG and a 16-bit pos TIFF of the body point each pixel shows, frame i turned by i * 15 degrees (so frame 6 is
    one quarter turn: one interval of 4-fold symmetry). Painted frame 0: nSym dark spokes on a tan disc plus one red
    mark on a single spoke (not symmetric), a blue-grey ground and a house block the wheel never touches. The plate
    is the ground with the disc painted out in green. Returns (painted, plate, masks, body points)."""
    folder.mkdir(parents=True, exist_ok=True)
    n, c, R, ext = 64, 32.0, 20.0, 1.0
    yy, xx = np.mgrid[0:n, 0:n] + 0.5
    X, Y = (xx - c) / R, (yy - c) / (0.6 * R)
    disc = X ** 2 + Y ** 2 <= 1
    masks, bodies = [], []
    for i in range(frames):
        th = math.radians(15 * i)
        # the body point under each pixel: the screen point turned back by the wheel's angle
        L = np.dstack([X * math.cos(th) + Y * math.sin(th), -X * math.sin(th) + Y * math.cos(th), np.zeros_like(X)])
        m = disc.copy()
        if occlude0 and i == 0:
            m[30:35, 40:46] = False  # something in front of the wheel in frame 0 only
        idimg = np.zeros((n, n, 3), np.uint8)
        idimg[m] = WHEEL_ID
        Image.fromarray(idimg).save(folder / f"id_{i:03d}.png")
        enc = np.clip(np.round((L / (2 * ext) + 0.5) * 65535), 0, 65535).astype(np.uint16)
        tifffile.imwrite(str(folder / f"pos_{i:03d}.tif"), np.dstack([enc, np.full((n, n), 65535, np.uint16)]))
        masks.append(m)
        bodies.append(L)
    meta = {"pos_extent": ext, "id_colours": {"wheel": [1, 0, 0]}, "loop": [{"rotate_axis": "Z"}],
            "rings": {"wheel": {"arms": nSym}}}
    (folder / "sprite.json").write_text(json.dumps(meta))
    L0 = bodies[0]
    ang = np.arctan2(L0[..., 1], L0[..., 0])
    rad = np.hypot(L0[..., 0], L0[..., 1])
    painted = np.zeros((n, n, 3), np.uint8)
    painted[:] = [90, 100, 120]
    painted[52:62, 2:14] = [200, 190, 160]  # the house: far from the wheel
    painted[disc] = [190, 150, 100]
    spoke = disc & (np.abs(np.sin(nSym * ang / 2)) < 0.25)
    painted[spoke] = [80, 50, 30]
    painted[disc & (rad > 0.85)] = [120, 80, 40]
    painted[disc & (np.abs(ang) < 0.12) & (rad > 0.4) & (rad < 0.7)] = [220, 40, 40]  # one marked spoke
    plate = painted.copy()
    plate[disc] = PLATE_GREEN
    return painted, plate, masks, bodies


@unittest.skipIf(tifffile is None, "tifffile not installed")
class TestModelRotate(Base):
    def setup_model(self, frames=7, nSym=4, occlude0=False, track=None, animFrames=6):
        painted, plate, masks, _ = draw_wheel_render(self.dir / "render", frames, nSym, occlude0)
        Image.fromarray(painted).save(self.dir / "painted.png")
        Image.fromarray(plate).save(self.dir / "plate.png")
        still = sw._downscale(painted / 255.0, np.ones((64, 64)), 32, 32).astype(np.uint8)
        Image.fromarray(still, "RGBA").save(self.dir / "mill.png")
        t = {"effect": "model_rotate", "region": "wheel", "frames": "render", "part": "wheel",
             "painted": "painted.png", "plate": "plate.png"}
        t.update(track or {})
        b = {"id": "mill", "still": "mill.png",
             "regions": {"wheel": {"model": {"frames": "render", "part": "wheel"}, "alpha": True},
                         "house": {"rects": [[1, 26, 7, 31]]}},
             "animations": {"turn": {"frames": animFrames, "rest": "none", "fps": 8, "tracks": [t]}}}
        (self.dir / "b.json").write_text(json.dumps(b))
        return still, masks

    def run_turn(self):
        code, res = self.run_sw("frames", "b.json", "out", "--no-aw")
        g = json.loads((self.dir / "out" / "mill.gates.json").read_text())["turn"]
        sheet = np.array(Image.open(self.dir / "out" / f"mill-turn-{g['frames']}f.png").convert("RGBA"))
        return code, res, g, [sheet[:, j * 32:(j + 1) * 32] for j in range(g["frames"])]

    def test_loop_closes_and_outside_untouched(self):
        still, _ = self.setup_model()
        code, res, g, frames = self.run_turn()
        self.assertEqual(code, 0, res)
        self.assertTrue(g["pass"], g)
        self.assertEqual(g["changed_outside_mask"], 0)
        self.assertTrue(g["loop_seam_ok"])
        house = np.zeros((32, 32), bool)
        house[26:31, 1:7] = True
        for f in frames:
            self.assertTrue((f[house] == still[house]).all())
        self.assertTrue(any((f != frames[0]).any() for f in frames[1:]))
        self.assertTrue((self.dir / "out" / "mill-wheel-hires" / "f05.png").is_file())

    def test_one_interval_lands_on_frame_zero(self):
        # frame 6 is frame 0 turned by exactly one spoke interval; the fold makes it frame 0 again
        self.setup_model(animFrames=7)
        code, res, g, frames = self.run_turn()
        same = (frames[6] == frames[0]).all(-1).mean()
        self.assertGreater(same, 0.99, same)
        # without the fold (symmetry 1) the marked spoke moves on, so a quarter turn is not frame 0
        sw._CACHE.clear()
        self.setup_model(animFrames=7, track={"symmetry": 1})
        code, res, g, frames = self.run_turn()
        self.assertLess((frames[6] == frames[0]).all(-1).mean(), same)

    def test_unmatched_part_pixels_never_show_the_plate(self):
        # symmetry 1 and a block in front of the wheel in frame 0: later frames show body points frame 0 never saw
        self.setup_model(occlude0=True, track={"symmetry": 1})
        code, res, g, frames = self.run_turn()
        self.assertGreater(max(g["model"]["wheel"]["unmatched_px"]), 0, g["model"])
        _, _, masks, _ = draw_wheel_render(self.dir / "render2", 7, 4, True)
        for j in range(1, 6):
            hi = np.array(Image.open(self.dir / "out" / "mill-wheel-hires" / f"f{j:02d}.png").convert("RGB"))
            inner = sw._erode(masks[j], 1)
            self.assertFalse((hi[inner] == PLATE_GREEN).all(-1).any(), j)

    def test_missing_axis_is_a_clean_failure(self):
        self.setup_model(track={"part": "wheel"})
        meta = json.loads((self.dir / "render" / "sprite.json").read_text())
        meta.pop("loop")
        (self.dir / "render" / "sprite.json").write_text(json.dumps(meta))
        code, res = self.run_sw("frames", "b.json", "out", "--no-aw")
        self.assertEqual(code, 1)
        self.assertIn("axis", res["error"])


class TestRotatePlane(Base):
    def bar(self, t):
        b = brief(x={"frames": 1, "tracks": [t]})
        a = np.zeros((32, 32, 4), np.uint8)
        a[15:17, 16:25] = DARK + [255]  # a horizontal bar from the pivot (16, 16) out to x = 24
        Image.fromarray(a, "RGBA").save(self.dir / "machine.png")
        b["regions"] = {"bar": {"rects": [[16, 15, 25, 17]]}, "zone": {"rects": "all", "alpha": True}}
        s = sw.Sprite(b, str(self.dir))
        return sw.build_frames(s, b["animations"]["x"])[0]

    def test_plane_foreshortens_the_turn(self):
        base = {"effect": "rotate", "part": "bar", "region": "zone", "pivot": [16, 16], "curve": [90]}
        flat = self.bar(base)
        tilted = self.bar(dict(base, plane=[[1, 0], [0, 0.5]]))
        rim = [[16 + 8 * math.cos(p), 16 + 4 * math.sin(p)] for p in np.linspace(0, 2 * math.pi, 16, endpoint=False)]
        fitted = self.bar(dict(base, plane={"rim": rim}))
        ys = np.nonzero(flat[..., 3])[0]
        yt = np.nonzero(tilted[..., 3])[0]
        # a quarter turn in the screen plane stands the bar up its full 8 px; in a plane squashed to half height it
        # stands up only 4 px
        self.assertGreaterEqual(ys.max() - 16, 7)
        self.assertLessEqual(yt.max() - 16, 4)
        self.assertGreaterEqual(yt.max() - 16, 3)
        self.assertTrue((fitted == tilted).all())
        # the identity plane is the plain screen rotation
        self.assertTrue((self.bar(dict(base, plane=[[1, 0], [0, 1]])) == flat).all())


class TestCommands(Base):
    def test_buildup_adds_frames_and_ends_on_still(self):
        (self.dir / "b.json").write_text(json.dumps(brief(place=json.loads(json.dumps(PULSE)))))
        code, res = self.run_sw("buildup", "b.json", "b2.json", "--frames", "4")
        self.assertEqual(code, 0, res)
        b2 = json.loads((self.dir / "b2.json").read_text())
        self.assertEqual(b2["animations"]["place"]["frames"], 10)
        b2["animations"]["place"]["tracks"][0]["curve"] = [0] * 10
        b2["animations"]["place"]["noticeable"] = {"share": 0, "luma": 0}
        code, res, g = self.frames(b2)
        self.assertTrue(g["place"]["rest_frame_identical"])
        sheet = self.sheet("machine-place-10f")
        self.assertLess((sheet[:, :32, 3] > 0).sum(), (self.still[..., 3] > 0).sum() * 0.6)

    def test_assemble_every_way_ends_on_still_and_reports_coverage(self):
        (self.dir / "b.json").write_text(json.dumps(brief(place=json.loads(json.dumps(PULSE)))))
        plan = {"frames": 8,
                "regions": {"p_belt": {"rects": [[4, 29, 28, 32]]}, "p_arm": {"rects": [[14, 8, 17, 12]]},
                            "p_cells": {"rects": [[20, 16, 24, 28]]}, "p_lamp": {"rects": [[8, 14, 12, 18]]},
                            "p_left": {"rects": [[4, 12, 14, 29]]}, "p_body": {"rects": [[0, 0, 32, 32]]}},
                "steps": [{"part": "p_belt", "how": "weld", "dir": "right", "at": [0, 2]},
                          {"part": "p_arm", "how": "hinge", "pivot": [15, 12], "angle": -60, "at": [5, 8]},
                          {"part": "p_cells", "how": "drone", "at": [3, 6]},
                          {"part": "p_lamp", "how": "telescope", "dir": "up", "at": [4, 6]},
                          {"part": "p_left", "how": "trolley", "from": [-20, 0], "at": [1, 4]},
                          {"part": "p_body", "how": "crane", "at": [1, 5]}]}
        (self.dir / "plan.json").write_text(json.dumps(plan))
        code, res = self.run_sw("assemble", "b.json", "b2.json", "--plan", "plan.json")
        self.assertEqual(code, 0, res)
        self.assertEqual(res["uncovered_pixels"], 0)
        b2 = json.loads((self.dir / "b2.json").read_text())
        b2["animations"]["place"]["tracks"][0]["curve"] = [0] * 14
        code, res, g = self.frames(b2)
        self.assertTrue(g["place"]["pass"], g["place"])
        sheet = self.sheet("machine-place-14f")
        # frame 0: only the first weld seam, its welding drone and sparks stand
        self.assertLess((sheet[:, :32, 3] > 0).sum(), (self.still[..., 3] > 0).sum() * 0.1)
        mid = sheet[:, 3 * 32:4 * 32]
        self.assertFalse((mid == self.still).all())

    def test_assemble_ramps_dust_and_machines_kick_up_puffs(self):
        place = json.loads(json.dumps(PULSE))
        place["tracks"].append({"effect": "dust", "region": "body", "band": [26, 32], "colour": [150, 140, 125],
                                "curve": [1, 1, 0.6, 0.3, 0, 0]})
        (self.dir / "b.json").write_text(json.dumps(brief(place=place)))
        plan = {"frames": 6,
                "regions": {"p_belt": {"rects": [[4, 29, 28, 32]]}, "p_left": {"rects": [[4, 12, 14, 29]]},
                            "p_body": {"rects": [[0, 0, 32, 32]]}},
                "steps": [{"part": "p_belt", "how": "weld", "dir": "right", "at": [0, 3]},
                          {"part": "p_left", "how": "trolley", "from": [-20, 0], "at": [1, 4]},
                          {"part": "p_body", "how": "crane", "at": [2, 5]}]}
        (self.dir / "plan.json").write_text(json.dumps(plan))
        code, res = self.run_sw("assemble", "b.json", "b2.json", "--plan", "plan.json")
        self.assertEqual(code, 0, res)
        b2 = json.loads((self.dir / "b2.json").read_text())
        dust = next(t for t in b2["animations"]["place"]["tracks"] if t["effect"] == "dust")
        # the haze builds up during construction instead of standing at full strength from frame 0
        self.assertLess(dust["curve"][0], 0.2)
        self.assertEqual(dust["curve"][:6], sorted(dust["curve"][:6]))
        self.assertTrue(dust["lumpy"])
        asm = b2["animations"]["place"]["tracks"][-1]
        self.assertEqual(asm["dust"][0], [150, 140, 125])
        code, res, g = self.frames(b2)
        self.assertTrue(g["place"]["pass"], g["place"])
        sheet = self.sheet("machine-place-12f")
        puff = {tuple(c) for c in asm["dust"]}
        seen = {tuple(sheet[y, x, :3]) for y in range(32) for x in range(32 * 2, 32 * 4) if sheet[y, x, 3]}
        self.assertTrue(puff & seen, "no machine dust in frames 2 and 3")

    def test_weld_front_is_ragged_and_covers_part_at_ends(self):
        st = {"part": "p", "how": "weld", "dir": "right", "at": [0, 4], "ragged": 2, "seed": 3}
        bb = (0, 0, 40, 10)
        axis, f0 = sw._weld_front(st, bb, 0.0)
        _, f1 = sw._weld_front(st, bb, 1.0)
        _, fm = sw._weld_front(st, bb, 0.5)
        self.assertEqual(axis, "x")
        self.assertTrue((f0 <= 0).all() and (f1 >= 40).all())
        self.assertGreater(len(set(fm.tolist())), 1, "the seam is a straight line")

    def test_arc_drone_cart_draw_in_zone_and_palette(self):
        b = brief()
        b["regions"]["all"] = {"rects": "all", "alpha": True}
        tracks = {
            "arc": {"effect": "arc", "region": "all", "paths": [[6, 14, 26, 26], [6, 26, 26, 14]],
                    "colours": [[255, 240, 200], CYAN], "flicker": 0, "curve": [0, 1, 1, 0]},
            "drone": {"effect": "drone", "region": "all", "path": [[0, 2], [16, 8], [34, 2]], "torch": [16, 14],
                      "torchFrames": [1, 2], "curve": [-1, 0.5, 0.5, -1]},
            "cart": {"effect": "cart", "region": "all", "from": -10, "to": 40, "y": 31, "curve": [-1, 0.3, 0.6, -1]},
        }
        for name, t in tracks.items():
            with self.subTest(name):
                anim = {"frames": 4, "focal": "body", "tracks": [t], "rest": "first"}
                b["animations"] = {"use": anim}
                s = sw.Sprite(b, str(self.dir))
                frames = sw.build_frames(s, anim)
                g = sw.gates(s, anim, frames, 0)
                self.assertTrue(g["rest_frame_identical"], name)
                self.assertEqual(g["new_colours"], 0, name)
                self.assertTrue((frames[1] != frames[0]).any(), name)
                self.assertTrue((frames[3] == frames[0]).all(), f"{name} should be hidden at k < 0 or off")

    def test_assemble_reports_uncovered_pixels(self):
        (self.dir / "b.json").write_text(json.dumps(brief(place=json.loads(json.dumps(PULSE)))))
        plan = {"frames": 4, "regions": {"p_belt": {"rects": [[4, 29, 28, 32]]}},
                "steps": [{"part": "p_belt", "how": "weld", "at": [0, 3]}]}
        (self.dir / "plan.json").write_text(json.dumps(plan))
        code, res = self.run_sw("assemble", "b.json", "b2.json", "--plan", "plan.json")
        self.assertEqual(code, 1)
        self.assertGreater(res["uncovered_pixels"], 0)

    def cottage(self):
        """A 48x48 timber-framed cottage seen from above at an angle: dark posts every 6 px in pale daub walls, a
        thatch roof band, a plank pile at the front left, no grey stone (the footing must still sample the still)."""
        a = np.zeros((48, 48, 4), dtype=np.uint8)
        a[18:41, 8:41] = [210, 190, 150, 255]
        a[18:41, 8:41:6] = [70, 45, 30, 255]
        a[38:41, 8:41] = [70, 45, 30, 255]
        a[6:23, 6:43] = [180, 150, 80, 255]
        a[6:23:3, 6:43:2] = [150, 120, 60, 255]
        a[42:44, 4:9] = [120, 80, 40, 255]
        Image.fromarray(a, "RGBA").save(self.dir / "cottage.png")
        (self.dir / "c.json").write_text(json.dumps({"id": "cottage", "still": "cottage.png", "motion": "raised on site",
                                                     "regions": {}}))
        plan = {"vocabulary": "natural", "frames": 20, "fps": 12,
                "regions": {"roof": {"rects": [[6, 6, 43, 23]]}, "lumber": {"rects": [[4, 42, 9, 44]]}},
                "roof": "roof", "lumber": "lumber",
                "groundBase": {"left": {"x": 6, "y": 38}, "front": {"x": 24, "y": 44}, "right": {"x": 42, "y": 38}},
                "wallHeight": 10, "eave": [[6, 22], [42, 22]], "ridge": [[6, 7], [42, 7]],
                "ladder": [[34, 42], [32, 26]], "rafters": 6}
        (self.dir / "plan.json").write_text(json.dumps(plan))
        return a, plan

    def test_natural_assemble_builds_up_from_the_ground_and_ends_on_still(self):
        still, plan = self.cottage()
        code, res = self.run_sw("assemble", "c.json", "c2.json", "--plan", "plan.json")
        self.assertEqual(code, 0, res)
        self.assertEqual(res["vocabulary"], "natural")
        self.assertGreater(res["parts"]["timber"], 0)
        self.assertGreater(res["parts"]["infill"], 0)
        self.assertEqual(res["parts"]["lumber"], 10)
        code, res = self.run_sw("frames", "c2.json", "out", "--no-aw")
        g = json.loads((self.dir / "out" / "cottage.gates.json").read_text())["place"]
        self.assertTrue(g["pass"], g)
        self.assertTrue(g["rest_frame_identical"])
        self.assertEqual(g["new_colours"], 0)
        sheet = self.sheet("cottage-place-20f")
        frame = [sheet[:, j * 48:(j + 1) * 48] for j in range(20)]
        roof = np.zeros((48, 48), dtype=bool)
        roof[6:23, 6:43] = True
        same = [(fr == still).all(-1) & (still[..., 3] > 0) for fr in frame]
        # frame 0: the plank pile stands; of the walls only a ragged first course (and string in timber colour)
        self.assertTrue(same[0][42:44, 4:9].all())
        self.assertLess(same[0][18:41, 8:41].mean(), 0.1)
        self.assertFalse(same[0][roof].any())
        # the walls rise from the ground: low courses stand before high ones, and before any roof
        low, high = (same[9][34:38, 8:41].mean(), same[9][24:28, 8:41].mean())
        self.assertGreater(low, high)
        self.assertLess(same[9][roof].mean(), 0.05)
        # the roof is laid from the eave up: near the eave first, the ridge last
        mid = next(j for j in range(20) if 0.2 < same[j][roof].mean() < 0.8)
        self.assertGreater(same[mid][19:22, 6:43].mean(), same[mid][7:10, 6:43].mean())
        # built share never falls back
        shares = [same[j][still[..., 3] > 0].mean() for j in range(20)]
        self.assertEqual(shares, sorted(shares))

    def test_natural_site_lines_stay_inside_the_finished_silhouette(self):
        still, plan = self.cottage()
        empty = still[..., 3] == 0
        code, res = self.run_sw("assemble", "c.json", "c2.json", "--plan", "plan.json")
        self.assertEqual(code, 0, res)
        self.run_sw("frames", "c2.json", "out", "--no-aw")
        g = json.loads((self.dir / "out" / "cottage.gates.json").read_text())["place"]
        self.assertEqual(g["drawn_outside_silhouette"], 0)
        self.assertTrue(g["pass"], g)
        sheet = self.sheet("cottage-place-20f")
        for j in range(20):
            self.assertFalse((sheet[:, j * 48:(j + 1) * 48, 3] > 0)[empty].any(), j)
        # unclipped, the string, ladder and rafters run out over empty ground and sky, and the gate fails
        plan["clip"] = False
        (self.dir / "plan.json").write_text(json.dumps(plan))
        self.run_sw("assemble", "c.json", "c3.json", "--plan", "plan.json")
        self.run_sw("frames", "c3.json", "out3", "--no-aw")
        g = json.loads((self.dir / "out3" / "cottage.gates.json").read_text())["place"]
        self.assertGreater(g["drawn_outside_silhouette"], 0)
        self.assertFalse(g["pass"])

    def test_natural_assemble_needs_the_geometry(self):
        self.cottage()
        plan = json.loads((self.dir / "plan.json").read_text())
        del plan["eave"]
        (self.dir / "plan.json").write_text(json.dumps(plan))
        code, res = self.run_sw("assemble", "c.json", "c2.json", "--plan", "plan.json")
        self.assertEqual(code, 1)
        self.assertIn("eave", json.dumps(res))

    def test_mask_reports_empty_region(self):
        b = brief(use=PULSE)
        b["regions"]["nothing"] = {"rects": [[0, 0, 2, 2]]}  # sky is transparent, so opaque-only gives 0 pixels
        (self.dir / "b.json").write_text(json.dumps(b))
        code, res = self.run_sw("mask", "b.json", "mask.png")
        self.assertEqual(code, 1)
        self.assertEqual(res["empty_regions"], ["nothing"])
        self.assertTrue((self.dir / "mask.png").is_file())

    def test_grid_contact_pack(self):
        code, res = self.run_sw("grid", "machine.png", "grid.png", "--zoom", "4")
        self.assertEqual((code, res["size"]), (0, [32, 32]))
        code, res = self.run_sw("pack", "sheet.png", "machine.png", "machine.png", "machine.png")
        self.assertEqual(res["frames"], 3)
        code, res = self.run_sw("contact", "sheet.png", "c.png", "--frames", "3")
        self.assertEqual(res["frame_size"], [32, 32])
        Image.new("RGBA", (8, 8)).save(self.dir / "small.png")
        code, res = self.run_sw("pack", "bad.png", "machine.png", "small.png")
        self.assertEqual(code, 1)

    def test_review_page_lists_and_hides_decided(self):
        self.frames(brief(use=PULSE))
        code, page = self.run_sw("review", ".", "--print-page")
        self.assertIn('data-key="machine/use"', page)
        (self.dir / "picks.json").write_text(json.dumps({"items": {"machine/use": {"pick": "keep"}}}))
        code, page = self.run_sw("review", ".", "--print-page")
        self.assertNotIn('data-key="machine/use"', page)
        (self.dir / "review-extra.json").write_text(json.dumps([{"key": "still/x", "title": "x", "kind": "choose",
                                                                  "choices": [{"value": "s1", "src": "machine.png"}]}]))
        code, page = self.run_sw("review", ".", "--print-page")
        self.assertIn('data-key="still/x"', page)

    def test_review_full_size_and_info_items(self):
        # paintings must not get the sprite's 3x pixel zoom, and an info card has a note but no pick buttons
        (self.dir / "review-extra.json").write_text(json.dumps([
            {"key": "scene/pick", "title": "pick", "kind": "choose", "display": "full",
             "choices": [{"value": "A", "src": "a.jpg"}]},
            {"key": "scene/why", "title": "why", "kind": "info", "display": "full", "text": ["context"],
             "images": ["b.jpg"]},
            {"key": "still/x", "title": "x", "kind": "choose", "choices": [{"value": "s1", "src": "m.png"}]}]))
        code, page = self.run_sw("review", ".", "--print-page")
        self.assertIn('class="cand full" data-v="A"', page)
        self.assertIn('class="cand" data-v="s1"', page)
        self.assertIn(".cand.full img{image-rendering:auto;zoom:1", page)
        why = page.split('data-key="scene/why"')[1].split("</section>")[0]
        self.assertIn('class="anim full" src="b.jpg"', why)
        self.assertNotIn("data-v=keep", why)
        self.assertIn('class=note', why)

    def test_review_refuses_a_busy_port(self):
        import socket
        # the holder reuses its address the way http.server does, so a careless second bind would succeed
        holder = socket.socket()
        holder.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        holder.bind(("127.0.0.1", 0))
        holder.listen()
        try:
            code, res = self.run_sw("review", ".", "--port", holder.getsockname()[1])
        finally:
            holder.close()
        self.assertEqual(code, 1, res)
        self.assertIn("in use", res["error"])

    def test_review_takes_and_legacy_gates(self):
        # batch/<id>/brief.json + out/, and a "build" take that changes place but leaves use byte-identical
        sprite = self.dir / "machine"
        sprite.mkdir()
        b = brief(use=PULSE, place=json.loads(json.dumps(PULSE)))
        b["animations"]["place"]["rest"] = "last"
        b["animations"]["place"]["tracks"][0]["curve"] = [1, 1, 0.6, 0.3, 0.1, 0]
        b["still"] = "../machine.png"
        (sprite / "brief.json").write_text(json.dumps(b))
        self.run_sw("frames", "machine/brief.json", "machine/out", "--no-aw", "--root", "machine")
        sw._CACHE.clear()
        self.run_sw("buildup", "machine/brief.json", "machine/brief-build.json", "--frames", "4")
        self.run_sw("frames", "machine/brief-build.json", "machine/out-build", "--no-aw", "--root", "machine")
        code, page = self.run_sw("review", ".", "--print-page")
        keys = sorted(set(__import__("re").findall(r'data-key="([^"]+)"', page)))
        self.assertEqual(keys, ["machine/place", "machine/place-build", "machine/use"])
        # a gates file written before 0.1.0: cardId, no frames field
        g = json.loads((sprite / "out" / "machine.gates.json").read_text())
        g["cardId"] = g.pop("id")
        for k in ("use", "place"):
            g[k].pop("frames")
        (sprite / "out" / "machine.gates.json").write_text(json.dumps(g))
        code, page = self.run_sw("review", ".", "--print-page")
        self.assertIn('data-key="machine/use"', page)
        self.assertIn("use (6 frames)", page)

    def test_doctor(self):
        code, res = self.run_sw("doctor")
        self.assertEqual(code, 0)
        self.assertIn("buildup", res["effects"])


class TestRound2Gates(Base):
    """Animation gates and the arc option from the 2026-10-25 book pass."""

    def make(self, anim, extra=None):
        b = brief(x=anim)
        b["regions"].update(extra or {})
        s = sw.Sprite(b, str(self.dir))
        return s, sw.build_frames(s, anim)

    def test_a_lone_blinking_pixel_is_flicker_and_a_blinking_block_is_not(self):
        blink = [0, 1, 0, 1, 0, 0]
        dot = {"frames": 6, "focal": "dot", "tracks": [{"effect": "pulse", "region": "dot", "hot": [255, 240, 200],
                                                         "strength": 1.0, "curve": blink}]}
        s, frames = self.make(dot, {"dot": {"rects": [[9, 15, 10, 16]]}})
        g = sw.gates(s, dot, frames, 0)
        self.assertEqual(g["flicker_pixels"], 1)
        self.assertEqual(g["flicker_at"], [[9, 15]])
        self.assertTrue(g["pass"])  # reported, not failed, unless the brief sets a limit
        dot["max_flicker_pixels"] = 0
        self.assertFalse(sw.gates(s, dot, frames, 0)["pass"])
        lamp = json.loads(json.dumps(PULSE))
        lamp["tracks"][0]["curve"] = blink
        s, frames = self.make(lamp)
        self.assertEqual(sw.gates(s, lamp, frames, 0)["flicker_pixels"], 0)

    def test_uneven_scroll_cadence_is_reported(self):
        for n, uneven in ((3, True), (4, False)):
            anim = {"frames": n, "tracks": [{"effect": "scroll", "region": "belt", "period": 4,
                                             "curve": [j / n for j in range(n)]}]}
            s, frames = self.make(anim)
            g = sw.gates(s, anim, frames, None)
            self.assertEqual("cadence_uneven" in g, uneven, g.get("cadence_uneven"))
        self.assertEqual(g.get("cadence_uneven"), None)
        anim = {"frames": 3, "tracks": [{"effect": "scroll", "region": "belt", "period": 4, "curve": [0, 1 / 3, 2 / 3]}]}
        s, frames = self.make(anim)
        self.assertEqual(sw.gates(s, anim, frames, None)["cadence_uneven"][0]["steps"], [1, 2])

    def test_pixel_perfect_path_drops_l_corners_and_keeps_ends(self):
        path = [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (2, 2), (3, 2), (3, 3)]
        out = sw._pixel_perfect(path)
        self.assertEqual(out[0], (0, 0))
        self.assertEqual(out[-1], (3, 3))
        for a, b in zip(out, out[1:]):
            self.assertEqual(max(abs(a[0] - b[0]), abs(a[1] - b[1])), 1)
        for a, b, c in zip(out, out[1:], out[2:]):
            self.assertFalse(abs(c[0] - a[0]) == 1 and abs(c[1] - a[1]) == 1, (a, b, c))
        self.assertEqual(sw._pixel_perfect([(5, 5)]), [(5, 5)])

    def test_perfect_arc_has_no_l_corners(self):
        s = sw.Sprite(brief(x=PULSE), str(self.dir))
        s.regions["wide"] = np.ones((32, 32), bool)
        for perfect, most in ((True, 0), (False, None)):
            hits = 0
            for seed in range(6):
                f = np.zeros((32, 32, 4), np.float32)
                sw.fx_arc(s, f, 1.0, {"region": "wide", "colours": [[255, 255, 0], [200, 100, 0]],
                                      "paths": [[2, 16, 29, 14]], "seed": seed, "flicker": 0, "perfect": perfect}, 0)
                core = (f[..., :3] == [255, 255, 0]).all(-1) & (f[..., 3] > 0)
                for y, x in zip(*np.nonzero(core)):
                    for dy in (-1, 1):
                        for dx in (-1, 1):
                            if 0 <= y + dy < 32 and 0 <= x + dx < 32 and core[y + dy, x] and core[y, x + dx] \
                                    and not core[y + dy, x + dx] and not (f[y + dy, x + dx, 3] > 0):
                                hits += 1
            if most is not None:
                self.assertEqual(hits, most)
            else:
                self.assertGreater(hits, 0)


class TestDownscale(unittest.TestCase):
    def test_box_filter_leaves_no_halo(self):
        """A white disc on mid grey reduced 8x: Lanczos rings below the grey outside the edge; box (linear light)
        keeps every pixel between the two."""
        yy, xx = np.mgrid[0:256, 0:256]
        rgb = np.where((((yy - 128) ** 2 + (xx - 128) ** 2) < 70 ** 2)[..., None], 1.0, 0.5) * np.ones((256, 256, 3))
        grey = round(0.5 * 255)
        lz = sw._downscale(rgb, np.ones((256, 256)), 32, 32)[..., 0]
        bx = sw._downscale(rgb, np.ones((256, 256)), 32, 32, "box")[..., 0]
        self.assertGreater(int((lz < grey).sum()), 0)
        self.assertEqual(int((bx < grey).sum()), 0)
        self.assertEqual(float(bx.max()), 255.0)


if __name__ == "__main__":
    unittest.main(verbosity=1)
