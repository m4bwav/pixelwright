"""Deterministic check for outcome-make-1: python evals/check_make_outcome.py <run folder>. Prints JSON; exit 1 on
failure. Passes when potion-clean.png, cropped to its opaque pixels, is the 16x16 potion the render was made from,
exactly, with binary alpha and only ref.png's colours."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent / "fixtures"))
from make_render import potion, ref  # noqa: E402

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
    p = potion()
    py, px = np.nonzero(p[..., 3])
    p = p[py.min():py.max() + 1, px.min():px.max() + 1]
    res["matches_truth"] = bool(t.shape == p.shape and (t == p).all())
    if t.shape == p.shape:
        res["pixels_wrong"] = int((t != p).any(-1).sum())
    res["pass"] = bool(res["alpha_binary"] and res["colours_outside_ref"] == 0 and res["matches_truth"])
else:
    res["pass"] = False
print(json.dumps(res))
sys.exit(0 if res["pass"] else 1)
