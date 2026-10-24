"""Deterministic check for outcome-make-2: python evals/check_make_hard.py <run folder>. Prints JSON; exit 1 on
failure. Passes when potion-clean.png, cropped to its opaque pixels, is the 16x16 potion the 5.5x render was made
from, exactly, with binary alpha and only the colours of the three sprites in refs/."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent / "fixtures"))
from make_render import potion  # noqa: E402
from make_render_hard import refs  # noqa: E402

run = Path(sys.argv[1])
found = sorted(p for p in run.rglob("potion-clean.png") if "refs" not in p.parts)
res = {"found": bool(found)}
if found:
    a = np.array(Image.open(found[0]).convert("RGBA"))
    res["size"] = [a.shape[1], a.shape[0]]
    res["alpha_binary"] = bool(np.isin(a[..., 3], (0, 255)).all())
    allowed = {tuple(c) for r in refs().values() for c in r[r[..., 3] > 0][:, :3].tolist()}
    used = {tuple(c) for c in a[a[..., 3] > 0][:, :3].tolist()}
    res["colours_outside_refs"] = len(used - allowed)
    ys, xs = np.nonzero(a[..., 3])
    t = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1] if len(ys) else a
    p = potion()
    py, px = np.nonzero(p[..., 3])
    p = p[py.min():py.max() + 1, px.min():px.max() + 1]
    res["matches_truth"] = bool(t.shape == p.shape and (t == p).all())
    if t.shape == p.shape:
        res["pixels_wrong"] = int((t != p).any(-1).sum())
    else:
        res["cropped_size"] = [t.shape[1], t.shape[0]]
    res["pass"] = bool(res["alpha_binary"] and res["colours_outside_refs"] == 0 and res["matches_truth"])
else:
    res["pass"] = False
print(json.dumps(res))
sys.exit(0 if res["pass"] else 1)
