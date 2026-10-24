"""Deterministic check for outcome-make-3: python evals/check_make_real.py <run folder>. Prints JSON; exit 1 on
failure. The input is a real model render: Z-Image Turbo img2img (denoise 0.75, seed 11) of make_render's potion drawn
at 58.5x, halved and cropped (outcome3_fixture.py holds the bytes). The model kept the 16x16 drawing, added off-grid shading inside blocks, and moved the highlight up one art
pixel, so the truth is the potion with those two pixels pink (checked by eye on the render). Passes when
potion-clean.png, cropped to its opaque pixels, is that sprite exactly, with binary alpha and only ref.png's colours."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent / "fixtures"))
from make_render import PINK, potion, ref  # noqa: E402


def truth():
    p = potion()
    py, px = np.nonzero(p[..., 3])
    p = p[py.min():py.max() + 1, px.min():px.max() + 1].copy()
    p[7, 2:4] = PINK + [255]
    return p


if __name__ == "__main__":
    run = Path(sys.argv[1])
    found = sorted(run.rglob("potion-clean.png"))
    res = {"found": bool(found)}
    if found:
        a = np.array(Image.open(found[0]).convert("RGBA"))
        res["size"] = [a.shape[1], a.shape[0]]
        res["alpha_binary"] = bool(np.isin(a[..., 3], (0, 255)).all())
        allowed = {tuple(c) for c in ref()[ref()[..., 3] > 0][:, :3].tolist()}
        used = {tuple(c) for c in a[a[..., 3] > 0][:, :3].tolist()}
        res["colours_outside_ref"] = len(used - allowed)
        ys, xs = np.nonzero(a[..., 3])
        t = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1] if len(ys) else a
        p = truth()
        res["matches_truth"] = bool(t.shape == p.shape and (t == p).all())
        if t.shape == p.shape:
            res["pixels_wrong"] = int((t != p).any(-1).sum())
        else:
            res["cropped_size"] = [t.shape[1], t.shape[0]]
        res["pass"] = bool(res["alpha_binary"] and res["colours_outside_ref"] == 0 and res["matches_truth"])
    else:
        res["pass"] = False
    print(json.dumps(res))
    sys.exit(0 if res["pass"] else 1)
